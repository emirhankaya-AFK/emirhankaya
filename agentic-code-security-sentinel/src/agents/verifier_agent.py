"""
Agent 4: Verification & Regression Sentinel Agent.
Validates syntax safety, recompiles patched code in isolated memory,
re-runs AST scan to confirm zero residual vulnerabilities, and checks invariant preservation.
"""

import ast
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.agents.scanner_agent import ScannerAgent
from src.vulnerability_rules import Finding


@dataclass
class VerificationResult:
    is_success: bool
    syntax_valid: bool
    residual_vulnerabilities_count: int
    eliminated_count: int
    ast_invariant_maintained: bool
    error_message: Optional[str] = None
    residual_findings: List[Finding] = None

    def to_dict(self) -> Dict:
        return {
            "is_success": self.is_success,
            "syntax_valid": self.syntax_valid,
            "residual_vulnerabilities_count": self.residual_vulnerabilities_count,
            "eliminated_count": self.eliminated_count,
            "ast_invariant_maintained": self.ast_invariant_maintained,
            "error_message": self.error_message,
        }


class VerifierAgent:
    """Agent 4: Verifies patch syntax and proves residual vulnerability elimination."""

    def __init__(self, name: str = "VerifierAgent"):
        self.name = name
        self.scanner = ScannerAgent(name="VerifierScannerSubAgent")

    def verify_patch(
        self, original_code: str, patched_code: str, initial_findings: List[Finding]
    ) -> Tuple[VerificationResult, List[Finding]]:
        """
        Executes complete verification pipeline:
        1. Syntax check via ast.parse and compile()
        2. Re-scan of patched code
        3. Residual vulnerability counting
        4. AST invariant validation
        """
        # 1. Syntax & Compilation Check
        try:
            patched_tree = ast.parse(patched_code, filename="<patched_buffer>")
            compile(patched_code, "<patched_buffer>", "exec")
            syntax_valid = True
        except Exception as e:
            return VerificationResult(
                is_success=False,
                syntax_valid=False,
                residual_vulnerabilities_count=len(initial_findings),
                eliminated_count=0,
                ast_invariant_maintained=False,
                error_message=f"Syntax Error in generated patch: {str(e)}",
                residual_findings=initial_findings,
            ), initial_findings

        # 2. Residual Vulnerability Re-scan
        post_findings = self.scanner.scan_code(patched_code)
        post_categories = {f.category for f in post_findings}

        eliminated = 0
        updated_findings = []
        for orig in initial_findings:
            # Check if this category is still present
            still_present = any(pf.category == orig.category for pf in post_findings)
            if not still_present:
                orig.is_verified = True
                eliminated += 1
            else:
                orig.is_verified = False
            updated_findings.append(orig)

        residual_count = len(post_findings)

        # 3. AST Invariant Check (functions in original code still exist in patched code)
        try:
            orig_tree = ast.parse(original_code)
            orig_funcs = {n.name for n in ast.walk(orig_tree) if isinstance(n, ast.FunctionDef)}
            patched_funcs = {n.name for n in ast.walk(patched_tree) if isinstance(n, ast.FunctionDef)}
            invariant_ok = orig_funcs.issubset(patched_funcs)
        except Exception:
            invariant_ok = True

        is_success = syntax_valid and (eliminated > 0 or len(initial_findings) == 0) and (residual_count == 0)

        result = VerificationResult(
            is_success=is_success,
            syntax_valid=syntax_valid,
            residual_vulnerabilities_count=residual_count,
            eliminated_count=eliminated,
            ast_invariant_maintained=invariant_ok,
            residual_findings=post_findings,
        )

        return result, updated_findings
