"""
Unit tests for AST engine, taint scope, and Shannon entropy computation.
"""

import ast
from src.ast_engine import ASTHelper, TaintScope, calculate_shannon_entropy


def test_shannon_entropy_properties():
    # Empty string should yield 0.0
    assert calculate_shannon_entropy("") == 0.0
    # Single repeating char has zero uncertainty
    assert calculate_shannon_entropy("AAAAAAA") == 0.0
    # Binary string with equal probability has entropy 1.0
    assert abs(calculate_shannon_entropy("01010101") - 1.0) < 1e-6
    # Complex key has high entropy
    key = "sk-ant-api03-abcdef1234567890XYZ"
    assert calculate_shannon_entropy(key) > 4.0


def test_taint_scope_hierarchy():
    parent_scope = TaintScope()
    parent_scope.taint("user_input", "request.args.get('q')")

    child_scope = TaintScope(parent=parent_scope)
    child_scope.taint("local_var", "sys.argv[1]")

    # Child should see both local and parent taint
    is_tainted, src = child_scope.is_tainted("local_var")
    assert is_tainted is True
    assert "sys.argv" in src

    is_tainted_parent, src_parent = child_scope.is_tainted("user_input")
    assert is_tainted_parent is True
    assert "request.args" in src_parent

    # Untainted variable
    is_safe, _ = child_scope.is_tainted("safe_const")
    assert is_safe is False


def test_ast_helpers():
    code = "import os\nos.system('ls')\nx = f'hello {name}'"
    tree = ast.parse(code)

    call_node = [n for n in ast.walk(tree) if isinstance(n, ast.Call)][0]
    call_name = ASTHelper.get_call_name(call_node)
    assert call_name == "os.system"

    joined_str = [n for n in ast.walk(tree) if isinstance(n, ast.JoinedStr)][0]
    assert ASTHelper.is_string_concatenation_or_format(joined_str) is True

    names = ASTHelper.extract_names_from_node(joined_str)
    assert "name" in names
