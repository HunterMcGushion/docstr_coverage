"""The central module for coverage collection and file-walking"""

import os
import re
import warnings
from ast import parse
from typing import Dict, List, Tuple

from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.printers import LegacyPrinter
from docstr_coverage.result_collection import File, FileStatus, ResultCollection
from docstr_coverage.visitor import DocStringCoverageVisitor


def do_ignore_node(filename: str, base_name: str, node_name: str, ignore_names: tuple) -> bool:
    """Determine whether a node (identified by its file, base, and own names) should be ignored

    Parameters
    ----------
    filename: String
        Name of the file containing `node_name`
    base_name: String
        Name of the node's parent node
    node_name: String
        Name of the node within the file. Usually a function name, class name, or a method name. In
        the case of method names, `node_name` will be only the method's name, while `base_name` will
        be of the form "<class_name>."
    ignore_names: Tuple[List[str], ...]
        Patterns of nodes to ignore. See :class:`docstr_coverage.ignore_config.IgnoreConfig`

    Returns
    -------
    Boolean
        True if the node should be ignored, else False"""
    filename = os.path.basename(filename).split(".")[0]

    for (file_regex, *name_regexes) in ignore_names:
        file_match = re.fullmatch(file_regex, filename)
        file_match = file_match.group() if file_match else None

        if file_match != filename:
            continue

        for name_regex in name_regexes:
            # Match on node name only
            name_match = re.fullmatch(name_regex, node_name)
            name_match = name_match.group() if name_match else None

            if name_match:
                return True

            # Match on node's period-delimited path: Its parent nodes (if any), plus the node name.
            #   This enables targeting i.e. the `__init__` method of a particular class, whereas
            #   the simple name match above would target `__init__` methods of all classes
            full_name_match = re.fullmatch(name_regex, "{}{}".format(base_name, node_name))
            full_name_match = full_name_match.group() if full_name_match else None

            if full_name_match:
                return True
    return False


def analyze_docstrings(
    file_result: File,
    base: str,
    node: Tuple[str, bool, List],
    filename,
    ignore_config: IgnoreConfig,
):
    """Track the existence of a docstring for `node`, and accumulate stats regarding
    expected and encountered docstrings for `node` and its children (if any).

    Parameters
    ----------
    file_result: File
        The result-collection file instance on which the docstring presence is recorded.
    base: String
        The name of this node's parent node
    node: Tuple triple of (String, Boolean, List)
        Information describing a node. `node[0]` is the node's name.
        `node[1]` is True if the node was properly documented,
        else False. `node[3]` is a list containing the node's children
        as triples of the same form (if it had any)
    filename: String
        String containing the name of the file.
    ignore_config: IgnoreConfig
        Information about which docstrings are to be ignored."""

    name, has_doc, child_nodes = node

    ##################################################
    # Check Current Node
    ##################################################

    # Check for ignore status
    ignore_reason = None
    if ignore_config.skip_init and name == "__init__":
        ignore_reason = "skip-init set to True"
    elif (
        ignore_config.skip_magic
        and name.startswith("__")
        and name.endswith("__")
        and name != "__init__"
    ):
        ignore_reason = "skip-magic set to True"
    elif ignore_config.skip_class_def and "_" not in name and (name[0] == name[0].upper()):
        ignore_reason = "skip-class-def set to True"
    elif ignore_config.skip_private and name.startswith("_") and not name.startswith("__"):
        ignore_reason = "skip-private set to True"
    elif ignore_config.ignore_names and do_ignore_node(
        filename, base, name, ignore_config.ignore_names
    ):
        ignore_reason = "matching ignore pattern"

    # Set Result
    node_identifier = str(base) + str(name)
    file_result.collect_docstring(
        identifier=node_identifier, has_docstring=has_doc, ignore_reason=ignore_reason
    )

    ##################################################
    # Check Child Nodes
    ##################################################
    for _symbol in child_nodes:
        analyze_docstrings(file_result, "%s." % name, _symbol, filename, ignore_config)


def get_docstring_coverage(
    filenames: list,
    skip_magic: bool = False,
    skip_file_docstring: bool = False,
    skip_init: bool = False,
    skip_class_def: bool = False,
    skip_private: bool = False,
    verbose: int = 0,
    ignore_names: Tuple[List[str], ...] = (),
) -> Tuple[Dict, Dict]:
    """***DEPRECATED***

    This used to be the primary way to access docstr-coverage as a software library.
    It is now replaced by the function `analyze`, which provides
    a slimmer interface and a more informative return value.

    For backwards compatibility with existing code, call `analyze(...).to_legacy()`"""
    warnings.warn(
        "get_docstring_coverage is deprecated." "See function docstring for details.",
        DeprecationWarning,
        stacklevel=2,
    )
    ignore_config = IgnoreConfig(
        skip_magic=skip_magic,
        skip_file_docstring=skip_file_docstring,
        skip_init=skip_init,
        skip_class_def=skip_class_def,
        skip_private=skip_private,
        ignore_names=ignore_names,
    )
    results = analyze(filenames, ignore_config)
    LegacyPrinter(verbosity=verbose, ignore_config=ignore_config).print(results)
    return results.to_legacy()


def analyze(filenames: list, ignore_config: IgnoreConfig = IgnoreConfig()) -> ResultCollection:
    """Checks contents of `filenames` for missing docstrings, and produces a report detailing
    docstring status

    Parameters
    ----------
    filenames: List
        List of filename strings that are absolute or relative paths
    ignore_config: IgnoreConfig
        Information about which docstrings are to be ignored

    Returns
    -------
    ResultCollection
        The collected information about docstring presence"""
    results = ResultCollection()

    for filename in filenames:
        file_result = results.get_file(file_path=filename)

        ##################################################
        # Read and Parse Source
        ##################################################
        with open(filename, "r", encoding="utf-8") as f:
            source_tree = f.read()

        doc_visitor = DocStringCoverageVisitor(filename=filename)
        doc_visitor.visit(parse(source_tree))
        _tree = doc_visitor.tree[0]

        ##################################################
        # Process Results
        ##################################################

        # _tree contains [<module docstring>, <is_empty: bool>, <symbols: classes and funcs>]
        if (not _tree[0]) and (not _tree[1]):
            if not ignore_config.skip_file_docstring:
                file_result.collect_module_docstring(has_docstring=False)
            else:
                file_result.collect_module_docstring(
                    has_docstring=False, ignore_reason="--skip-file-docstring=True"
                )
        elif _tree[1]:
            file_result.status = FileStatus.EMPTY
        else:
            file_result.collect_module_docstring(bool(_tree[0]))

        # Recursively traverse through functions and classes
        for symbol in _tree[-1]:
            analyze_docstrings(file_result, "", symbol, filename, ignore_config)

    return results
