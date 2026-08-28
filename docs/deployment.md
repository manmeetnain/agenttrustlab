# Self-hosting

AgentTrustLab is designed to remain useful without a managed service.

## Container

```bash
docker compose up --build
```

The dashboard binds to `127.0.0.1:8787` and stores immutable reports in a named volume. The container runs as an unprivileged user with a read-only root filesystem and no-new-privileges enabled.

For team access, place AgentTrustLab behind an authenticated TLS reverse proxy and set a strong ingestion token:

```bash
export AGENTTRUST_API_TOKEN='replace-with-a-random-secret'
docker compose up --build -d
```

Send the token as `Authorization: Bearer …` when posting reports. Read APIs intentionally remain available to users who can reach the service; network access must therefore be restricted when reports contain sensitive prompts or tool output.

## Evidence signing

Generate a signing identity once and keep the private key outside the repository:

```bash
agenttrust keygen
agenttrust run suite.py --attacks --signing-key agenttrust-private.pem
agenttrust verify agenttrust-report.json agenttrust-manifest.json
```

Ed25519 manifests embed the public verification key. Verification does not require an AgentTrustLab account or private signing material.

