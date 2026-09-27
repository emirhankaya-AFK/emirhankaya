"""
Agent 1: Vulnerability Scanner Agent.
Performs Abstract Syntax Tree analysis, source-sink taint propagation,
and classifies security flaws according to CWE / OWASP Top 10 rules.
"""

import ast
import re
from typing import Dict, List, Optional, Set, Tuple

from src.ast_engine import ASTHelper, TaintScope, calculate_shannon_entropy
from src.vulnerability_rules import (
    Finding,
    RULE_METADATA,
    Severity,
    VulnerabilityCategory,
    calculate_cvss_v31,
)


class VulnerabilityVisitor(ast.NodeVisitor):
    """AST NodeVisitor implementing taint analysis and CWE vulnerability rules."""

    SECRET_NAME_PATTERNS = re.compile(r"(SECRET|API_KEY|TOKEN|PASSWORD|PRIVATE_KEY|AUTH_KEY|CLIENT_SECRET)", re.IGNORECASE)

    def __init__(self, source_code: str, file_path: str = "inline_code.py"):
        self.source_code = source_code
        self.file_path = file_path
        self.findings: List[Finding] = []
        self.current_scope = TaintScope()
        self.lines = source_code.splitlines()

    def _add_finding(
        self,
        category: VulnerabilityCategory,
        node: ast.AST,
        tainted_var: Optional[str] = None,
        taint_source: Optional[str] = None,
        sink_call: Optional[str] = None,
        confidence: float = 0.95,
        custom_desc: Optional[str] = None,
    ) -> None:
        meta = RULE_METADATA[category]
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        col = getattr(node, "col_offset", 0)
        snippet = ASTHelper.get_source_snippet(self.source_code, start_line, end_line)

        finding = Finding(
            category=category,
            cwe_id=meta["cwe_id"],
            title=meta["title"],
            description=custom_desc or meta["description"],
            severity=meta["default_severity"],
            cvss_score=meta["default_cvss"],
            file_path=self.file_path,
            line_number=start_line,
            end_line_number=end_line,
            column=col,
            snippet=snippet,
            tainted_variable=tainted_var,
            taint_source=taint_source,
            sink_call=sink_call,
            confidence=confidence,
            remediation_advice=meta["remediation"],
        )
        self.findings.append(finding)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for hardcoded secrets
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                # Check variable name suspicion
                is_secret_name = bool(self.SECRET_NAME_PATTERNS.search(var_name))
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val_str = node.value.value
                    entropy = calculate_shannon_entropy(val_str)
                    if (is_secret_name and len(val_str) >= 6) or (entropy >= 4.2 and len(val_str) >= 16):
                        self._add_finding(
                            category=VulnerabilityCategory.HARDCODED_SECRET,
                            node=node,
                            tainted_var=var_name,
                            custom_desc=f"Hardcoded sensitive credential '{var_name}' detected with Shannon entropy {entropy:.2f}.",
                            confidence=0.98 if is_secret_name else 0.88,
                        )

                # Check taint source assignment (e.g. user_id = request.args.get('id'))
                if isinstance(node.value, ast.Call):
                    call_name = ASTHelper.get_call_name(node.value)
                    if any(src in call_name for src in ["request.", "input", "sys.argv", "os.environ"]):
                        self.current_scope.taint(var_name, call_name)

                # Sanitization checks:
                if isinstance(node.value, ast.Call):
                    call_name_val = ASTHelper.get_call_name(node.value)
                    if any(cleaner in call_name_val for cleaner in ["basename", "commonpath", "int", "float", "safe_load"]):
                        self.current_scope.sanitize(var_name)

                # Propagate taint if right-hand side references tainted variable
                ref_names = ASTHelper.extract_names_from_node(node.value)
                for rname in ref_names:
                    tainted, src = self.current_scope.is_tainted(rname)
                    if tainted:
                        self.current_scope.taint(var_name, f"derived from {rname} ({src})")
                        break

        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        # Check for path boundary validation guards (startswith, is_relative_to, commonpath)
        for child in ast.walk(node.test):
            if isinstance(child, ast.Call):
                call_name = ASTHelper.get_call_name(child)
                if any(chk in call_name for chk in ["startswith", "is_relative_to", "commonpath"]):
                    names = ASTHelper.extract_names_from_node(child)
                    for n in names:
                        self.current_scope.sanitize(n)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_scope = self.current_scope
        self.current_scope = TaintScope(parent=old_scope)
        for arg in node.args.args:
            if arg.arg not in ["self", "cls"]:
                self.current_scope.taint(arg.arg, f"function parameter '{arg.arg}'")
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_Call(self, node: ast.Call) -> None:
        call_name = ASTHelper.get_call_name(node)

        # 1. SQL Injection Detection
        if any(sink in call_name for sink in ["execute", "executemany", "execute_query"]):
            if node.args:
                query_arg = node.args[0]
                if ASTHelper.is_string_concatenation_or_format(query_arg):
                    self._add_finding(
                        category=VulnerabilityCategory.SQL_INJECTION,
                        node=node,
                        sink_call=call_name,
                        custom_desc=f"Unparameterized SQL query dynamically built and passed to '{call_name}'.",
                        confidence=0.96,
                    )
                elif isinstance(query_arg, ast.Name):
                    tainted, src = self.current_scope.is_tainted(query_arg.id)
                    if tainted:
                        self._add_finding(
                            category=VulnerabilityCategory.SQL_INJECTION,
                            node=node,
                            tainted_var=query_arg.id,
                            taint_source=src,
                            sink_call=call_name,
                            confidence=0.95,
                        )

        # 2. Command Injection Detection
        if call_name in ["os.system", "os.popen", "subprocess.call", "subprocess.Popen", "subprocess.run"]:
            is_shell_true = False
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    is_shell_true = True

            if call_name in ["os.system", "os.popen"] or is_shell_true:
                if node.args:
                    cmd_arg = node.args[0]
                    if ASTHelper.is_string_concatenation_or_format(cmd_arg):
                        self._add_finding(
                            category=VulnerabilityCategory.COMMAND_INJECTION,
                            node=node,
                            sink_call=call_name,
                            confidence=0.98,
                        )
                    elif isinstance(cmd_arg, ast.Name):
                        tainted, src = self.current_scope.is_tainted(cmd_arg.id)
                        if tainted or call_name in ["os.system", "os.popen"]:
                            self._add_finding(
                                category=VulnerabilityCategory.COMMAND_INJECTION,
                                node=node,
                                tainted_var=cmd_arg.id,
                                taint_source=src or "untrusted variable",
                                sink_call=call_name,
                                confidence=0.95 if tainted else 0.90,
                            )

        # 3. Path Traversal Detection (File Sinks: open, os.remove, os.unlink, shutil.rmtree)
        if call_name in ["open", "os.remove", "os.unlink", "shutil.rmtree"]:
            if node.args:
                path_arg = node.args[0]
                if ASTHelper.is_string_concatenation_or_format(path_arg):
                    self._add_finding(
                        category=VulnerabilityCategory.PATH_TRAVERSAL,
                        node=node,
                        sink_call=call_name,
                        confidence=0.92,
                    )
                elif isinstance(path_arg, ast.Name):
                    tainted, src = self.current_scope.is_tainted(path_arg.id)
                    if tainted:
                        self._add_finding(
                            category=VulnerabilityCategory.PATH_TRAVERSAL,
                            node=node,
                            tainted_var=path_arg.id,
                            taint_source=src,
                            sink_call=call_name,
                            confidence=0.91,
                        )

        # 4. Insecure Deserialization
        if call_name in ["pickle.loads", "pickle.load", "_pickle.loads", "yaml.unsafe_load"]:
            self._add_finding(
                category=VulnerabilityCategory.INSECURE_DESERIALIZATION,
                node=node,
                sink_call=call_name,
                confidence=0.99,
            )

        # 5. Broken Cryptography (MD5 / SHA-1)
        if call_name in ["hashlib.md5", "hashlib.sha1"]:
            self._add_finding(
                category=VulnerabilityCategory.BROKEN_CRYPTO,
                node=node,
                sink_call=call_name,
                custom_desc=f"Deprecated and collision-vulnerable hashing function '{call_name}' detected.",
                confidence=0.95,
            )

        # 6. Dynamic Code Injection (eval / exec)
        if call_name in ["eval", "exec"]:
            self._add_finding(
                category=VulnerabilityCategory.CODE_INJECTION,
                node=node,
                sink_call=call_name,
                confidence=0.99,
            )

        self.generic_visit(node)


class ScannerAgent:
    """Agent 1: Performs static AST inspection and taint tracking."""

    def __init__(self, name: str = "ScannerAgent"):
        self.name = name

    def scan_code(self, source_code: str, file_path: str = "main.py") -> List[Finding]:
        """Parses Python source code and identifies all vulnerability candidates."""
        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            return [
                Finding(
                    category=VulnerabilityCategory.CODE_INJECTION,
                    cwe_id="CWE-SyntaxError",
                    title="Syntax Error in Target Source",
                    description=f"File could not be parsed by AST engine: {str(e)}",
                    severity=Severity.INFO,
                    cvss_score=0.0,
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    end_line_number=e.lineno or 1,
                    column=e.offset or 0,
                    snippet="",
                    confidence=1.0,
                )
            ]

        visitor = VulnerabilityVisitor(source_code, file_path)
        visitor.visit(tree)
        return visitor.findings
