FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGENTTRUST_DB=/data/agenttrustlab.db

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir '.[server,signing]'

RUN groupadd --system agenttrust \
    && useradd --system --gid agenttrust --home-dir /app agenttrust \
    && mkdir /data \
    && chown agenttrust:agenttrust /data

USER agenttrust
EXPOSE 8787
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=2)"
CMD ["agenttrust", "serve", "--host", "0.0.0.0", "--port", "8787"]

