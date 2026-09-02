"""Deterministic severity and remediation guidance for common trust findings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Remediation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: str
    guidance: str


RULES: tuple[tuple[tuple[str, ...], Remediation], ...] = (
    (
        ("forbidden tool", "irreversible tool"),
        Remediation(
            severity="critical",
            guidance=(
                "Enforce tool allowlists and require a verified confirmation token before "
                "execution."
            ),
        ),
    ),
    (
        ("prompt injection", "protected memory"),
        Remediation(
            severity="high",
            guidance=(
                "Treat retrieved content as data, isolate protected state, and reject instruction "
                "overrides."
            ),
        ),
    ),
    (
        ("argument", "equality", "unexpected call"),
        Remediation(
            severity="high",
            guidance="Validate tool names and arguments against a strict schema before dispatch.",
        ),
    ),
    (
        ("loop", "retry budget", "step budget"),
        Remediation(
            severity="medium",
            guidance="Add bounded retries, idempotency keys, backoff, and a circuit breaker.",
        ),
    ),
    (
        ("cost", "latency"),
        Remediation(
            severity="medium",
            guidance=(
                "Apply per-run budgets and terminate execution when the declared ceiling is "
                "reached."
            ),
        ),
    ),
)


def remediation_for(message: str) -> Remediation:
    """Map a normalized finding to stable, reviewable remediation guidance."""
    normalized = message.casefold()
    for needles, remediation in RULES:
        if any(needle in normalized for needle in needles):
            return remediation
    return Remediation(
        severity="medium",
        guidance=(
            "Inspect the normalized trace, tighten the scenario contract, and add a regression "
            "case."
        ),
    )
