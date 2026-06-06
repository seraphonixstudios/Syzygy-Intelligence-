# ─── Base Stage ───────────────────────────────────────────
FROM node:20-alpine AS base

# Set npm to prefer offline mode & reduce install logs
ENV NPM_CONFIG_LOGLEVEL=warn

# ─── Dependencies Stage ───────────────────────────────────────
FROM base AS deps

WORKDIR /app

# Copy only package files for better layer caching
COPY package*.json ./

# Use npm ci for reproducible installs
RUN npm ci --frozen-lockfile

# ─── Builder Stage ────────────────────────────────────────────
FROM base AS builder

WORKDIR /app

# Copy dependencies from previous stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
COPY . .

# Build Next.js app with optimizations
RUN npm run build

# ─── Runtime Stage ────────────────────────────────────────────
FROM base AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built application and static files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
