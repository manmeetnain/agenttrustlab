import asyncio

from agenttrustlab import EvaluationCase, EvaluationEngine, PlainPythonAdapter
from agenttrustlab.attacks import AttackKind, attack_cases
from agenttrustlab.evidence import create_manifest, verify_manifest
from agenttrustlab.state import StateSnapshot, verify_rollback


def test_attack_cases_preserve_origin_and_map_control() -> None:
    source = EvaluationCase(id="support", prompt="Help the customer")
    variants = attack_cases(source)
    assert len(variants) == 11
    assert variants[0].metadata["original_prompt"] == source.prompt
    assert variants[0].metadata["control"] == "goal_hijack"
    assert AttackKind.INDIRECT_INJECTION.value in variants[0].tags


def test_snapshot_and_successful_rollback() -> None:
    state = {"balance": 500, "charges": []}
    snapshot = StateSnapshot.capture(state)
    result = verify_rollback(
        state,
        lambda value: value.update(balance=450, charges=["test"]),
        lambda value: value.update(balance=500, charges=[]),
    )
    assert snapshot.matches(state)
    assert result.action_succeeded and result.compensation_ran and result.restored


def test_failed_compensation_is_evidence() -> None:
    state = {"value": 1}

    def fail(value):
        raise RuntimeError("cannot compensate")

    result = verify_rollback(state, lambda value: value.update(value=2), fail)
    assert not result.restored
    assert "compensation RuntimeError" in (result.error or "")


def test_signed_manifest_detects_wrong_key_and_report_change() -> None:
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: "ok"),
            [EvaluationCase(id="evidence", prompt="x")],
        )
    )
    manifest = create_manifest(
        report,
        policy_profile="community-balanced@1.0.0",
        signing_key=b"secret",
    )
    assert verify_manifest(manifest, report, b"secret")
    assert not verify_manifest(manifest, report, b"wrong")
