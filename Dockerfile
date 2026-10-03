# Demo-only Docker image for Dockploy / any Docker host.
# Runs `demo_server.py` (FastAPI + uvicorn) on port 8766.
#
# We don't use the pyproject.toml groups because they pull in pipecat /
# anthropic / google-generativeai which the demo doesn't actually need.
# We only install what `demo_server.py` and the `agent/` it imports use.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: only what we need at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps in their own layer so the build cache survives code changes.
RUN pip install \
    'fastapi>=0.115' \
    'uvicorn[standard]>=0.30' \
    'pyyaml>=6.0' \
    'openai>=1.50' \
    'deepgram-sdk>=7.0' \
    'cartesia>=4.0' \
    'pydantic>=2.7' \
    'pydantic-settings>=2.4' \
    'structlog>=24.1' \
    'httpx>=0.27' \
    'websockets>=12.0'

# Copy the project. The agent/ and eval/ packages are imported by demo_server.py.
COPY demo_server.py ./
COPY agent/ ./agent/
COPY eval/ ./eval/

# Drop privileges (Dockploy / many hosts expect a non-root user).
RUN useradd --create-home --uid 1000 app \
    && chown -R app:app /app
USER app

EXPOSE 8766

# Healthcheck so Dockploy knows when the container is up.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8766/ > /dev/null || exit 1

CMD ["uvicorn", "demo_server:app", "--host", "0.0.0.0", "--port", "8766"]