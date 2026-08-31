"""Deterministic expected-versus-observed tool trace assertions."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import regex
from pydantic import BaseModel, ConfigDict

from agenttrustlab.contracts import ToolCall
from agenttrustlab.scenarios import (
    ArgumentMatcher,
    ContainsMatcher,
    EqualsMatcher,
    PresentMatcher,
    RegexMatcher,
    ToolCallExpectation,
    TraceExpectation,
    TypeMatcher,
)

REGEX_TIMEOUT_SECONDS = 0.05
MAX_MATCH_VALUE_LENGTH = 100_000


class TraceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DifferenceKind(StrEnum):
    MISSING_CALL = "missing_call"
    UNEXPECTED_CALL = "unexpected_call"
    ARGUMENT_MISMATCH = "argument_mismatch"
    UNEXPECTED_ARGUMENT = "unexpected_argument"
    ORDER_MISMATCH = "order_mismatch"
    DUPLICATE_CALL = "duplicate_call"


class TraceDifference(TraceModel):
    kind: DifferenceKind
    message: str
    tool: str
    expected_index: int | None = None
    actual_index: int | None = None
    argument: str | None = None
    expected: Any = None
    actual: Any = None


class TraceAssertionResult(TraceModel):
    passed: bool
    differences: tuple[TraceDifference, ...]
    matched: tuple[tuple[int, int], ...] = ()


def _contains(expected: Any, actual: Any) -> bool:
    if isinstance(actual, str) and isinstance(expected, str):
        return expected in actual
    if isinstance(actual, dict) and isinstance(expected, dict):
        return all(key in actual and actual[key] == value for key, value in expected.items())
    if isinstance(actual, (list, tuple, set, frozenset)):
        return expected in actual
    return False


def _type_matches(expected: str, actual: Any) -> bool:
    checks = {
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, (list, tuple)),
        "null": lambda value: value is None,
    }
    return checks[expected](actual)


def match_argument(matcher: ArgumentMatcher, actual: Any) -> tuple[bool, str]:
    """Evaluate one explicit argument matcher with a stable failure reason."""
    if isinstance(matcher, EqualsMatcher):
        passed = actual == matcher.value
        return passed, f"expected equality with {matcher.value!r}"
    if isinstance(matcher, ContainsMatcher):
        passed = _contains(matcher.value, actual)
        return passed, f"expected value to contain {matcher.value!r}"
    if isinstance(matcher, RegexMatcher):
        if not isinstance(actual, str):
            return False, f"expected a string matching /{matcher.pattern}/"
        if len(actual) > MAX_MATCH_VALUE_LENGTH:
            return (
                False,
                f"value exceeds regex matching limit of {MAX_MATCH_VALUE_LENGTH} characters",
            )
        try:
            passed = (
                regex.search(matcher.pattern, actual, timeout=REGEX_TIMEOUT_SECONDS) is not None
            )
        except TimeoutError:
            return False, f"regex /{matcher.pattern}/ exceeded the matching timeout"
        except regex.error as exc:
            return False, f"invalid regex /{matcher.pattern}/: {exc}"
        return passed, f"expected a string matching /{matcher.pattern}/"
    if isinstance(matcher, TypeMatcher):
        passed = _type_matches(matcher.value, actual)
        return passed, f"expected type {matcher.value}"
    if isinstance(matcher, PresentMatcher):
        return matcher.value, "expected argument to be present"
    raise TypeError(f"unsupported matcher: {type(matcher).__name__}")


def _argument_differences(
    expected: ToolCallExpectation,
    actual: ToolCall,
    expected_index: int,
    actual_index: int,
) -> list[TraceDifference]:
    differences: list[TraceDifference] = []
    for name, matcher in expected.arguments.items():
        if name not in actual.arguments:
            differences.append(
                TraceDifference(
                    kind=DifferenceKind.ARGUMENT_MISMATCH,
                    message=f"{actual.name} is missing expected argument {name}",
                    tool=actual.name,
                    expected_index=expected_index,
                    actual_index=actual_index,
                    argument=name,
                    expected=matcher.model_dump(mode="json"),
                )
            )
            continue
        passed, reason = match_argument(matcher, actual.arguments[name])
        if not passed:
            differences.append(
                TraceDifference(
                    kind=DifferenceKind.ARGUMENT_MISMATCH,
                    message=f"{actual.name}.{name}: {reason}",
                    tool=actual.name,
                    expected_index=expected_index,
                    actual_index=actual_index,
                    argument=name,
                    expected=matcher.model_dump(mode="json"),
                    actual=actual.arguments[name],
                )
            )
    if not expected.allow_unexpected_arguments:
        for name in sorted(actual.arguments.keys() - expected.arguments.keys()):
            differences.append(
                TraceDifference(
                    kind=DifferenceKind.UNEXPECTED_ARGUMENT,
                    message=f"{actual.name} received unexpected argument {name}",
                    tool=actual.name,
                    expected_index=expected_index,
                    actual_index=actual_index,
                    argument=name,
                    actual=actual.arguments[name],
                )
            )
    return differences


def _ordered_trace(
    expected: TraceExpectation, actual: tuple[ToolCall, ...]
) -> TraceAssertionResult:
    differences: list[TraceDifference] = []
    matched: list[tuple[int, int]] = []
    cursor = 0
    used: set[int] = set()
    for expected_index, call in enumerate(expected.calls):
        actual_index = next(
            (index for index in range(cursor, len(actual)) if actual[index].name == call.tool),
            None,
        )
        if actual_index is None:
            if call.optional:
                continue
            earlier = next(
                (index for index in range(cursor) if actual[index].name == call.tool), None
            )
            kind = (
                DifferenceKind.ORDER_MISMATCH
                if earlier is not None
                else DifferenceKind.MISSING_CALL
            )
            differences.append(
                TraceDifference(
                    kind=kind,
                    message=(
                        f"expected {call.tool} after observed position {cursor - 1}"
                        if earlier is not None
                        else f"expected call {call.tool} was not observed"
                    ),
                    tool=call.tool,
                    expected_index=expected_index,
                    actual_index=earlier,
                )
            )
            continue
        if not expected.allow_unexpected:
            for index in range(cursor, actual_index):
                if index not in used:
                    differences.append(
                        TraceDifference(
                            kind=DifferenceKind.UNEXPECTED_CALL,
                            message=f"unexpected call {actual[index].name} before {call.tool}",
                            tool=actual[index].name,
                            expected_index=expected_index,
                            actual_index=index,
                        )
                    )
                    used.add(index)
        matched.append((expected_index, actual_index))
        used.add(actual_index)
        differences.extend(
            _argument_differences(call, actual[actual_index], expected_index, actual_index)
        )
        cursor = actual_index + 1
    if not expected.allow_unexpected:
        for index, observed in enumerate(actual):
            if index not in used:
                differences.append(
                    TraceDifference(
                        kind=DifferenceKind.UNEXPECTED_CALL,
                        message=f"unexpected call {observed.name}",
                        tool=observed.name,
                        actual_index=index,
                    )
                )
    differences.extend(_duplicate_differences(expected, actual))
    return TraceAssertionResult(
        passed=not differences, differences=tuple(differences), matched=tuple(matched)
    )


def _unordered_trace(
    expected: TraceExpectation, actual: tuple[ToolCall, ...]
) -> TraceAssertionResult:
    differences: list[TraceDifference] = []
    matched: list[tuple[int, int]] = []
    used: set[int] = set()
    for expected_index, call in enumerate(expected.calls):
        actual_index = next(
            (
                index
                for index, observed in enumerate(actual)
                if index not in used and observed.name == call.tool
            ),
            None,
        )
        if actual_index is None:
            if not call.optional:
                differences.append(
                    TraceDifference(
                        kind=DifferenceKind.MISSING_CALL,
                        message=f"expected call {call.tool} was not observed",
                        tool=call.tool,
                        expected_index=expected_index,
                    )
                )
            continue
        used.add(actual_index)
        matched.append((expected_index, actual_index))
        differences.extend(
            _argument_differences(call, actual[actual_index], expected_index, actual_index)
        )
    if not expected.allow_unexpected:
        for index, observed in enumerate(actual):
            if index not in used:
                differences.append(
                    TraceDifference(
                        kind=DifferenceKind.UNEXPECTED_CALL,
                        message=f"unexpected call {observed.name}",
                        tool=observed.name,
                        actual_index=index,
                    )
                )
    differences.extend(_duplicate_differences(expected, actual))
    return TraceAssertionResult(
        passed=not differences, differences=tuple(differences), matched=tuple(matched)
    )


def _duplicate_differences(
    expected: TraceExpectation, actual: tuple[ToolCall, ...]
) -> list[TraceDifference]:
    limits: dict[str, int] = {}
    for call in expected.calls:
        limits[call.tool] = limits.get(call.tool, 0) + call.maximum_occurrences
    differences: list[TraceDifference] = []
    for tool, maximum in limits.items():
        indexes = [index for index, call in enumerate(actual) if call.name == tool]
        for index in indexes[maximum:]:
            differences.append(
                TraceDifference(
                    kind=DifferenceKind.DUPLICATE_CALL,
                    message=f"{tool} exceeded maximum occurrence count {maximum}",
                    tool=tool,
                    actual_index=index,
                    expected=maximum,
                    actual=len(indexes),
                )
            )
    return differences


def assert_trace(expected: TraceExpectation, actual: tuple[ToolCall, ...]) -> TraceAssertionResult:
    """Compare one normalized trace using the declared ordering semantics."""
    return (
        _ordered_trace(expected, actual)
        if expected.mode == "ordered"
        else _unordered_trace(expected, actual)
    )
