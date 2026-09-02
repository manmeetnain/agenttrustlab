from agenttrustlab.remediation import remediation_for


def test_remediation_prioritizes_irreversible_and_injection_findings() -> None:
    assert remediation_for("forbidden tool use: delete").severity == "critical"
    assert remediation_for("output appears to follow prompt injection").severity == "high"


def test_remediation_has_stable_fallback() -> None:
    result = remediation_for("custom evaluator failed")
    assert result.severity == "medium"
    assert "regression" in result.guidance
