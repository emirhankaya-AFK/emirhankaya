"""
Unit tests for SARIF 2.1.0 report generation and GitHub CodeQL compatibility.
"""

from src.agents.coordinator import AuditCoordinator


def test_sarif_generation_structure():
    code = (
        "def run_cmd(user_cmd):\n"
        "    import os\n"
        "    os.system(user_cmd)\n"
    )
    coordinator = AuditCoordinator()
    report = coordinator.run_pipeline(code, "runner.py")
    sarif = report.to_sarif()

    # Structural assertions according to OASIS SARIF v2.1.0 standard
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    tool = run["tool"]["driver"]
    assert tool["name"] == "MultiAgentCodeSentinel"
    assert tool["semanticVersion"] == "1.0.0"
    assert len(tool["rules"]) > 0

    results = run["results"]
    assert len(results) == 1
    result = results[0]
    assert result["ruleId"] == "CWE-78"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "runner.py"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 3
    assert result["properties"]["cvssScore"] >= 9.0
