# 90-second demonstration

**0–12 seconds:** “Agent demos show the happy path. AgentTrustLab tests whether the same agent survives hostile inputs, unsafe tools, bad arguments, memory attacks, loops and budget overruns.”

**12–28 seconds:** Show `scenario-pack/core/07-confirmation.yml`. “The expectation is reviewable YAML: request confirmation before an irreversible action, enforce the trace and cap execution.”

**28–42 seconds:** Run `python -m benchmarks.simulated.run`. “The same 30 cases run twice against vulnerable and hardened fixtures—no API key and no paid inference.”

**42–58 seconds:** Show the 0/60 versus 60/60 summary. “This is not an opaque judge score. Each failure points to the exact tool, argument, policy or budget divergence.”

**58–75 seconds:** Open the evidence cockpit and SARIF/Markdown report. “Developers get pytest-style CI failure; security and audit teams get traceable evidence and remediation.”

**75–90 seconds:** “AgentTrustLab is an independent Apache-2.0 verification layer for plain Python, OpenAI Agents, MCP and the broader ecosystem. Try the core pack and tell us where your agent breaks.”
