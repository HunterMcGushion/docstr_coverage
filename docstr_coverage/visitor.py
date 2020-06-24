"""This module handles traversing abstract syntax trees to check for docstrings"""
from ast import NodeVisitor, get_docstring, FunctionDef, ClassDef, Module


class DocStringCoverageVisitor(NodeVisitor):
    """Class to visit nodes, determine whether a node requires a docstring,
    and to check for the existence of a docstring"""

    def __init__(self):
        self.symbol_count = 0
        self.tree = []

    def visit_Module(self, node: Module):
        """Upon visiting a module, initialize :attr:`DocStringCoverageVisitor.tree`
        with module-wide node info."""
        has_doc = get_docstring(node) is not None and get_docstring(node).strip() != ""
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
        has_doc = get_docstring(node) is not None and get_docstring(node).strip() != ""
        _node = (node.name, has_doc, [])
        self.tree[-1][-1].append(_node)
        self.tree.append(_node)
        self.generic_visit(node)
        self.tree.pop()
