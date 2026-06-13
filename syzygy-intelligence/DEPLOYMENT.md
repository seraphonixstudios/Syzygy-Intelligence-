# Syzygy Intelligence — Deployment & Security Guide

## Overview

This document covers deployment best practices and explains the fixes applied to the codebase.

## Bug Fixes Summary

### 1. Configuration Validation (Critical)

**Issue**: Missing `neo4j_password` reference in config validation caused `AttributeError` in production.

**Fix**: 
- Explicit field definitions with proper types
- Separated validation logic into dedicated methods
- Production-only validation doesn't fail on missing optional fields
- Uses `field_validator` from pydantic for type safety

**File**: `backend/app/config.py`

### 2. Rate Limiter Circuit Breaker (High Priority)

**Issue**: Redis rate limiter never retried after failure; permanent `_failed` flag.

**Fix**:
- Implemented circuit breaker pattern (CLOSED → OPEN → HALF_OPEN)
- Automatic recovery attempts every 30 seconds
- Graceful fallback to in-memory rate limiting
- Detailed logging for troubleshooting

**File**: `backend/app/middleware/rate_limiter.py`

### 3. Database Transaction Handling (High Priority)

**Issue**: Sessions committed on exit even if exceptions occurred; incorrect error recovery.

**Fix**:
- Moved commit to `else` block (only on success)
- Explicit rollback on exceptions
- Separate `get_db_context()` for background tasks
- Proper resource cleanup in `finally` block

**File**: `backend/app/db/session.py`

### 4. Migration Failure Handling (High Priority)

**Issue**: Migrations could fail silently; app would start without database.

**Fix**:
- Created dedicated `migrate.py` script with proper error handling
- Explicit exit code on failure (causes container restart)
- Structured logging for debugging

**Files**: `backend/migrate.py`, `backend/Dockerfile`

### 5. Python Version Availability (High Priority)

**Issue**: Dockerfile specified `python:3.14-slim` which doesn't exist yet.

**Fix**:
- Downgraded to `python:3.13-slim` (latest stable)
- Added explicit version pins for reproducibility

**Files**: `backend/Dockerfile`, `frontend/Dockerfile`

### 6. Health Checks (Medium Priority)

**Issue**: Frontend health check depended on backend but didn't wait properly.

**Fix**:
- Added proper `service_healthy` conditions
- Increased start periods and timeouts
- Proper retry logic in health checks

**File**: `docker-compose.yml`

### 7. Frontend CSS Classes (Low Priority)

**Issue**: `h-dvh` (dynamic viewport height) not defined in Tailwind config.

**Fix**:
- Added explicit height utilities to tailwind config
- Includes `dvh` (modern browsers) and `screen-safe` (fallback)

**File**: `frontend/tailwind.config.ts`

### 8. Security Hardening

**Added**:
- Non-root user in all Dockerfiles
- Read-only filesystem where possible
- Explicit file permissions
- Security labels in images
- Network segmentation (bridge network)
- Health checks with reasonable timeouts

## Deployment Checklist

### Pre-Production

- [ ] Generate secure `SYZYGY_SECRET_KEY`: `openssl rand -hex 32`
- [ ] Generate secure `SYZYGY_DB_PASSWORD` (20+ characters)
- [ ] Generate secure `SYZYGY_NEO4J_PASSWORD`
- [ ] Set `SYZYGY_ENV=production` in `.env`
- [ ] Configure `SYZYGY_CORS_ORIGINS` to your domain(s)
- [ ] Configure `SYZYGY_OAUTH_REDIRECT_URL` for production domain
- [ ] Set up email provider (SendGrid or AWS SES)
- [ ] Configure Stripe keys if using payments
- [ ] Run `docker-compose config` to validate

### Database Migration

```bash
# The migration runs automatically on container startup
# To verify: docker-compose logs backend | grep -i "database initialized"

# Manual migration (if needed):
docker-compose exec backend python migrate.py
```

### Health Checks

