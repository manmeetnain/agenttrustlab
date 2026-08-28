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
from agenttrustlab.framework_adapters import LangGraphAdapter, MCPAdapter, PydanticAIAdapter
from agenttrustlab.policies import DefaultSafetyPolicy, PolicyDecision
from agenttrustlab.tools import SimulatedTool, ToolRegistry

__all__ = [
    "AgentAdapter",
    "AgentResult",
    "DefaultSafetyPolicy",
    "EvaluationCase",
    "EvaluationEngine",
    "EvaluationReport",
    "ExpectedOutcome",
    "LangGraphAdapter",
    "MCPAdapter",
    "PlainPythonAdapter",
    "PolicyDecision",
    "PydanticAIAdapter",
    "RunConfig",
    "RunStatus",
    "ScoreCard",
    "SimulatedTool",
    "ToolCall",
    "ToolRegistry",
    "ToolResult",
]
__version__ = "0.1.0"
