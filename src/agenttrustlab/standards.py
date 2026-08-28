"""Versioned public mappings to recognized AI risk frameworks.

Mappings provide traceability, not certification or legal compliance.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Framework(StrEnum):
    OWASP_AGENTIC_2026 = "owasp-agentic-2026"
    MITRE_ATLAS = "mitre-atlas"
    NIST_AI_RMF = "nist-ai-rmf"
    ISO_IEC_23894 = "iso-iec-23894"
    ISO_IEC_42001 = "iso-iec-42001"


class StandardReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    framework: Framework
    control: str
    title: str
    url: str


CONTROL_REFERENCES: dict[str, tuple[StandardReference, ...]] = {
    "goal_hijack": (
        StandardReference(
            framework=Framework.OWASP_AGENTIC_2026,
            control="ASI01",
            title="Agent Goal Hijack",
            url="https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
        ),
    ),
    "tool_misuse": (
        StandardReference(
            framework=Framework.OWASP_AGENTIC_2026,
            control="ASI02",
            title="Tool Misuse",
            url="https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
        ),
    ),
    "memory_poisoning": (
        StandardReference(
            framework=Framework.OWASP_AGENTIC_2026,
            control="ASI06",
            title="Memory & Context Poisoning",
            url="https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
        ),
    ),
    "exfiltration": (
        StandardReference(
            framework=Framework.MITRE_ATLAS,
            control="Exfiltration",
            title="Adversarial Threat Landscape for AI Systems",
            url="https://atlas.mitre.org/",
        ),
    ),
    **{
        control: (
            StandardReference(
                framework=Framework.OWASP_AGENTIC_2026,
                control=identifier,
                title=title,
                url="https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
            ),
        )
        for control, identifier, title in (
            ("identity_privilege_abuse", "ASI03", "Identity & Privilege Abuse"),
            ("agentic_supply_chain", "ASI04", "Agentic Supply Chain Vulnerabilities"),
            ("unexpected_code_execution", "ASI05", "Unexpected Code Execution"),
            ("insecure_inter_agent_communication", "ASI07", "Insecure Inter-Agent Communication"),
            ("cascading_failures", "ASI08", "Cascading Failures"),
            ("human_agent_trust_exploitation", "ASI09", "Human-Agent Trust Exploitation"),
            ("rogue_agents", "ASI10", "Rogue Agents"),
        )
    },
}


def references_for(control: str) -> tuple[StandardReference, ...]:
    """Return immutable external references for a canonical control."""
    return CONTROL_REFERENCES.get(control, ())
