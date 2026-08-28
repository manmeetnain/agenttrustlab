# Contributing

Open an issue before substantial changes. Keep the core framework-neutral, add behavior through typed boundaries, and include tests for success, failure, timeout, and hostile input paths.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,docs]'
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/pytest --cov
.venv/bin/mkdocs build --strict
```

By contributing, you agree that your work is licensed under Apache-2.0.

