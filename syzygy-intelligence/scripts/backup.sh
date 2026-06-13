#!/bin/sh
# pg_dump backup script — called by docker-compose.backup.yml cron container.
set -e

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
FILENAME="syzygy-db-${TIMESTAMP}.sql.gz"

pg_dump --no-owner --no-acl | gzip > "${BACKUP_DIR}/${FILENAME}"

# Remove backups older than RETENTION_DAYS
find "${BACKUP_DIR}" -name "syzygy-db-*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

echo "Backup created: ${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"
