"""This module handles traversing abstract syntax trees to check for docstrings"""
import re
import tokenize
from ast import NodeVisitor, get_docstring, FunctionDef, ClassDef, Module

ACCEPTED_EXCUSE_PATTERNS = (
    re.compile("#\s*docstr(ing)?_cov(erage)?\s*:\s*inherit(ed)?\s*"),
    re.compile("#\s*docstr(ing)?_cov(erage)?\s*:\s*excuse\s* [\"\'].*[\"\']\s*")
)


class DocStringCoverageVisitor(NodeVisitor):
    """Class to visit nodes, determine whether a node requires a docstring,
    and to check for the existence of a docstring"""

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'rb') as file:
            self.line_tokens = list(tokenize.tokenize(file.readline))
        self.symbol_count = 0
        self.tree = []

    def visit_Module(self, node: Module):
        """Upon visiting a module, initialize :attr:`DocStringCoverageVisitor.tree`
        with module-wide node info."""
        has_doc = self._has_docstring(node)
        is_empty = not len(node.body)
        self.tree.append((has_doc, is_empty, []))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ClassDef):
        """Collect information regarding class declaration nodes"""
        self._visit_helper(node)

    def visit_FunctionDef(self, node: FunctionDef):
        """Collect information regarding function/method declaration nodes"""
        self._visit_helper(node)

    def _visit_helper(self, node):
        """Helper method to update :attr:`DocStringCoverageVisitor.tree` with pertinent
        documentation information for `node`, then ensure all child nodes are
        also visited"""
        self.symbol_count += 1
        has_doc = self._has_doc_or_excuse(node)
        _node = (node.name, has_doc, [])
        self.tree[-1][-1].append(_node)
        self.tree.append(_node)
        self.generic_visit(node)
        self.tree.pop()

    def _has_doc_or_excuse(self, node):
        return self._has_docstring(node=node) or self._has_excuse(node=node)

    def _has_excuse(self, node):
        excuse_line = node.lineno - 1
        if excuse_line < 0:
            # The node started on line 0 and has thus no excuse line
            return False
        assert excuse_line < len(self.line_tokens), \
            f"An unexpected context occurred during parsing of {self.filename} " \
            "It seems not all file lines were tokenized for comment checking."
        as_token = self.line_tokens[excuse_line]
        return (
                as_token.type == tokenize.COMMENT
                and any(regex.match(as_token.string) for regex in ACCEPTED_EXCUSE_PATTERNS)
        )

    @staticmethod
    def _has_docstring(node):
        return get_docstring(node) is not None and get_docstring(node).strip() != ""



