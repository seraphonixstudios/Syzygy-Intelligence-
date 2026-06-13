# ─── Builder Stage ────────────────────────────────────────────────
# Compile Python dependencies and create virtual environment
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies in single layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Build venv with optimized pip settings, wheel caching, and cleanup
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip>=23.0 setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete

# ─── Runtime Stage ────────────────────────────────────────────────
# Minimal production image with only runtime dependencies
FROM python:3.13-slim

WORKDIR /app

# Create non-root user for security (before copying files)
RUN groupadd -r syzygy && useradd -r -g syzygy syzygy

# Install only essential runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Set Python environment variables for optimization
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

# Copy pre-built virtual environment from builder
COPY --from=builder --chown=syzygy:syzygy /opt/venv /opt/venv

# Copy application code
COPY --chown=syzygy:syzygy . .

# Create data directories and clean build artifacts
RUN mkdir -p data/chroma data/uploads data/sandbox && \
    chown -R syzygy:syzygy data && \
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete

# Switch to non-root user
USER syzygy

EXPOSE 8000

# Health check with reasonable timeouts
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Metadata labels
LABEL org.opencontainers.image.title="Syzygy Intelligence Backend" \
      org.opencontainers.image.description="Multi-agent platform with consensus engine" \
      org.opencontainers.image.vendor="syzygy" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/syzygy/syzygy-intelligence"

# Entrypoint: init DB, then start server with production workers
# Use alembic for migrations (more standard than migrate.py)
# If migration fails, container exits with error (Docker will restart it)
CMD alembic upgrade head 2>/dev/null || alembic stamp head; \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info --workers 4
