"""
Unit tests for the 5-agent security pipeline:
ScannerAgent, ExploitSimulatorAgent, PatcherAgent, VerifierAgent, AuditCoordinator.
"""

from src.agents.scanner_agent import ScannerAgent
from src.agents.exploit_simulator_agent import ExploitSimulatorAgent
from src.agents.patcher_agent import PatcherAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.coordinator import AuditCoordinator
from src.vulnerability_rules import VulnerabilityCategory


def test_scanner_sql_injection():
    code = (
        "import sqlite3\n"
        "conn = sqlite3.connect('db')\n"
        "cursor = conn.cursor()\n"
        "user_id = '123'\n"
        "cursor.execute(f\"SELECT * FROM users WHERE id = '{user_id}'\")\n"
    )
    scanner = ScannerAgent()
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].category == VulnerabilityCategory.SQL_INJECTION
    assert findings[0].cwe_id == "CWE-89"


def test_scanner_syntax_error_graceful_handling():
    invalid_code = "def broken_syntax(x: return"
    scanner = ScannerAgent()
    findings = scanner.scan_code(invalid_code)
    assert len(findings) == 1
    assert "SyntaxError" in findings[0].cwe_id


def test_exploit_simulator_poc_attachment():
    code = "import os\nos.system(f'ping {host}')\n"
    scanner = ScannerAgent()
    findings = scanner.scan_code(code)
    simulator = ExploitSimulatorAgent()
    verified = simulator.evaluate_findings(findings)
    assert len(verified) == 1
    assert verified[0].poc_payload is not None
    assert verified[0].confidence >= 0.85


def test_patcher_and_verifier_pipeline():
    code = (
        "import hashlib\n"
        "def hash_pass(pwd):\n"
        "    return hashlib.md5(pwd.encode()).hexdigest()\n"
    )
    scanner = ScannerAgent()
    patcher = PatcherAgent()
    verifier = VerifierAgent()

    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].category == VulnerabilityCategory.BROKEN_CRYPTO

    patched_code, diff, patched_findings = patcher.generate_patch(code, findings)
    assert "hashlib.sha256" in patched_code
    assert diff != ""

    v_res, final_findings = verifier.verify_patch(code, patched_code, patched_findings)
    assert v_res.is_success is True
    assert v_res.residual_vulnerabilities_count == 0
    assert v_res.eliminated_count == 1
    assert final_findings[0].is_verified is True


def test_audit_coordinator_end_to_end():
    code = (
        "import pickle\n"
        "def unpack(data):\n"
        "    return pickle.loads(data)\n"
    )
    coordinator = AuditCoordinator()
    report = coordinator.run_pipeline(code, "test_pickle.py")
    assert report.total_findings == 1
    assert report.all_verified is True
    assert report.eliminated_count == 1
    assert report.residual_count == 0
    assert len(report.agent_logs) >= 4
    md = report.to_markdown()
    assert "Multi-Agent Code Security Sentinel Audit Report" in md
    assert "CWE-502" in md
