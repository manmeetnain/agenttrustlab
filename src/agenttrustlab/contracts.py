"""Stable, serializable contracts at the heart of AgentTrustLab."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RunStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    BLOCKED = "blocked"


class ToolCall(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(StrictModel):
    call_id: str
    output: Any = None
    error: str | None = None
    latency_ms: float = Field(default=0, ge=0)


class Evidence(StrictModel):
    source: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(StrictModel):
    output: str
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    memory_after: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExpectedOutcome(StrictModel):
    contains: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()
    required_tools: tuple[str, ...] = ()
    forbidden_tools: tuple[str, ...] = ()
    min_evidence: int = Field(default=0, ge=0)
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_latency_ms: float | None = Field(default=None, ge=0)


class EvaluationCase(StrictModel):
    id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    prompt: str = Field(min_length=1)
    expected: ExpectedOutcome = Field(default_factory=ExpectedOutcome)
    memory_before: dict[str, Any] = Field(default_factory=dict)
    tags: frozenset[str] = frozenset()
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunConfig(StrictModel):
    seed: int = 0
    timeout_seconds: float = Field(default=30, gt=0, le=3600)
    repetitions: int = Field(default=1, ge=1, le=100)
    fail_fast: bool = False


class MetricScore(StrictModel):
    name: str
    value: float = Field(ge=0, le=1)
    weight: float = Field(default=1, ge=0)
    reason: str = ""


class ScoreCard(StrictModel):
    metrics: tuple[MetricScore, ...]
    total: float = Field(ge=0, le=1)
    passed: bool

    @model_validator(mode="after")
    def total_matches_metrics(self) -> ScoreCard:
        weights = sum(m.weight for m in self.metrics)
        expected = sum(m.value * m.weight for m in self.metrics) / weights if weights else 0
        if abs(self.total - expected) > 1e-6:
            raise ValueError("total must equal the weighted metric mean")
        return self


class RunRecord(StrictModel):
    case_id: str
    status: RunStatus
    result: AgentResult | None = None
    score: ScoreCard | None = None
    violations: tuple[str, ...] = ()
    error: str | None = None
    latency_ms: float = Field(default=0, ge=0)


class EvaluationReport(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    adapter: str
    config: RunConfig
    runs: tuple[RunRecord, ...]
    deterministic: bool = True

    @property
    def passed(self) -> bool:
        return bool(self.runs) and all(run.status == RunStatus.PASSED for run in self.runs)
