"""This repository is based on the work of Alexey "DataGreed" Strelkov, and James Harlow (see "THANKS.txt" for details)"""

# TODO: If Python 2, ```from __future__ import print_function```
from ast import NodeVisitor, parse, get_docstring
import os
from pprint import pprint as pp
import re
import sys


class DocStringCoverageVisitor(NodeVisitor):
    """Class to visit nodes, determine whether a node requires a docstring, and to check for the existence of a docstring"""

    def __init__(self):
        self.symbol_count = 0
        self.tree = []

    def visit_Module(self, node):
        """Upon visiting a module, initialize :attr:`DocStringCoverageVisitor.tree` with module-wide node info"""
        has_doc = get_docstring(node) is not None and get_docstring(node).strip() != ""
        is_empty = not len(node.body)
        self.tree.append((has_doc, is_empty, []))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Collect information regarding class declaration nodes"""
        self._visit_helper(node)

    def visit_FunctionDef(self, node):
        """Collect information regarding function/method declaration nodes"""
        self._visit_helper(node)

    def _visit_helper(self, node):
        """Helper method to update :attr:`DocStringCoverageVisitor.tree` with pertinent documentation information for `node`, then
        ensure all child nodes are also visited"""
        self.symbol_count += 1
        has_doc = get_docstring(node) is not None and get_docstring(node).strip() != ""
        _node = (node.name, has_doc, [])
        self.tree[-1][-1].append(_node)
        self.tree.append(_node)
        self.generic_visit(node)
        self.tree.pop()


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
    ("Do you even docstring?", 1),
)


def get_docstring_coverage(
    filenames,
    skip_magic=False,
    skip_file_docstring=False,
    skip_init=False,
    skip_class_def=False,
    verbose=0,
):
    """Checks contents of `filenames` for missing docstrings, and produces a report detailing docstring status

    Parameters
    ----------
    filenames: List
        List of filename strings that are absolute or relative paths
    skip_magic: Boolean, default=False
        If True, skips all magic methods (double-underscore-prefixed), except '__init__' and does not include them in the report
    skip_file_docstring: Boolean, default=False
        If True, skips check for a module-level docstring
    skip_init: Boolean, default=False
        If True, skips methods named '__init__' and does not include them in the report
    skip_class_def: Boolean, default=False
        If True, skips class definitions and does not include them in the report. If this is True, the class's methods will still
        be checked
    verbose: Int in [0, 1, 2, 3], default=0
        0) No printing. 1) Print total stats only. 2) Print stats for all files. 3) Print missing docstrings for all files

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
        ... }
    """
    verbose = int(verbose)

    # TODO: Switch to Python's `logging` module, and remove below nested `log` function definition
    def log(text, level=1, append=False):
        """Prints `text` to log depending on `verbose`

        Parameters
        ----------
        text: String
            The text to print
        level: Int
            The verbosity level at which it becomes appropriate to print the content. If `level` > `verbose`, nothing happens.
            Otherwise, `text` is printed
        append: Boolean, default=False
            If True, print with an ending space, rather than a newline character"""
        if verbose >= level:
            if append:
                print(text, end=" ")
            else:
                print(text)

    # TODO: Move :func:`print_docstring` to be a normal function outside of :func:`get_docstring_coverage`
    def print_docstring(base, node):
        """Log the existence of a docstring for `node`, and accumulate stats regarding expected and encountered docstrings for
        `node` and its children (if any)

        Parameters
        ----------
        base: String
            The name of this node's parent node
        node: Tuple triple of (String, Boolean, List)
            Information describing a node. `node[0]` is the node's name. `node[1]` is True if the node was properly documented,
            else False. `node[3]` is a list containing the node's children as triples of the same form (if it had any)

        Returns
        -------
        docs_needed: Int
            The number of docstrings expected for `node` and its children to achieve full documentation coverage
        docs_covered: Int
            The number of docstrings found for `node` and its children
        _missing_list: List
            Nodes that were expected to have docstrings but did not. Values are the concatenation of a node's base and its name"""
        _missing_list = []
        docs_needed = 1
        docs_covered = 0
        name, has_doc, child_nodes = node

        #################### Check Current Node ####################
        if not has_doc:
            # TODO: Add option to skip class definition docstrings (though one of class or magic methods should used)
            if skip_init and name == "__init__":
                docs_needed -= 1
            elif (
                skip_magic and name.startswith("__") and name.endswith("__") and name != "__init__"
            ):
                docs_needed -= 1
            elif skip_class_def and "_" not in name and (name[0] == name[0].upper()):
                docs_needed -= 1
            else:
                log(" - No docstring for `%s%s`" % (base, name), 3)
                _missing_list.append(base + name)
        else:
            docs_covered += 1

        #################### Check Child Nodes ####################
        for _symbol in child_nodes:
            _temp_docs_needed, _temp_docs_covered, temp_missing_list = print_docstring(
                "%s." % name, _symbol
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
        with open(filename, "r") as f:
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
            temp_docs_needed, temp_docs_covered, missing_list = print_docstring("", symbol)
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
        "coverage": float(total_docs_covered) * 100 / float(total_docs_needed),
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

    log("\n", 2)

    if len(filenames) > 1:
        log("Overall statistics for %s files%s:" % (len(filenames), postfix), 1)
    else:
        log("Overall statistics%s:" % postfix, 1)

    log("Docstrings needed: %s;" % total_docs_needed, 1, append=True)
    log("Docstrings found: %s;" % total_docs_covered, 1, append=True)
    log("Docstrings missing: %s" % (total_results["missing_count"]), 1)
    log("Total docstring coverage: %.1f%%; " % (total_results["coverage"]), 1, True)

    #################### Calculate Total Grade ####################
    grade = next(_[0] for _ in GRADES if _[1] <= total_results["coverage"])
    log("Grade: %s" % grade, 1)
    return file_results, total_results


def _execute():
    """Main command-line execution routine"""
    from optparse import OptionParser

    # TODO: Move away from optparse - Deprecated (https://pythonprogramminglanguage.com/command-line-arguments/)

    #################### Declare Options ####################
    parser = OptionParser()
    # TODO: Add option to generate pretty coverage reports - Like Python's `coverage` module does for test coverage
    # TODO: Add option to sort report summaries by filename, coverage score... (ascending/descending)
    parser.add_option(
        "-e",
        "--exclude",
        dest="exclude",
        default=None,
        type="string",
        help="Regex identifying filepaths to exclude",
    )
    # TODO: Add support for multiple `--exclude` regexes to lessen need for long regexes describing separate exclusion items
    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        default="3",
        metavar="LEVEL",
        help="Verbosity level <0-3>, default=3",
        type="choice",
        choices=["0", "1", "2", "3"],
    )
    parser.add_option(
        "-m",
        "--skipmagic",
        action="store_true",
        dest="skip_magic",
        default=False,
        help='Ignore docstrings of magic methods (except "__init__")',
    )
    parser.add_option(
        "-f",
        "--skipfiledoc",
        action="store_true",
        dest="skip_file_docstring",
        default=False,
        help="Ignore module docstrings",
    )
    parser.add_option(
        "-i",
        "--skipinit",
        action="store_true",
        dest="skip_init",
        default=False,
        help='Ignore docstrings of "__init__" methods',
    )
    parser.add_option(
        "-c",
        "--skipclassdef",
        action="store_true",
        dest="skip_class_def",
        default=False,
        help="Ignore docstrings of class definitions",
    )
    parser.add_option(
        "-l",
        "--followlinks",
        action="store_true",
        dest="follow_links",
        default=False,
        help="Follow symlinks",
    )
    # TODO: Separate above arg/option parsing into separate function - Document return values to describe allowed options
    options, args = parser.parse_args()

    if len(args) != 1:
        print("Expected a single path argument. Received invalid argument(s): {}".format(args[1:]))
        sys.exit()

    #################### Collect Filenames ####################
    exclude_re = re.compile(r"{}".format(options.exclude)) if options.exclude else None
    filenames = []

    if args[0].endswith(".py"):
        filenames = [args[0]]
    else:
        for root, dirs, f_names in os.walk(args[0], followlinks=options.follow_links):
            if exclude_re is not None:
                dirs[:] = [_ for _ in dirs if not exclude_re.match(_)]

            new_files = [os.path.join(root, _) for _ in f_names if _.endswith(".py")]

            if exclude_re is not None:
                filenames.extend([_ for _ in new_files if not exclude_re.match(_)])
            else:
                filenames.extend(new_files)

    if len(filenames) < 1:
        sys.exit("No Python files found")

    get_docstring_coverage(
        filenames,
        skip_magic=options.skip_magic,
        skip_file_docstring=options.skip_file_docstring,
        skip_init=options.skip_init,
        skip_class_def=options.skip_class_def,
        verbose=options.verbose,
    )


if __name__ == "__main__":
    _execute()
