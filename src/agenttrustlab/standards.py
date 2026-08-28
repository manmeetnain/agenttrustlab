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
}


def references_for(control: str) -> tuple[StandardReference, ...]:
    """Return immutable external references for a canonical control."""
    return CONTROL_REFERENCES.get(control, ())
