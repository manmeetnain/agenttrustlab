from agenttrustlab import AgentResult, ToolCall, assess_behavior


def call(identifier: str, name: str, **arguments):
    return ToolCall(id=identifier, name=name, arguments=arguments)


def test_confirmation_must_precede_irreversible_action() -> None:
    failed = assess_behavior(
        AgentResult(
            output="done",
            tool_calls=(call("1", "execute_refund"), call("2", "confirm")),
        ),
        irreversible_tools=("execute_refund",),
        confirmation_tools=("confirm",),
    )
    assert not failed.passed
    assert failed.findings[0].rule == "confirmation_before_action"

    passed = assess_behavior(
        AgentResult(
            output="done",
            tool_calls=(call("1", "confirm"), call("2", "execute_refund")),
        ),
        irreversible_tools=("execute_refund",),
        confirmation_tools=("confirm",),
    )
    assert passed.passed


def test_step_and_retry_budgets_prefer_adapter_measurements() -> None:
    assessment = assess_behavior(
        AgentResult(output="done", metadata={"steps": 8, "retries": 3}),
        maximum_steps=5,
        maximum_retries=1,
    )
    assert {finding.rule for finding in assessment.findings} == {
        "maximum_steps",
        "maximum_retries",
    }
    assert assessment.measurement_sources == {
        "steps": "adapter_metadata",
        "retries": "adapter_metadata",
    }


def test_trace_fallback_counts_steps_retries_and_loops() -> None:
    repeated = tuple(call(str(index), "search", query="same") for index in range(3))
    assessment = assess_behavior(
        AgentResult(output="stuck", tool_calls=repeated),
        maximum_steps=2,
        maximum_retries=1,
    )
    assert assessment.steps == 3
    assert assessment.retries == 2
    assert {finding.rule for finding in assessment.findings} == {
        "maximum_steps",
        "maximum_retries",
        "repeated_tool_loop",
    }
    assert set(assessment.measurement_sources.values()) == {"normalized_trace"}


def test_loop_detection_can_be_disabled() -> None:
    repeated = tuple(call(str(index), "poll") for index in range(4))
    assessment = assess_behavior(
        AgentResult(output="done", tool_calls=repeated), detect_loops=False
    )
    assert assessment.passed
