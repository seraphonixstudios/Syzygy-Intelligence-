# ─── Builder Stage ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (leverage layer caching)
COPY requirements.txt .

# Build venv with optimized pip settings
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip>=23.0 setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ─── Runtime Stage ────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Create non-root user early for layer caching and security
RUN groupadd -r syzygy && useradd -r -g syzygy syzygy

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Python optimization
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

# Copy pre-built virtual environment from builder (before app code for caching)
COPY --from=builder --chown=syzygy:syzygy /opt/venv /opt/venv

# Copy application code
COPY --chown=syzygy:syzygy . .

# Switch to non-root user
USER syzygy

EXPOSE 8000

# Healthcheck with retries
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
