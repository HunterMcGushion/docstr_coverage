"""This repository is based on the work of Alexey "DataGreed" Strelkov,
and James Harlow (see "THANKS.txt" for details)"""

# TODO: If Python 2, ```from __future__ import print_function```
from ast import parse
import logging
import os
import re
from typing import List, Tuple

from docstr_coverage.visitor import DocStringCoverageVisitor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


GRADES = (
    ("AMAZING! Your docstrings are truly a wonder to behold!", 100),
    ("Excellent", 92),
    ("Great", 85),
    ("Very good", 70),
    ("Good", 60),
    ("Not bad", 40),
    ("Not good", 25),
    ("Extremely poor", 10),
    ("Not documented at all", 2),
    ("Do you even docstring?", 0),
)


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
        Patterns to ignore when checking documentation. Each list in `ignore_names` defines a
        different pattern to be ignored. The first element in each list is the regular expression
        for matching filenames. All remaining arguments in each list are regexes for matching names
        of functions/classes. A node is ignored if it matches the filename regex and at least one
        of the remaining regexes

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


def get_docstring_coverage(
    filenames: list,
    skip_magic: bool = False,
    skip_file_docstring: bool = False,
    skip_init: bool = False,
    skip_class_def: bool = False,
    skip_private: bool = False,
    verbose: int = 0,
    ignore_names: Tuple[List[str], ...] = (),
):
    """Checks contents of `filenames` for missing docstrings, and produces a report
    detailing docstring status.

    Parameters
    ----------
    filenames: List
        List of filename strings that are absolute or relative paths
    skip_magic: Boolean, default=False
        If True, skips all magic methods (double-underscore-prefixed),
        except '__init__' and does not include them in the report
    skip_file_docstring: Boolean, default=False
        If True, skips check for a module-level docstring
    skip_init: Boolean, default=False
        If True, skips methods named '__init__' and does not include
        them in the report
    skip_class_def: Boolean, default=False
        If True, skips class definitions and does not include them in the report.
        If this is True, the class's methods will still be checked
    skip_private: Boolean, default=False
        If True, skips function definitions beginning with a single underscore and does
        not include them in the report.
    verbose: Int in [0, 1, 2, 3], default=0
        0) No printing.
        1) Print total stats only.
        2) Print stats for all files.
        3) Print missing docstrings for all files.
    ignore_names: Tuple[List[str], ...], default=()
        Patterns to ignore when checking documentation. Each list in `ignore_names` defines a
        different pattern to be ignored. The first element in each list is the regular expression
        for matching filenames. All remaining arguments in each list are regexes for matching names
        of functions/classes. A node is ignored if it matches the filename regex and at least one
        of the remaining regexes

    Returns
    -------
    Dict
        Links filename keys to a dict of stats for that filename. Example:

        >>> {
        ...     '<filename>': {
        ...         'missing': ['<method_or_class_name>', '...'],
        ...         'module_doc': '<Boolean>',
        ...         'missing_count': '<missing_count int>',
        ...         'needed_count': '<needed_docstrings_count int>',
        ...         'coverage': '<percent_of_coverage float>',
        ...         'empty': '<Boolean>'
        ...     }, ...
        ... }
    Dict
        Total summary stats for all files analyzed. Example:

        >>> {
        ...     'missing_count': '<total_missing_count int>',
        ...     'needed_count': '<total_needed_docstrings_count int>',
        ...     'coverage': '<total_percent_of_coverage float>'
        ... }"""

    verbose = int(verbose)

    # TODO: Switch to Python's `logging` module, and remove
    #       below nested `log` function definition
    def log(text, level=1):
        """Prints `text` to log depending on `verbose`

        Parameters
        ----------
        text: String
            The text to print
        level: Int
            The verbosity level at which it becomes appropriate to print the content.
            If `level` > `verbose`, nothing happens. Otherwise, `text` is printed."""
        if verbose >= level:
            logger.info(text)

    # TODO: Move :func:`print_docstring` to be a normal function
    #       outside of :func:`get_docstring_coverage`
    def print_docstring(base, node, filename, ignore_names=()):
        """Log the existence of a docstring for `node`, and accumulate stats regarding
        expected and encountered docstrings for `node` and its children (if any).

        Parameters
        ----------
        base: String
            The name of this node's parent node
        node: Tuple triple of (String, Boolean, List)
            Information describing a node. `node[0]` is the node's name.
            `node[1]` is True if the node was properly documented,
            else False. `node[3]` is a list containing the node's children
            as triples of the same form (if it had any)
        filename: String
            String containing a name of file.
        ignore_names: tuple of lists ([String, String, [String...]]) where the first
            element is the regular expression for matching filenames. All remaining
            arguments are regexes for matching names of functions/classes to be
            excluded from checking for documentation. It will be excluded if and
            only if the first and at least one of the remaining regexes hits a match.

        Returns
        -------
        docs_needed: Int
            The number of docstrings expected for `node` and its children to achieve
            full documentation coverage
        docs_covered: Int
            The number of docstrings found for `node` and its children
        _missing_list: List
            Nodes that were expected to have docstrings but did not.
            Values are the concatenation of a node's base and its name"""

        _missing_list = []
        docs_needed = 1
        docs_covered = 0
        name, has_doc, child_nodes = node

        #################### Check Current Node ####################
        if not has_doc:
            # TODO: Add option to skip class definition docstrings
            #      (though one of class or magic methods should used)
            if skip_init and name == "__init__":
                docs_needed -= 1
            elif (
                skip_magic and name.startswith("__") and name.endswith("__") and name != "__init__"
            ):
                docs_needed -= 1
            elif skip_class_def and "_" not in name and (name[0] == name[0].upper()):
                docs_needed -= 1
            elif skip_private and name.startswith("_") and not name.startswith("__"):
                docs_needed -= 1
            elif ignore_names and do_ignore_node(filename, base, name, ignore_names):
                docs_needed -= 1
            else:
                log(" - No docstring for `%s%s`" % (base, name), 3)
                _missing_list.append(base + name)
        else:
            docs_covered += 1

        #################### Check Child Nodes ####################
        for _symbol in child_nodes:
            _temp_docs_needed, _temp_docs_covered, temp_missing_list = print_docstring(
                "%s." % name, _symbol, filename, ignore_names
            )
            docs_needed += _temp_docs_needed
            docs_covered += _temp_docs_covered
            _missing_list += temp_missing_list

        return docs_needed, docs_covered, _missing_list

    total_docs_needed = 0
    total_docs_covered = 0
    empty_files = 0
    file_results = {}

    for filename in filenames:
        log('\nFile: "%s"' % filename, 2)

        file_docs_needed = 1
        file_docs_covered = 1
        file_missing_list = []

        #################### Read and Parse Source ####################
        with open(filename, "r", encoding="utf-8") as f:
            source_tree = f.read()

        doc_visitor = DocStringCoverageVisitor()
        doc_visitor.visit(parse(source_tree))
        _tree = doc_visitor.tree[0]
        # pp(_tree)

        #################### Process Results ####################
        # _tree contains [<module docstring>, <is_empty: bool>, <symbols: classes and funcs>]
        if (not _tree[0]) and (not _tree[1]) and (not skip_file_docstring):
            log(" - No module docstring", 3)
            file_docs_covered -= 1
        elif _tree[1]:
            log(" - File is empty", 3)
            file_docs_needed = 0
            file_docs_covered = 0
            empty_files += 1

        # Traverse through functions and classes
        for symbol in _tree[-1]:
            temp_docs_needed, temp_docs_covered, missing_list = print_docstring(
                "", symbol, filename, ignore_names
            )
            file_docs_needed += temp_docs_needed
            file_docs_covered += temp_docs_covered
            file_missing_list += missing_list

        total_docs_needed += file_docs_needed
        total_docs_covered += file_docs_covered

        if file_docs_needed:
            coverage = float(file_docs_covered) * 100 / float(file_docs_needed)
        else:
            coverage = 0

        file_results[filename] = {
            "missing": file_missing_list,
            "module_doc": bool(_tree[0]),
            "missing_count": file_docs_needed - file_docs_covered,
            "needed_count": file_docs_needed,
            "coverage": coverage,
            "empty": bool(_tree[1]),
        }

        log(
            " Needed: %s; Found: %s; Missing: %s; Coverage: %.1f%%"
            % (
                file_docs_needed,
                file_docs_covered,
                file_results[filename]["missing_count"],
                file_results[filename]["coverage"],
            ),
            2,
        )

    total_results = {
        "missing_count": total_docs_needed - total_docs_covered,
        "needed_count": total_docs_needed,
        "coverage": (
            float(total_docs_covered) * 100 / float(total_docs_needed) if total_docs_needed else 100
        ),
    }

    postfix = ""
    if empty_files:
        postfix = " (%s files are empty)" % empty_files
    if skip_magic:
        postfix += " (skipped all non-init magic methods)"
    if skip_file_docstring:
        postfix += " (skipped file-level docstrings)"
    if skip_init:
        postfix += " (skipped __init__ methods)"
    if skip_class_def:
        postfix += " (skipped class definitions)"
    if skip_private:
        postfix += " (skipped private methods)"

    log("\n", 2)

    if len(filenames) > 1:
        log("Overall statistics for %s files%s:" % (len(filenames), postfix), 1)
    else:
        log("Overall statistics%s:" % postfix, 1)

    log(
        "Needed: {}  -  Found: {}  -  Missing: {}".format(
            total_docs_needed, total_docs_covered, total_results["missing_count"]
        ),
        1,
    )

    #################### Calculate Total Grade ####################
    grade = next(
        message
        for message, grade_threshold in GRADES
        if grade_threshold <= total_results["coverage"]
    )

    log("Total coverage: {:.1f}%  -  Grade: {}".format(total_results["coverage"], grade), 1)

    return file_results, total_results
