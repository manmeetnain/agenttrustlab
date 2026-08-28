"""State integrity and framework-neutral rollback journals."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict


def state_digest(state: Mapping[str, Any]) -> str:
    encoded = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


class StateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    values: dict[str, Any]
    digest: str

    @classmethod
    def capture(cls, state: Mapping[str, Any]) -> StateSnapshot:
        values = dict(state)
        return cls(values=values, digest=state_digest(values))

    def matches(self, state: Mapping[str, Any]) -> bool:
        return self.digest == state_digest(state)


class RollbackResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_succeeded: bool
    compensation_ran: bool
    restored: bool
    before: StateSnapshot
    after: StateSnapshot
    error: str | None = None


def verify_rollback(
    state: dict[str, Any],
    action: Callable[[dict[str, Any]], None],
    compensate: Callable[[dict[str, Any]], None],
) -> RollbackResult:
    """Execute an action and its compensation, then verify exact restoration."""
    before = StateSnapshot.capture(state)
    action_succeeded = False
    error: str | None = None
    try:
        action(state)
        action_succeeded = True
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    compensation_ran = False
    try:
        compensate(state)
        compensation_ran = True
    except Exception as exc:
        error = f"{error}; " if error else ""
        error += f"compensation {type(exc).__name__}: {exc}"
    after = StateSnapshot.capture(state)
    return RollbackResult(
        action_succeeded=action_succeeded,
        compensation_ran=compensation_ran,
        restored=before.digest == after.digest,
        before=before,
        after=after,
        error=error,
    )
