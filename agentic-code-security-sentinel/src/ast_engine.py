"""
AST & Taint Analysis Engine.
Implements Abstract Syntax Tree parsing, Shannon entropy computation,
control flow reachability, and variable taint propagation.
"""

import ast
from collections import Counter
import math
from typing import Any, Dict, List, Optional, Set, Tuple


def calculate_shannon_entropy(text: str) -> float:
    """
    Computes Shannon Information Entropy H(X) = -sum(p * log2(p)) for a string.
    High entropy (> 4.2) indicates cryptographic keys, tokens, or random passwords.
    """
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


class TaintScope:
    """Tracks tainted and sanitized variable identifiers within an execution scope."""

    def __init__(self, parent: Optional["TaintScope"] = None):
        self.parent = parent
        self.tainted_vars: Dict[str, str] = {}  # var_name -> source_expr
        self.sanitized_vars: Set[str] = set()

    def taint(self, var_name: str, source: str) -> None:
        if var_name not in self.sanitized_vars:
            self.tainted_vars[var_name] = source

    def sanitize(self, var_name: str) -> None:
        self.sanitized_vars.add(var_name)
        if var_name in self.tainted_vars:
            del self.tainted_vars[var_name]

    def is_tainted(self, var_name: str) -> Tuple[bool, Optional[str]]:
        if var_name in self.sanitized_vars:
            return False, None
        if var_name in self.tainted_vars:
            return True, self.tainted_vars[var_name]
        if self.parent:
            return self.parent.is_tainted(var_name)
        return False, None


class ASTHelper:
    """Utility class for AST traversal and metadata extraction."""

    @staticmethod
    def get_call_name(node: ast.Call) -> str:
        """Extracts dotted name of a Call node, e.g., 'cursor.execute' or 'os.system'."""
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            val = func.value
            parts = [func.attr]
            while isinstance(val, ast.Attribute):
                parts.append(val.attr)
                val = val.value
            if isinstance(val, ast.Name):
                parts.append(val.id)
            parts.reverse()
            return ".".join(parts)
        return ""

    @staticmethod
    def get_source_snippet(code: str, start_line: int, end_line: int) -> str:
        """Extracts source lines from 1-indexed line numbers."""
        lines = code.splitlines()
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        return "\n".join(lines[start_idx:end_idx])

    @staticmethod
    def is_string_concatenation_or_format(node: ast.AST) -> bool:
        """Checks if a node is an f-string, format call, or % operator."""
        if isinstance(node, ast.JoinedStr):
            # F-string
            return True
        if isinstance(node, ast.BinOp):
            # str % var or "str" + var
            if isinstance(node.op, (ast.Mod, ast.Add)):
                return True
        if isinstance(node, ast.Call):
            # .format(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                return True
        return False

    @staticmethod
    def extract_names_from_node(node: ast.AST) -> Set[str]:
        """Extracts all variable names referenced in an AST expression."""
        names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
        return names
