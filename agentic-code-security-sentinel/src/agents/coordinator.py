"""
Agent 5: Audit Coordinator Agent.
Orchestrates multi-agent pipeline, enforces consensus, logs audit timeline,
and generates standardized SARIF 2.1.0 and Markdown security audit reports.
"""

from dataclasses import dataclass, field
import datetime
import json
from typing import Any, Dict, List, Optional

from src.agents.exploit_simulator_agent import ExploitSimulatorAgent
from src.agents.patcher_agent import PatcherAgent
from src.agents.scanner_agent import ScannerAgent
from src.agents.verifier_agent import VerificationResult, VerifierAgent
from src.vulnerability_rules import Finding, RULE_METADATA


@dataclass
class AuditPipelineReport:
    timestamp: str
    target_file: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    eliminated_count: int
    residual_count: int
    all_verified: bool
    findings: List[Finding]
    original_code: str
    patched_code: str
    unified_diff: str
    verification_result: VerificationResult
    agent_logs: List[Dict[str, Any]] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# Multi-Agent Code Security Sentinel Audit Report",
            f"**Audit Timestamp:** `{self.timestamp}`  ",
            f"**Target:** `{self.target_file}`  ",
            f"**Overall Status:** `{'PASSED - ALL VULNERABILITIES REMEDIATED' if self.all_verified else 'NEEDS MANUAL REVIEW'}`\n",
            f"## Executive Summary",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Total Findings Discovered | **{self.total_findings}** |",
            f"| Critical Severity | **{self.critical_count}** |",
            f"| High Severity | **{self.high_count}** |",
            f"| Medium Severity | **{self.medium_count}** |",
            f"| Successfully Auto-Patched | **{self.eliminated_count}** |",
            f"| Residual Vulnerabilities | **{self.residual_count}** |",
            f"| Syntax Verification | `{'VALID' if self.verification_result.syntax_valid else 'INVALID'}` |\n",
            f"## Detailed Findings & Remediation\n",
        ]

        for i, f in enumerate(self.findings, 1):
            status_badge = "✅ REMEDIATED" if f.is_verified else "⚠️ UNVERIFIED"
            lines.extend([
                f"### {i}. [{f.cwe_id}] {f.title} ({status_badge})",
                f"- **Severity:** `{f.severity.value}` (CVSS Base: `{f.cvss_score}`)",
                f"- **Location:** `{f.file_path}` Line `{f.line_number}`",
                f"- **Description:** {f.description}",
                f"- **PoC Payload:** `{f.poc_payload or 'N/A'}`",
                f"- **Remediation Strategy:** {f.remediation_advice}\n",
                f"```python",
                f"# Vulnerable Code Snippet",
                f"{f.snippet}",
                f"```\n",
            ])

        if self.unified_diff:
            lines.extend([
                f"## Unified Remediation Patch Diff",
                f"```diff",
                f"{self.unified_diff}",
                f"```\n",
            ])

        return "\n".join(lines)

    def to_sarif(self) -> Dict[str, Any]:
        """Generates standard SARIF 2.1.0 output compliant with GitHub CodeQL."""
        rules = []
        for cat, meta in RULE_METADATA.items():
            rules.append({
                "id": meta["cwe_id"],
                "name": cat.value,
                "shortDescription": {"text": meta["title"]},
                "fullDescription": {"text": meta["description"]},
                "defaultConfiguration": {
                    "level": "error" if meta["default_severity"].value in ["CRITICAL", "HIGH"] else "warning"
                },
                "properties": {
                    "security-severity": str(meta["default_cvss"])
                }
            })

        results = []
        for f in self.findings:
            results.append({
                "ruleId": f.cwe_id,
                "level": "error" if f.severity.value in ["CRITICAL", "HIGH"] else "warning",
                "message": {"text": f.description},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": f.file_path},
                            "region": {
                                "startLine": f.line_number,
                                "endLine": f.end_line_number,
                                "startColumn": f.column + 1,
                            }
                        }
                    }
                ],
                "properties": {
                    "cvssScore": f.cvss_score,
                    "confidence": f.confidence,
                    "isRemediated": f.is_verified,
                }
            })

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "MultiAgentCodeSentinel",
                            "semanticVersion": "1.0.0",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ]
        }


class AuditCoordinator:
    """Agent 5: Coordinates the multi-agent pipeline and synthesizes reports."""

    def __init__(self):
        self.scanner = ScannerAgent()
        self.simulator = ExploitSimulatorAgent()
        self.patcher = PatcherAgent()
        self.verifier = VerifierAgent()

    def run_pipeline(self, source_code: str, file_path: str = "app.py") -> AuditPipelineReport:
        logs = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Scanner Agent
        logs.append({"agent": "ScannerAgent", "action": "Scanning AST & computing taint paths...", "status": "RUNNING"})
        findings = self.scanner.scan_code(source_code, file_path)
        logs.append({
            "agent": "ScannerAgent",
            "action": f"Identified {len(findings)} suspect vulnerability candidate(s).",
            "status": "COMPLETED",
        })

        # 2. Exploit Simulator Agent
        logs.append({"agent": "ExploitSimulatorAgent", "action": "Simulating reachability & synthesizing PoCs...", "status": "RUNNING"})
        verified_findings = self.simulator.evaluate_findings(findings)
        logs.append({
            "agent": "ExploitSimulatorAgent",
            "action": f"Verified {len(verified_findings)} exploitable finding(s) with PoC payloads.",
            "status": "COMPLETED",
        })

        # 3. Patcher Agent
        logs.append({"agent": "PatcherAgent", "action": "Synthesizing AST transformations and unified diffs...", "status": "RUNNING"})
        patched_code, diff, patched_findings = self.patcher.generate_patch(source_code, verified_findings)
        logs.append({
            "agent": "PatcherAgent",
            "action": "Generated unified diff for all candidate vulnerabilities.",
            "status": "COMPLETED",
        })

        # 4. Verifier Agent
        logs.append({"agent": "VerifierAgent", "action": "Recompiling patched AST and testing residual vulnerabilities...", "status": "RUNNING"})
        verification_result, final_findings = self.verifier.verify_patch(source_code, patched_code, patched_findings)
        logs.append({
            "agent": "VerifierAgent",
            "action": (
                f"Verification {'PASSED' if verification_result.is_success else 'FAILED'}: "
                f"{verification_result.eliminated_count} eliminated, {verification_result.residual_vulnerabilities_count} residual."
            ),
            "status": "COMPLETED",
        })

        crit_count = sum(1 for f in final_findings if f.severity.value == "CRITICAL")
        high_count = sum(1 for f in final_findings if f.severity.value == "HIGH")
        med_count = sum(1 for f in final_findings if f.severity.value == "MEDIUM")

        return AuditPipelineReport(
            timestamp=timestamp,
            target_file=file_path,
            total_findings=len(final_findings),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            eliminated_count=verification_result.eliminated_count,
            residual_count=verification_result.residual_vulnerabilities_count,
            all_verified=verification_result.is_success,
            findings=final_findings,
            original_code=source_code,
            patched_code=patched_code,
            unified_diff=diff,
            verification_result=verification_result,
            agent_logs=logs,
        )
