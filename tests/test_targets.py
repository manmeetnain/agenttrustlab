import pytest
from pydantic import ValidationError

from agenttrustlab import EvaluationCase, ToolRegistry
from agenttrustlab.targets import create_adapter, load_target


def write_target(tmp_path, entrypoint: str = "agent.py:agent"):
    target = tmp_path / "target.yml"
    target.write_text(
        'version: "1"\n'
        "target:\n"
        "  name: test-agent\n"
        "  adapter: plain-python\n"
        f"  entrypoint: {entrypoint}\n",
        encoding="utf-8",
    )
    return target


def test_load_and_create_plain_python_target(tmp_path) -> None:
    agent = tmp_path / "agent.py"
    agent.write_text("def agent(case, tools): return 'ready'\n", encoding="utf-8")
    target_path = write_target(tmp_path)
    target = load_target(target_path)
    adapter = create_adapter(target, target_path)

    import asyncio

    result = asyncio.run(adapter.run(EvaluationCase(id="target", prompt="x"), ToolRegistry()))
    assert result.output == "ready"


def test_target_rejects_invalid_shape_and_entrypoint(tmp_path) -> None:
    invalid = tmp_path / "invalid.yml"
    invalid.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a YAML mapping"):
        load_target(invalid)

    target_path = write_target(tmp_path, "missing.py:agent")
    with pytest.raises(ValueError, match="does not exist"):
        create_adapter(load_target(target_path), target_path)

    bad_adapter = tmp_path / "bad-adapter.yml"
    bad_adapter.write_text(
        'version: "1"\ntarget:\n  name: bad\n  adapter: unknown\n  entrypoint: x.py:x\n',
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_target(bad_adapter)


def test_target_rejects_non_callable_entrypoint(tmp_path) -> None:
    (tmp_path / "agent.py").write_text("agent = 42\n", encoding="utf-8")
    target_path = write_target(tmp_path)
    with pytest.raises(ValueError, match="not callable"):
        create_adapter(load_target(target_path), target_path)
