# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and README for hatchling
COPY pyproject.toml README.md ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python .

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home reading-agent

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY config.yaml ./

# Create data directories
RUN mkdir -p /app/data /app/logs && \
    chown -R reading-agent:reading-agent /app

# Switch to non-root user
USER reading-agent

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import src.main; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "src.main"]
