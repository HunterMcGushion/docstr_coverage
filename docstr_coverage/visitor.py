"""This module handles traversing abstract syntax trees to check for docstrings"""
import re
import tokenize
from ast import NodeVisitor, get_docstring, FunctionDef, ClassDef, Module

ACCEPTED_EXCUSE_PATTERNS = (
    re.compile(r"#\s*docstr(ing)?_cov(erage)?\s*:\s*inherit(ed)?\s*"),
    re.compile(r"#\s*docstr(ing)?_cov(erage)?\s*:\s*excuse(d)?\s* [\"\'].*[\"\']\s*"),
)


class DocStringCoverageVisitor(NodeVisitor):
    """Class to visit nodes, determine whether a node requires a docstring,
    and to check for the existence of a docstring"""

    def __init__(self, filename):
        self.filename = filename
        with open(filename, "rb") as file:
            self.tokens = list(tokenize.tokenize(file.readline))
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
        """Evaluates if the passed not has a corresponding docstring
        or if there is an excuse comment."""
        return self._has_docstring(node=node) or self._has_excuse(node=node)

    @staticmethod
    def _is_excuse_token(token):
        """Evaluates, for the given tokenizer.token
        if said token represents a valid excuse comment."""
        return token.type == tokenize.COMMENT and any(
            regex.match(token.string) for regex in ACCEPTED_EXCUSE_PATTERNS
        )

    @staticmethod
    def _is_skip_token(token):
        """Evaluates, for the given tokenize.token,
        if said token is expected between a node start and an excuse token."""
        return (
            token.type == tokenize.NL
            or token.type == tokenize.NEWLINE
            or (token.type == tokenize.NAME and token.string == "class")
            or token.line.strip().startswith("@")
        )

    def _has_excuse(self, node):
        """Iterates through the tokenize tokens above the passed node to evaluate whether a
        doc-missing excuse has been placed (right) above this nodes begin."""
        node_start = node.lineno
        if node_start < 0:
            # The node started on line 0 and has thus no excuse line
            return False
        assert node_start < len(self.tokens), (
            "An unexpected context occurred during parsing of {} "
            "It seems not all file lines were tokenized for comment checking."
        ).format(self.filename)

        token_index = -1
        for i, t in enumerate(self.tokens):
            if t.start[0] == node_start:
                token_index = i - 1
                break

        while token_index >= 0:
            as_token = self.tokens[token_index]
            if self._is_skip_token(as_token):
                token_index -= 1
            else:
                return self._is_excuse_token(as_token)
        # Reached the top of the file
        return False

    @staticmethod
    def _has_docstring(node):
        """Uses ast to check if the passed not contains a non-empty docstring."""
        return get_docstring(node) is not None and get_docstring(node).strip() != ""
