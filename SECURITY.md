# Security policy

AgentTrustLab is pre-1.0. Security fixes target the latest release and `main`.

Please report vulnerabilities privately using GitHub's **Report a vulnerability** flow. Include affected versions, reproduction steps, impact, and suggested mitigation. Do not include secrets or exploit live systems. Maintainer: Manmeet Nain ([@manmeetnain](https://github.com/manmeetnain)).

The local dashboard is not an identity provider. Bind it to loopback by default. For shared deployments, use an authenticated TLS reverse proxy, set `AGENTTRUST_API_TOKEN`, restrict network access, and treat stored prompts, traces, tool output, reports and private signing keys as sensitive data.
