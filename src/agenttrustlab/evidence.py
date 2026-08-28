"""Canonical, tamper-evident evidence bundles."""

from __future__ import annotations

import hashlib
import hmac
import json
import platform
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agenttrustlab.contracts import EvaluationReport


class EvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    report_id: str
    adapter: str
    python: str
    platform: str
    policy_profile: str
    attack_corpus: str
    report_sha256: str
    limitations: tuple[str, ...] = ()
    signature: str | None = None


def canonical_report(report: EvaluationReport) -> bytes:
    data: dict[str, Any] = report.model_dump(mode="json")
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def create_manifest(
    report: EvaluationReport,
    *,
    policy_profile: str,
    attack_corpus: str = "builtin@1.0.0",
    limitations: tuple[str, ...] = (),
    signing_key: bytes | None = None,
) -> EvidenceManifest:
    digest = hashlib.sha256(canonical_report(report)).hexdigest()
    signature = (
        hmac.new(signing_key, digest.encode(), hashlib.sha256).hexdigest() if signing_key else None
    )
    return EvidenceManifest(
        report_id=str(report.id),
        adapter=report.adapter,
        python=platform.python_version(),
        platform=platform.platform(),
        policy_profile=policy_profile,
        attack_corpus=attack_corpus,
        report_sha256=digest,
        limitations=limitations,
        signature=signature,
    )


def verify_manifest(
    manifest: EvidenceManifest, report: EvaluationReport, signing_key: bytes | None = None
) -> bool:
    digest = hashlib.sha256(canonical_report(report)).hexdigest()
    if not hmac.compare_digest(manifest.report_sha256, digest):
        return False
    if signing_key is None:
        return manifest.signature is None
    expected = hmac.new(signing_key, digest.encode(), hashlib.sha256).hexdigest()
    return manifest.signature is not None and hmac.compare_digest(manifest.signature, expected)
