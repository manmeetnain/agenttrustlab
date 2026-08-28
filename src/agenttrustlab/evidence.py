"""Canonical, tamper-evident evidence bundles."""

from __future__ import annotations

import hashlib
import hmac
import json
import platform
from base64 import b64decode, b64encode
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
    signature_algorithm: str | None = None
    public_key: str | None = None
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
    private_key_pem: bytes | None = None,
) -> EvidenceManifest:
    if signing_key and private_key_pem:
        raise ValueError("choose HMAC or Ed25519 signing, not both")
    digest = hashlib.sha256(canonical_report(report)).hexdigest()
    signature: str | None = None
    algorithm: str | None = None
    public_key: str | None = None
    if private_key_pem:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError as exc:
            raise ImportError("Install AgentTrustLab with the 'signing' extra") from exc
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("signing key must be an Ed25519 private key")
        signature = b64encode(private_key.sign(digest.encode())).decode()
        public_key = b64encode(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode()
        algorithm = "ed25519"
    elif signing_key:
        signature = hmac.new(signing_key, digest.encode(), hashlib.sha256).hexdigest()
        algorithm = "hmac-sha256"
    return EvidenceManifest(
        report_id=str(report.id),
        adapter=report.adapter,
        python=platform.python_version(),
        platform=platform.platform(),
        policy_profile=policy_profile,
        attack_corpus=attack_corpus,
        report_sha256=digest,
        limitations=limitations,
        signature_algorithm=algorithm,
        public_key=public_key,
        signature=signature,
    )


def verify_manifest(
    manifest: EvidenceManifest, report: EvaluationReport, signing_key: bytes | None = None
) -> bool:
    digest = hashlib.sha256(canonical_report(report)).hexdigest()
    if not hmac.compare_digest(manifest.report_sha256, digest):
        return False
    if manifest.signature_algorithm == "ed25519":
        if not manifest.signature or not manifest.public_key:
            return False
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

            Ed25519PublicKey.from_public_bytes(b64decode(manifest.public_key)).verify(
                b64decode(manifest.signature), digest.encode()
            )
            return True
        except (ImportError, InvalidSignature, ValueError):
            return False
    if signing_key is None:
        return manifest.signature is None
    expected = hmac.new(signing_key, digest.encode(), hashlib.sha256).hexdigest()
    return manifest.signature is not None and hmac.compare_digest(manifest.signature, expected)


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Return PEM private and public keys for evidence signing."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise ImportError("Install AgentTrustLab with the 'signing' extra") from exc
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem
