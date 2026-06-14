# Database Migration Guide

## Overview
These migrations add user ownership tracking and performance indexes to enforce data isolation and improve query performance.

## Pre-Migration Checklist

- [ ] Backup production database
- [ ] Test migrations on staging database first
- [ ] Schedule during low-traffic window
- [ ] Have rollback plan ready
- [ ] Notify users of potential brief downtime

## Migration Steps

### Step 1: Add user_id to agents table

```sql
-- Add column (nullable for existing agents)
ALTER TABLE agents ADD COLUMN user_id UUID;

-- Add foreign key constraint
ALTER TABLE agents ADD CONSTRAINT agents_user_id_fkey 
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Create index for efficient lookups
CREATE INDEX idx_agent_user ON agents(user_id);

-- Backfill user_id for existing agents
-- Associate agents with first superuser or default user
UPDATE agents SET user_id = (SELECT id FROM users WHERE is_superuser = true LIMIT 1)
WHERE user_id IS NULL;

-- Make column NOT NULL after backfill
ALTER TABLE agents ALTER COLUMN user_id SET NOT NULL;
```

### Step 2: Add user_id to sessions table

```sql
-- Add column (nullable initially)
ALTER TABLE sessions ADD COLUMN user_id UUID;

-- Add foreign key constraint
ALTER TABLE sessions ADD CONSTRAINT sessions_user_id_fkey 
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Create index
CREATE INDEX idx_session_user ON sessions(user_id);

-- Backfill: associate sessions with their agent's owner
UPDATE sessions SET user_id = a.user_id
FROM agents a
WHERE sessions.agent_id = a.id AND sessions.user_id IS NULL;

-- Make column NOT NULL after backfill
ALTER TABLE sessions ALTER COLUMN user_id SET NOT NULL;
```

### Step 3: Update foreign key cascading

```sql
-- Update consensus_rounds to cascade on session delete
ALTER TABLE consensus_rounds DROP CONSTRAINT consensus_rounds_session_id_fkey;
ALTER TABLE consensus_rounds ADD CONSTRAINT consensus_rounds_session_id_fkey 
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;

-- Update memories agent FK to cascade
ALTER TABLE memories DROP CONSTRAINT memories_agent_id_fkey;
ALTER TABLE memories ADD CONSTRAINT memories_agent_id_fkey 
  FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE;

-- Update memories session FK to cascade
ALTER TABLE memories DROP CONSTRAINT memories_session_id_fkey;
ALTER TABLE memories ADD CONSTRAINT memories_session_id_fkey 
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;
```

### Step 4: Update task_results indexes and constraints

```sql
-- Change agent FK to SET NULL (preserve task result even if agent deleted)
ALTER TABLE task_results DROP CONSTRAINT task_results_agent_id_fkey;
ALTER TABLE task_results ADD CONSTRAINT task_results_agent_id_fkey 
  FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL;

-- Add cascade on session delete
ALTER TABLE task_results DROP CONSTRAINT task_results_session_id_fkey;
ALTER TABLE task_results ADD CONSTRAINT task_results_session_id_fkey 
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;

-- Add indexes for common queries
CREATE INDEX idx_task_session ON task_results(session_id);
CREATE INDEX idx_task_id ON task_results(task_id);
CREATE INDEX idx_task_status ON task_results(status);
CREATE INDEX idx_task_created ON task_results(created_at);
CREATE INDEX idx_task_session_status ON task_results(session_id, status);
```

### Step 5: Add missing memory index

```sql
-- Index for expiry-based cleanup queries
CREATE INDEX idx_memory_expires ON memories(expires_at);
```

### Step 6: Improve audit logging indexes

```sql
-- Compound index for filtering by event type + time range
CREATE INDEX idx_audit_event_created ON audit_logs(event_type, created_at);
```

## Verification

After migrations complete, verify integrity:

```sql
-- Check all agents have user_id
SELECT COUNT(*) as agents_without_user FROM agents WHERE user_id IS NULL;
-- Expected: 0

-- Check all sessions have user_id
SELECT COUNT(*) as sessions_without_user FROM sessions WHERE user_id IS NULL;
-- Expected: 0

-- Verify foreign key constraints
SELECT constraint_name, table_name, column_name 
FROM information_schema.key_column_usage 
WHERE table_name IN ('agents', 'sessions', 'task_results', 'memories')
ORDER BY table_name;

-- Check indexes created
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('agents', 'sessions', 'task_results', 'memories', 'audit_logs')
ORDER BY tablename, indexname;
```

## Rollback Plan (if needed)

```sql
-- Remove new indexes
DROP INDEX IF EXISTS idx_agent_user;
DROP INDEX IF EXISTS idx_session_user;
DROP INDEX IF EXISTS idx_task_session;
DROP INDEX IF EXISTS idx_task_id;
DROP INDEX IF EXISTS idx_task_status;
DROP INDEX IF EXISTS idx_task_created;
DROP INDEX IF EXISTS idx_task_session_status;
DROP INDEX IF EXISTS idx_memory_expires;
DROP INDEX IF EXISTS idx_audit_event_created;

-- Restore old FK constraints
ALTER TABLE consensus_rounds DROP CONSTRAINT consensus_rounds_session_id_fkey;
ALTER TABLE consensus_rounds ADD CONSTRAINT consensus_rounds_session_id_fkey 
  FOREIGN KEY (session_id) REFERENCES sessions(id);

-- Remove user_id columns (data loss - only for emergency rollback)
ALTER TABLE agents DROP COLUMN user_id;
ALTER TABLE sessions DROP COLUMN user_id;
```

## Monitoring After Migration

1. **Monitor query performance:**
   ```sql
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   WHERE query LIKE '%agents%' OR query LIKE '%sessions%'
   ORDER BY mean_time DESC;
   ```

2. **Check index usage:**
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan 
   FROM pg_stat_user_indexes 
   WHERE tablename IN ('agents', 'sessions', 'task_results')
   ORDER BY idx_scan DESC;
   ```

3. **Monitor disk space:**
   ```sql
   SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
   ```

## Timeline

- **Pre-migration:** 15 minutes (backup, staging test)
- **Migration execution:** 5-15 minutes (depends on data volume)
- **Verification:** 5 minutes
- **Total downtime (with app stop):** 15-25 minutes
- **Zero-downtime option:** Use ALTER TABLE ... CONCURRENTLY for indexes (requires PostgreSQL 11+)

## Zero-Downtime Alternative (PostgreSQL 11+)

```sql
-- Create indexes without blocking writes
CREATE INDEX CONCURRENTLY idx_agent_user ON agents(user_id);
CREATE INDEX CONCURRENTLY idx_session_user ON sessions(user_id);
-- ... repeat for other indexes

-- Then proceed with FK updates (shorter blocking window)
```

