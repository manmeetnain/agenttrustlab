"""Reproducible evaluation execution engine."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Iterable
from time import perf_counter

from agenttrustlab.adapters import AgentAdapter
from agenttrustlab.contracts import (
    EvaluationCase,
    EvaluationReport,
    RunConfig,
    RunRecord,
    RunStatus,
)
from agenttrustlab.policies import DefaultSafetyPolicy, SafetyPolicy
from agenttrustlab.scenarios import TraceExpectation
from agenttrustlab.scoring import score_result
from agenttrustlab.tools import ToolRegistry
from agenttrustlab.trace_assertions import assert_trace


class EvaluationEngine:
    def __init__(
        self, *, policy: SafetyPolicy | None = None, tools: ToolRegistry | None = None
    ) -> None:
        self.policy = policy or DefaultSafetyPolicy()
        self.tools = tools or ToolRegistry()

    async def evaluate(
        self,
        adapter: AgentAdapter,
        cases: Iterable[EvaluationCase],
        config: RunConfig | None = None,
    ) -> EvaluationReport:
        config = config or RunConfig()
        records: list[RunRecord] = []
        fingerprints: dict[str, set[str]] = {}
        for case in cases:
            fingerprints[case.id] = set()
            for repetition in range(config.repetitions):
                random.seed(config.seed + repetition)
                record = await self._run_one(adapter, case, config)
                records.append(record)
                if record.result:
                    fingerprints[case.id].add(record.result.model_dump_json(exclude={"metadata"}))
                if config.fail_fast and record.status != RunStatus.PASSED:
                    return EvaluationReport(
                        adapter=adapter.name,
                        config=config,
                        runs=tuple(records),
                        deterministic=False,
                    )
        deterministic = all(len(values) <= 1 for values in fingerprints.values())
        return EvaluationReport(
            adapter=adapter.name, config=config, runs=tuple(records), deterministic=deterministic
        )

    async def _run_one(
        self, adapter: AgentAdapter, case: EvaluationCase, config: RunConfig
    ) -> RunRecord:
        started = perf_counter()
        try:
            result = await asyncio.wait_for(
                adapter.run(case, self.tools), timeout=config.timeout_seconds
            )
            latency = (perf_counter() - started) * 1000
            decision = self.policy.evaluate(case, result)
            trace_data = case.metadata.get("trace_expectation")
            trace_assertion = (
                assert_trace(TraceExpectation.model_validate(trace_data), result.tool_calls)
                if trace_data is not None
                else None
            )
            trace_violations = (
                tuple(difference.message for difference in trace_assertion.differences)
                if trace_assertion is not None
                else ()
            )
            score = score_result(
                case,
                result,
                latency,
                trace_passed=trace_assertion.passed if trace_assertion is not None else None,
            )
            violations = (*decision.violations, *trace_violations)
            allowed = decision.allowed and not trace_violations
            status = RunStatus.PASSED if allowed and score.passed else RunStatus.FAILED
            metadata = dict(case.metadata)
            if trace_assertion is not None:
                metadata["trace_assertion"] = trace_assertion.model_dump(mode="json")
            return RunRecord(
                case_id=case.id,
                status=status,
                result=result,
                score=score,
                violations=violations,
                latency_ms=latency,
                metadata=metadata,
            )
        except TimeoutError:
            latency = (perf_counter() - started) * 1000
            return RunRecord(
                case_id=case.id,
                status=RunStatus.ERROR,
                error="agent timed out",
                latency_ms=latency,
                metadata=case.metadata,
            )
        except Exception as exc:
            latency = (perf_counter() - started) * 1000
            return RunRecord(
                case_id=case.id,
                status=RunStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=latency,
                metadata=case.metadata,
            )
