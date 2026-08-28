from agenttrustlab.attacks import BUILTIN_ATTACKS
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT, ReleaseProfile
from agenttrustlab.standards import Framework, references_for


def test_standards_mapping_is_explicit() -> None:
    reference = references_for("goal_hijack")[0]
    assert reference.framework == Framework.OWASP_AGENTIC_2026
    assert reference.control == "ASI01"
    assert references_for("unknown") == ()


def test_every_builtin_attack_has_an_external_mapping() -> None:
    unmapped = [attack.control for attack in BUILTIN_ATTACKS if not references_for(attack.control)]
    assert unmapped == []


def test_high_impact_profile_is_at_least_as_strict() -> None:
    assert COMMUNITY_HIGH_IMPACT.min_task_completion >= COMMUNITY_BALANCED.min_task_completion
    assert COMMUNITY_HIGH_IMPACT.min_evidence_grounding >= COMMUNITY_BALANCED.min_evidence_grounding
    assert (
        COMMUNITY_HIGH_IMPACT.min_deterministic_agreement
        >= COMMUNITY_BALANCED.min_deterministic_agreement
    )


def test_profiles_round_trip() -> None:
    encoded = COMMUNITY_BALANCED.model_dump_json()
    assert ReleaseProfile.model_validate_json(encoded) == COMMUNITY_BALANCED
