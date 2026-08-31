"""Versioned execution-target configuration for scenario runs."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from yaml.tokens import AliasToken

from agenttrustlab.adapters import AgentAdapter, PlainPythonAdapter
from agenttrustlab.scenarios import MAX_SCENARIO_BYTES, MAX_YAML_ALIASES

EXAMPLE_TARGET_YAML = """version: "1"
target:
  name: local-refund-agent
  adapter: plain-python
  entrypoint: agent.py:agent
"""

EXAMPLE_AGENT_PY = '''from agenttrustlab import AgentResult, ToolCall, ToolResult


def agent(case, tools):
    """Safe starter agent: inspect the order, then request confirmation."""
    return AgentResult(
        output="Confirmation is required before the refund can be executed.",
        tool_calls=(
            ToolCall(id="lookup-1", name="lookup_order", arguments={"order_id": "4821"}),
            ToolCall(id="confirm-1", name="request_confirmation", arguments={}),
        ),
        tool_results=(
            ToolResult(call_id="lookup-1", output={"order_id": "4821", "status": "paid"}),
        ),
    )
'''


class TargetModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PlainPythonTarget(TargetModel):
    name: str = Field(min_length=1)
    adapter: Literal["plain-python"]
    entrypoint: str = Field(min_length=3, pattern=r"^.+\.py:[a-zA-Z_][a-zA-Z0-9_]*$")


class TargetFile(TargetModel):
    version: Literal["1"]
    target: PlainPythonTarget


def load_target(path: str | Path) -> TargetFile:
    """Load one bounded, declarative target file."""
    source = Path(path)
    payload = source.read_bytes()
    if len(payload) > MAX_SCENARIO_BYTES:
        raise ValueError(f"target exceeds {MAX_SCENARIO_BYTES} bytes")
    text = payload.decode("utf-8")
    aliases = sum(
        isinstance(token, AliasToken) for token in yaml.scan(text, Loader=yaml.SafeLoader)
    )
    if aliases > MAX_YAML_ALIASES:
        raise ValueError(f"target exceeds {MAX_YAML_ALIASES} YAML aliases")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("target document must be a YAML mapping")
    return TargetFile.model_validate(data)


def _load_entrypoint(specification: str, base_directory: Path) -> Any:
    relative_path, attribute = specification.rsplit(":", 1)
    module_path = (base_directory / relative_path).resolve()
    if not module_path.is_file():
        raise ValueError(f"target entrypoint file does not exist: {module_path}")
    spec = importlib.util.spec_from_file_location("agenttrust_target", module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import target entrypoint: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = getattr(module, attribute, None)
    if not callable(value):
        raise ValueError(f"target entrypoint is not callable: {specification}")
    return value


def create_adapter(target_file: TargetFile, config_path: str | Path) -> AgentAdapter:
    """Instantiate the declared adapter without making policy decisions."""
    target = target_file.target
    if target.adapter == "plain-python":
        return PlainPythonAdapter(_load_entrypoint(target.entrypoint, Path(config_path).parent))
    raise ValueError(f"unsupported target adapter: {target.adapter}")
