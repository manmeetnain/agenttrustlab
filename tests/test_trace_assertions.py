import pytest
from pydantic import TypeAdapter

from agenttrustlab import ToolCall
from agenttrustlab.scenarios import ArgumentMatcher, TraceExpectation
from agenttrustlab.trace_assertions import DifferenceKind, assert_trace, match_argument


def matcher(value):
    return TypeAdapter(ArgumentMatcher).validate_python(value)


@pytest.mark.parametrize(
    ("specification", "actual", "passed"),
    [
        ({"match": "equals", "value": 4}, 4, True),
        ({"match": "equals", "value": 4}, "4", False),
        ({"match": "contains", "value": "trust"}, "agent trust lab", True),
        ({"match": "contains", "value": 2}, [1, 2, 3], True),
        ({"match": "contains", "value": {"safe": True}}, {"safe": True, "x": 1}, True),
        ({"match": "regex", "pattern": r"^REF-[0-9]+$"}, "REF-42", True),
        ({"match": "regex", "pattern": r"^REF-[0-9]+$"}, 42, False),
        ({"match": "type", "value": "integer"}, 3, True),
        ({"match": "type", "value": "integer"}, True, False),
        ({"match": "type", "value": "number"}, 3.5, True),
        ({"match": "type", "value": "boolean"}, False, True),
        ({"match": "type", "value": "object"}, {}, True),
        ({"match": "type", "value": "array"}, [], True),
        ({"match": "type", "value": "null"}, None, True),
        ({"match": "present", "value": True}, "anything", True),
    ],
)
def test_argument_matchers(specification, actual, passed) -> None:
    observed, reason = match_argument(matcher(specification), actual)
    assert observed is passed
    assert reason


def test_ordered_trace_passes_and_preserves_pairing() -> None:
    expected = TraceExpectation.model_validate(
        {
            "mode": "ordered",
            "calls": [
                {
                    "tool": "lookup",
                    "arguments": {"id": {"match": "equals", "value": "42"}},
                    "allow_unexpected_arguments": False,
                },
                {"tool": "confirm"},
            ],
        }
    )
    actual = (
        ToolCall(id="1", name="lookup", arguments={"id": "42"}),
        ToolCall(id="2", name="confirm"),
    )
    result = assert_trace(expected, actual)
    assert result.passed
    assert result.matched == ((0, 0), (1, 1))


def test_ordered_trace_explains_every_divergence() -> None:
    expected = TraceExpectation.model_validate(
        {
            "calls": [
                {
                    "tool": "lookup",
                    "arguments": {"id": {"match": "equals", "value": "42"}},
                    "allow_unexpected_arguments": False,
                },
                {"tool": "confirm"},
                {"tool": "execute"},
            ]
        }
    )
    actual = (
        ToolCall(id="1", name="confirm"),
        ToolCall(id="2", name="lookup", arguments={"id": "wrong", "admin": True}),
        ToolCall(id="3", name="lookup", arguments={"id": "42"}),
        ToolCall(id="4", name="noise"),
    )
    result = assert_trace(expected, actual)
    kinds = {difference.kind for difference in result.differences}
    assert not result.passed
    assert DifferenceKind.UNEXPECTED_CALL in kinds
    assert DifferenceKind.ARGUMENT_MISMATCH in kinds
    assert DifferenceKind.UNEXPECTED_ARGUMENT in kinds
    assert DifferenceKind.ORDER_MISMATCH in kinds
    assert DifferenceKind.MISSING_CALL in kinds
    assert DifferenceKind.DUPLICATE_CALL in kinds


def test_unordered_optional_and_allow_unexpected() -> None:
    expected = TraceExpectation.model_validate(
        {
            "mode": "unordered",
            "allow_unexpected": True,
            "calls": [
                {"tool": "lookup"},
                {"tool": "optional-audit", "optional": True},
            ],
        }
    )
    actual = (
        ToolCall(id="1", name="unrelated"),
        ToolCall(id="2", name="lookup"),
    )
    assert assert_trace(expected, actual).passed


def test_missing_argument_and_invalid_regex_are_failures() -> None:
    expected = TraceExpectation.model_validate(
        {
            "calls": [
                {
                    "tool": "lookup",
                    "arguments": {
                        "id": {"match": "present"},
                        "reference": {"match": "regex", "pattern": "["},
                    },
                }
            ]
        }
    )
    actual = (ToolCall(id="1", name="lookup", arguments={"reference": "REF-1"}),)
    result = assert_trace(expected, actual)
    assert not result.passed
    assert len(result.differences) == 2
    assert all(item.kind == DifferenceKind.ARGUMENT_MISMATCH for item in result.differences)
