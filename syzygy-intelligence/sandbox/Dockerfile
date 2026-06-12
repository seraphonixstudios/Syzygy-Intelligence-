FROM python:3.11-slim

WORKDIR /sandbox

# Install build dependencies and runtime essentials in single layer with cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early for security
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

# Copy policy file
COPY --chown=sandbox:sandbox sandbox_policy.json /sandbox/sandbox_policy.json

# Switch to non-root user
USER sandbox

# Labels for metadata
LABEL org.opencontainers.image.description="Syzygy Sandbox Environment" \
      org.opencontainers.image.vendor="syzygy"

CMD ["sleep", "infinity"]
