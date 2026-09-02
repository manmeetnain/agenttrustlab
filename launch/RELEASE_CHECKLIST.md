# v0.1 release checklist

## Verified automatically

- Python 3.11–3.13 test matrix
- Ruff, strict MyPy and coverage gate
- Wheel and source distribution build
- Twine metadata validation
- Clean Python 3.12 wheel installation with dependency resolution
- Bundled 20-case pack extraction and schema validation
- Documentation, CodeQL, dependency graph and container workflows
- Reproducible simulated benchmark and evidence bundle

## Account-bound publication

1. Create or sign in to the PyPI account that will own `agenttrustlab`.
2. Add a pending Trusted Publisher for repository `manmeetnain/agenttrustlab`, workflow `release.yml`, environment `pypi`.
3. Confirm the GitHub `pypi` environment exists and has the desired reviewers.
4. Push tag `v0.1.0`. The workflow builds, publishes to PyPI and creates the GitHub Release.
5. Verify `pip install agenttrustlab` and `agenttrust pack` from the public index.

Do not push the release tag until the Trusted Publisher is configured; otherwise the publish job will fail after a valid build.
