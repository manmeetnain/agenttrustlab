from agenttrustlab.profiles import COMMUNITY_BALANCED
from agenttrustlab.verdicts import GateStatus, TrustMeasurements, evaluate_release


def measurements(**overrides):
    values = {
        "task_completion": 1.0,
        "critical_findings": 0,
        "unauthorized_tool_calls": 0,
        "protected_memory_mutations": 0,
        "rollback_success": 1.0,
        "evidence_grounding": 1.0,
        "deterministic_agreement": 1.0,
    }
    values.update(overrides)
    return TrustMeasurements(**values)


def test_release_passes_only_when_every_gate_passes() -> None:
    verdict = evaluate_release(measurements(), COMMUNITY_BALANCED)
    assert verdict.status == GateStatus.PASSED
    assert verdict.blockers == ()


def test_critical_finding_cannot_be_averaged_away() -> None:
    verdict = evaluate_release(measurements(critical_findings=1), COMMUNITY_BALANCED)
    assert verdict.status == GateStatus.BLOCKED
    assert verdict.blockers[0].metric == "critical_findings"
    assert verdict.blockers[0].critical


def test_noncritical_threshold_still_blocks_declared_policy() -> None:
    verdict = evaluate_release(measurements(evidence_grounding=0.5), COMMUNITY_BALANCED)
    assert verdict.status == GateStatus.BLOCKED
    assert {check.metric for check in verdict.blockers} == {"evidence_grounding"}
