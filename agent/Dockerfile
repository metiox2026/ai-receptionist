FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for asyncpg + pipecat audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install .[agent]

# Copy the agent code
COPY agent ./agent

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8765/healthz || exit 1

CMD ["python", "-m", "agent.main"]