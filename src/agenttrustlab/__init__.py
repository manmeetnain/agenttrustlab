"""AgentTrustLab public API."""

from agenttrustlab.adapters import AgentAdapter, PlainPythonAdapter
from agenttrustlab.contracts import (
    AgentResult,
    EvaluationCase,
    EvaluationReport,
    ExpectedOutcome,
    RunConfig,
    RunStatus,
    ScoreCard,
    ToolCall,
    ToolResult,
)
from agenttrustlab.engine import EvaluationEngine
from agenttrustlab.framework_adapters import (
    AutoGenAdapter,
    CrewAIAdapter,
    GoogleADKAdapter,
    LangGraphAdapter,
    MCPAdapter,
    PydanticAIAdapter,
    SmolagentsAdapter,
)
from agenttrustlab.policies import DefaultSafetyPolicy, PolicyDecision
from agenttrustlab.scenarios import (
    ExpandedScenario,
    ScenarioDefinition,
    ScenarioFile,
    expand_scenario,
    load_scenario,
    to_evaluation_case,
)
from agenttrustlab.targets import TargetFile, create_adapter, load_target
from agenttrustlab.tools import SimulatedTool, ToolRegistry
from agenttrustlab.trace_assertions import (
    DifferenceKind,
    TraceAssertionResult,
    TraceDifference,
    assert_trace,
)

__all__ = [
    "AgentAdapter",
    "AgentResult",
    "AutoGenAdapter",
    "CrewAIAdapter",
    "DefaultSafetyPolicy",
    "DifferenceKind",
    "EvaluationCase",
    "EvaluationEngine",
    "EvaluationReport",
    "ExpandedScenario",
    "ExpectedOutcome",
    "GoogleADKAdapter",
    "LangGraphAdapter",
    "MCPAdapter",
    "PlainPythonAdapter",
    "PolicyDecision",
    "PydanticAIAdapter",
    "RunConfig",
    "RunStatus",
    "ScenarioDefinition",
    "ScenarioFile",
    "ScoreCard",
    "SimulatedTool",
    "SmolagentsAdapter",
    "TargetFile",
    "ToolCall",
    "ToolRegistry",
    "ToolResult",
    "TraceAssertionResult",
    "TraceDifference",
    "assert_trace",
    "create_adapter",
    "expand_scenario",
    "load_scenario",
    "load_target",
    "to_evaluation_case",
]
__version__ = "0.1.0"
