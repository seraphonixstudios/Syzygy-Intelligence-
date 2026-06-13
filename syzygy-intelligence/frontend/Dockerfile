# ─── Base Stage ───────────────────────────────────────────────
# Lightweight Alpine-based Node runtime
FROM node:20.13-alpine AS base

# Configure npm for efficiency
ENV NPM_CONFIG_LOGLEVEL=error \
    NPM_CONFIG_AUDIT=false

# Build-time environment variables for public Next.js config
ARG NEXT_PUBLIC_SYZYGY_API_URL
ARG NEXT_PUBLIC_SYZYGY_WS_URL

# ─── Dependencies Stage ───────────────────────────────────────
# Install dependencies separately for layer caching
FROM base AS deps

WORKDIR /app

# Copy package files first (leverages Docker layer caching)
COPY --chown=node:node package.json package-lock.json ./

# Install dependencies with cache mount and reproducible lockfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci --frozen-lockfile --prefer-offline --no-audit && \
    npm cache clean --force

# ─── Builder Stage ────────────────────────────────────────────
# Compile Next.js application
FROM base AS builder

ARG NEXT_PUBLIC_SYZYGY_API_URL
ARG NEXT_PUBLIC_SYZYGY_WS_URL

ENV NEXT_PUBLIC_SYZYGY_API_URL=${NEXT_PUBLIC_SYZYGY_API_URL} \
    NEXT_PUBLIC_SYZYGY_WS_URL=${NEXT_PUBLIC_SYZYGY_WS_URL} \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps --chown=node:node /app/node_modules ./node_modules

# Copy source code (excludes from .dockerignore)
COPY --chown=node:node . .

# Build Next.js with output optimization
RUN npm run build

# ─── Runtime Stage ────────────────────────────────────────────
# Minimal production image with built application
FROM base AS runner

ENV NODE_ENV=production \
    PORT=3000 \
    NODE_OPTIONS="--max-old-space-size=256 --no-warnings" \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built application from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

# Switch to non-root user
USER nextjs

EXPOSE 3000

# Health check with HTTP probing
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Metadata labels
LABEL org.opencontainers.image.title="Syzygy Intelligence Frontend" \
      org.opencontainers.image.description="Next.js-based React frontend" \
      org.opencontainers.image.vendor="syzygy" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/syzygy/syzygy-intelligence"

# Start Next.js server
CMD ["node", "server.js"]
