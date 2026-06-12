# Observability Setup Guide

This guide covers the complete observability stack for Syzygy Intelligence.

## Components

### 1. **Prometheus** (Metrics Collection)
- Scrapes `/metrics` endpoint on the API
- Stores time-series data for 30 days
- Dashboard: http://localhost:9090

### 2. **Grafana** (Visualization)
- Pre-configured Prometheus datasource
- Syzygy overview dashboard with:
  - HTTP request rates and latency
  - Login attempts (success/failure)
  - Message charging metrics
  - Database and cache performance
- Dashboard: http://localhost:3001 (admin/admin by default)

### 3. **Alertmanager** (Alerting)
- Processes alerts from Prometheus rules
- Routes critical/warning/info alerts
- Supports Slack, email, PagerDuty integrations
- Dashboard: http://localhost:9093

### 4. **Jaeger** (Distributed Tracing - Optional)
- Traces request flows across services
- Production-only (set `SYZYGY_ENV=production`)
- Dashboard: http://localhost:16686

## Quick Start

### Launch the monitoring stack:

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Access the dashboards:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **Alertmanager**: http://localhost:9093
- **Jaeger** (if enabled): http://localhost:16686

### Enable Jaeger tracing:

Set environment variables for production:
```bash
export SYZYGY_ENV=production
export JAEGER_HOST=localhost
export JAEGER_PORT=6831
```

## Metrics Explained

### Auth Metrics
- `syzygy_auth_login_attempts_total` - Total login attempts by status (success/failed)
- `syzygy_auth_token_refreshes_total` - Token refresh operations
- `syzygy_auth_password_resets_total` - Password reset requests by result
- `syzygy_auth_email_verifications_total` - Email verification attempts
- `syzygy_auth_api_keys_created_total` - API keys created
- `syzygy_auth_api_keys_revoked_total` - API keys revoked

### Usage Metrics
- `syzygy_messages_charged_total` - Messages charged by subscription tier
- `syzygy_usage_limit_exceeded_total` - Users hitting usage limits
- `syzygy_trial_expirations_total` - Trial periods that expired
- `syzygy_premium_upgrades_total` - Upgrades to premium tier

### API Metrics
- `syzygy_http_requests_total` - Total HTTP requests by method, endpoint, status
- `syzygy_http_request_duration_seconds` - Request latency histogram by endpoint

### Database Metrics
- `syzygy_db_query_duration_seconds` - Query latency by operation (select/insert/update/delete)
- `syzygy_db_connection_errors_total` - Connection errors

### Consensus/LLM Metrics
- `syzygy_consensus_rounds_completed_total` - Completed rounds by result
- `syzygy_consensus_round_duration_seconds` - Round execution time histogram
- `syzygy_active_sessions` - Current active sessions
- `syzygy_llm_calls_total` - LLM calls by model and status
- `syzygy_llm_latency_seconds` - LLM response latency by model

### Cache Metrics
- `syzygy_cache_hits_total` - Cache hits by type
- `syzygy_cache_misses_total` - Cache misses by type

## Logging

### Log Files
Structured JSON logs are stored in `backend/data/logs/`:
- `syzygy.log` - General application logs
- `syzygy_error.log` - Error-level logs only
- `syzygy_audit.log` - Audit trail (auth events, usage events)

### Log Context
Request logs include:
- `request_id` - Unique request identifier
- `correlation_id` - Cross-service correlation ID
- `user_id` - Authenticated user ID (if available)
- `method` - HTTP method
- `path` - API endpoint
- `duration_ms` - Request duration in milliseconds

### Audit Logging
Auth and usage events are logged to the audit trail with structured data:
```python
# Example: User login
{
  "event_type": "auth",
  "audit_action": "login",
  "user_email": "user@example.com",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "result": "success",
  "timestamp": "2024-01-01T12:00:00+00:00"
}
```

## Alert Rules

### Critical Alerts
- `HighErrorRate` - API error rate > 5%
- `DatabaseConnectionErrors` - DB connection failures detected

### Warning Alerts
- `HighFailedLoginRate` - Failed logins > 0.1/sec for 5 min
- `HighAPILatency` - p95 latency > 1 second
- `HighUsageLimitExceeded` - Users hitting limits at rate > 0.5/sec
- `SlowDatabaseQueries` - p95 query time > 0.5 seconds
- `ConsensusRoundFailures` - Consensus failure rate > 0.1/sec
- `LLMAPIErrors` - LLM error rate > 0.1/sec

### Info Alerts
- `HighPasswordResetRequests` - Password resets > 1/sec
- `HighTrialExpirations` - Multiple trial expirations/hour
- `LowCacheHitRate` - Cache hit rate < 70%

## Alert Integration

### Slack Integration

1. Create a Slack webhook URL: https://api.slack.com/messaging/webhooks

2. Edit `monitoring/alertmanager.yml` and add your webhook:
```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#critical-alerts'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
```

3. Restart alertmanager:
```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

## Custom Queries

### Find failed login attempts in last hour:
```
rate(syzygy_auth_login_attempts_total{status="failed"}[1h])
```

### High-latency endpoints:
```
histogram_quantile(0.99, rate(syzygy_http_request_duration_seconds_bucket[5m])) > 0.5
```

### Messages charged by tier:
```
increase(syzygy_messages_charged_total[24h]) by (subscription_tier)
```

### Usage limit violations:
```
increase(syzygy_usage_limit_exceeded_total[24h]) by (subscription_tier)
```

## Tracing with Jaeger (Production)

When `SYZYGY_ENV=production`, OpenTelemetry automatically traces:
- FastAPI requests
- SQLAlchemy queries
- Redis operations

View traces at: http://localhost:16686

Search for traces by:
- Service: `syzygy-intelligence`
- Operation: endpoint path (e.g., `/api/auth/login`)
- Tag: `user_id`, `request_id`

## Retention Policies

- **Metrics**: 30 days (Prometheus)
- **Logs**: Rotate at 10MB, keep 5 backups
- **Error logs**: Rotate at 10MB, keep 3 backups
- **Audit logs**: Rotate at 25MB, keep 10 backups

## Troubleshooting

### Metrics not appearing in Prometheus
1. Verify `/metrics` endpoint is accessible: `curl http://localhost:8000/metrics`
2. Check Prometheus scrape targets: http://localhost:9090/targets
3. Review Prometheus logs: `docker logs syzygy-prometheus`

### Alerts not firing
1. Check alert rule syntax: `docker exec syzygy-prometheus promtool check rules /etc/prometheus/alerting_rules.yml`
2. Verify evaluation in Prometheus UI: http://localhost:9090/alerts
3. Check alertmanager status: http://localhost:9093

### High memory usage
- Reduce metric retention: edit `docker-compose.monitoring.yml`, change `--storage.tsdb.retention.time`
- Disable infrequently-used metrics in Prometheus scrape config

## Security

- Change Grafana default password: Set `GRAFANA_PASSWORD` environment variable
- Run alertmanager with authentication if exposed publicly
- Use TLS/mTLS for inter-service communication
- Restrict access to `/metrics` endpoint in production (consider reverse proxy)

## Best Practices

1. **Alert on business metrics**: Focus on user impact (failed logins, exceeded limits) not just system metrics
2. **Set reasonable thresholds**: Use historical data to establish baselines
3. **Preserve context**: Include user_id, request_id in all logs
4. **Correlate signals**: Link errors → latency → database metrics
5. **Alert fatigue**: Use alert aggregation and inhibit rules to reduce noise
6. **Regular review**: Audit alert effectiveness monthly
