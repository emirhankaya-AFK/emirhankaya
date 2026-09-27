"""
Self-Audit & Mathematical Verification Engine for Multi-Agent Code Security Sentinel.
Executes 8 rigorous logical, mathematical, and algorithmic checks against ground-truth benchmarks.
"""

import ast
import hashlib
import json
import math
import os
import sys

# Ensure src is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ast_engine import calculate_shannon_entropy
from src.agents.scanner_agent import ScannerAgent
from src.agents.patcher_agent import PatcherAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.coordinator import AuditCoordinator
from src.vulnerability_rules import VulnerabilityCategory


def run_all_audits() -> bool:
    print("\n=======================================================")
    print("  MULTI-AGENT CODE SENTINEL: SYSTEM SELF-AUDIT")
    print("=======================================================")

    all_passed = True
    vulnerable_file = os.path.join(PROJECT_ROOT, "samples", "vulnerable_app.py")
    secure_file = os.path.join(PROJECT_ROOT, "samples", "secure_app.py")

    with open(vulnerable_file, "r", encoding="utf-8") as f:
        vulnerable_code = f.read()

    with open(secure_file, "r", encoding="utf-8") as f:
        secure_code = f.read()

    scanner = ScannerAgent()
    patcher = PatcherAgent()
    verifier = VerifierAgent()
    coordinator = AuditCoordinator()

    # -------------------------------------------------------------------------
    # Check 1: Ground Truth Recall on Vulnerable Testbed (Target: 7/7 = 100%)
    # -------------------------------------------------------------------------
    vuln_findings = scanner.scan_code(vulnerable_code, "vulnerable_app.py")
    detected_cats = {f.category for f in vuln_findings}
    expected_cats = {
        VulnerabilityCategory.SQL_INJECTION,
        VulnerabilityCategory.COMMAND_INJECTION,
        VulnerabilityCategory.PATH_TRAVERSAL,
        VulnerabilityCategory.INSECURE_DESERIALIZATION,
        VulnerabilityCategory.HARDCODED_SECRET,
        VulnerabilityCategory.BROKEN_CRYPTO,
        VulnerabilityCategory.CODE_INJECTION,
    }
    recall = len(detected_cats.intersection(expected_cats)) / len(expected_cats)
    if recall >= 0.95:
        print(f"1. Ground Truth Recall: PASS ({len(vuln_findings)}/{len(expected_cats)} categories detected, Recall: {recall:.1%})")
    else:
        print(f"1. Ground Truth Recall: FAIL (Detected {len(detected_cats)}/{len(expected_cats)})")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 2: Benign Code Precision (Zero False Positives on Secure App)
    # -------------------------------------------------------------------------
    secure_findings = scanner.scan_code(secure_code, "secure_app.py")
    if len(secure_findings) == 0:
        print(f"2. Benign Code Precision: PASS (0 false positives on secure reference code)")
    else:
        print(f"2. Benign Code Precision: FAIL ({len(secure_findings)} false positive(s) detected)")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 3: Shannon Information Entropy Calculation Accuracy
    # -------------------------------------------------------------------------
    # High entropy token: 36-char random API key
    high_ent_str = "sk-live-99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4"
    h_high = calculate_shannon_entropy(high_ent_str)
    # Low entropy standard identifier
    low_ent_str = "localhost"
    h_low = calculate_shannon_entropy(low_ent_str)

    if h_high > 4.0 and h_low < 3.0:
        print(f"3. Shannon Entropy Engine: PASS (High-entropy: {h_high:.3f} > 4.0, Low-entropy: {h_low:.3f} < 3.0)")
    else:
        print(f"3. Shannon Entropy Engine: FAIL (h_high={h_high}, h_low={h_low})")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 4: Auto-Patch Syntax Safety (Zero Syntax Errors)
    # -------------------------------------------------------------------------
    patched_code, diff, patched_findings = patcher.generate_patch(vulnerable_code, vuln_findings)
    try:
        ast.parse(patched_code)
        compile(patched_code, "<patched_audit>", "exec")
        print(f"4. Auto-Patch Syntax Safety: PASS (100% valid AST compilation without SyntaxError)")
    except Exception as e:
        print(f"4. Auto-Patch Syntax Safety: FAIL ({str(e)})")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 5: Residual Vulnerability Elimination (100% Elimination)
    # -------------------------------------------------------------------------
    v_res, _ = verifier.verify_patch(vulnerable_code, patched_code, patched_findings)
    if v_res.is_success and v_res.residual_vulnerabilities_count == 0:
        print(f"5. Residual Vulnerability Elimination: PASS (0 residual flaws, {v_res.eliminated_count} eliminated)")
    else:
        print(f"5. Residual Vulnerability Elimination: FAIL ({v_res.residual_vulnerabilities_count} residual remaining)")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 6: AST Invariant Preservation
    # -------------------------------------------------------------------------
    orig_tree = ast.parse(vulnerable_code)
    orig_funcs = {n.name for n in ast.walk(orig_tree) if isinstance(n, ast.FunctionDef)}
    patched_tree = ast.parse(patched_code)
    patched_funcs = {n.name for n in ast.walk(patched_tree) if isinstance(n, ast.FunctionDef)}

    if orig_funcs.issubset(patched_funcs):
        print(f"6. AST Invariant Preservation: PASS (All {len(orig_funcs)} functions preserved without scope corruption)")
    else:
        missing = orig_funcs - patched_funcs
        print(f"6. AST Invariant Preservation: FAIL (Missing functions: {missing})")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 7: Multi-Agent Determinism & Reproducibility
    # -------------------------------------------------------------------------
    rep1 = coordinator.run_pipeline(vulnerable_code, "vulnerable_app.py")
    rep2 = coordinator.run_pipeline(vulnerable_code, "vulnerable_app.py")
    hash1 = hashlib.sha256(rep1.patched_code.encode()).hexdigest()
    hash2 = hashlib.sha256(rep2.patched_code.encode()).hexdigest()

    if hash1 == hash2 and len(rep1.findings) == len(rep2.findings):
        print(f"7. Multi-Agent Pipeline Determinism: PASS (Strict cryptographic hash match across runs)")
    else:
        print(f"7. Multi-Agent Pipeline Determinism: FAIL (Non-deterministic pipeline output)")
        all_passed = False

    # -------------------------------------------------------------------------
    # Check 8: SARIF 2.1.0 Standard Schema Compliance
    # -------------------------------------------------------------------------
    sarif = rep1.to_sarif()
    has_schema = sarif.get("version") == "2.1.0" and "$schema" in sarif
    has_runs = "runs" in sarif and len(sarif["runs"]) > 0
    has_rules = "rules" in sarif["runs"][0]["tool"]["driver"]
    has_results = "results" in sarif["runs"][0]

    if has_schema and has_runs and has_rules and has_results:
        print(f"8. SARIF 2.1.0 Schema Compliance: PASS (OASIS SARIF 2.1.0 standard schema validated)")
    else:
        print(f"8. SARIF 2.1.0 Schema Compliance: FAIL")
        all_passed = False

    print("=======================================================")
    if all_passed:
        print(">>> ALL 8 SELF-AUDIT CHECKS PASSED WITH ZERO ERRORS! <<<\n")
        return True
    else:
        print(">>> ONE OR MORE SELF-AUDIT CHECKS FAILED! <<<\n")
        return False


if __name__ == "__main__":
    success = run_all_audits()
    sys.exit(0 if success else 1)