```bash
# Monitor startup
docker-compose logs -f backend frontend postgres redis

# Check service health
docker-compose ps

# Test API health
curl http://localhost:8000/health
curl http://localhost:3000/
```

### Scaling Considerations

**Rate Limiting**:
- Redis is essential for distributed rate limiting
- If Redis is unavailable, in-memory fallback allows ~50 requests before degradation
- Adjust `SYZYGY_RATE_LIMIT_PER_SECOND` based on your load

**Database**:
- PostgreSQL connection pool: 10 connections (default)
- Max overflow: 20 connections
- Adjust in `backend/app/db/session.py` for high-traffic scenarios

**Ollama Models**:
- Pull models during startup: `docker-compose exec ollama ollama pull qwen3:8b-gpu`
- Cache models in volume to avoid re-downloading: `ollama_data:/root/.ollama`

## Monitoring & Logging

### Structured Logging

All logs are JSON-formatted in production for easy parsing:

```bash
# View formatted logs
docker-compose logs backend | jq '.log_level'

# Filter errors
docker-compose logs backend | jq 'select(.log_level == "ERROR")'
```

### Metrics Endpoint

```bash
# Prometheus metrics available at
curl http://localhost:8000/metrics
```

### Circuit Breaker Status

Logs will indicate circuit breaker state:

```
"Circuit breaker: attempting to reconnect to Redis"  # Half-open state
"Redis connection established"  # Recovered (closed state)
"Redis rate limiter unavailable"  # Open state (using fallback)
```

## Production Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with production values
nano .env
```

Key variables for production:

```env
SYZYGY_ENV=production
SYZYGY_SECRET_KEY=<random-32-byte-hex>
SYZYGY_DB_PASSWORD=<strong-password>
SYZYGY_NEO4J_PASSWORD=<strong-password>
SYZYGY_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
SYZYGY_EMAIL_PROVIDER=sendgrid
SYZYGY_SENDGRID_API_KEY=<api-key>
```

## Troubleshooting

### Container Won't Start

```bash
docker-compose logs backend

# Check for migration errors
# Check for missing environment variables
# Verify database connectivity
```

### Rate Limiting Not Working

```bash
docker-compose logs backend | grep -i "rate limiter"

# If Redis is down, fallback is active (allow list is less strict)
# Check Redis: docker-compose ps redis
```

### Database Connection Issues

```bash
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U syzygy -d syzygy -c "SELECT 1"
```

### Frontend Not Loading

```bash
docker-compose logs frontend

# Verify API URL is correct
docker-compose exec frontend env | grep NEXT_PUBLIC
```

## Rollback Procedure

If issues occur after deployment:

```bash
# Stop current deployment
docker-compose down

# Restore previous version
git checkout <previous-commit>

# Restart with previous code
docker-compose up -d
```

## Security Considerations

1. **Secrets**: Never commit `.env` to Git. Use CI/CD secrets management.
2. **Network**: Use firewall rules to restrict access to databases (no public port exposure).
3. **HTTPS**: Deploy behind reverse proxy (Nginx/Caddy) with TLS.
4. **API Keys**: Rotate regularly. Use short-lived tokens where possible.
5. **Database**: Regular backups. Use encrypted connections.

## Performance Optimization

### Caching

- Redis caches rate limit state and session data
- Adjust TTLs based on usage patterns
- Monitor Redis memory: `docker-compose exec redis redis-cli INFO memory`

### Connection Pooling

- PostgreSQL: 10 connections per process
- Increase if handling >100 concurrent requests
- Monitor: `docker-compose exec postgres psql -U syzygy -d syzygy -c "SELECT count(*) FROM pg_stat_activity"`

### Log Level

- Production: `INFO` (logs important events)
- Debug: `DEBUG` (verbose, impacts performance)

## Support & Reporting Issues

When reporting bugs:

1. Collect logs: `docker-compose logs > debug.log`
2. Run health checks
3. Check environment configuration
4. Include error messages and timestamps
