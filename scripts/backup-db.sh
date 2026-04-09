#!/bin/bash
# Usage: ./scripts/backup-db.sh [compose-file]
# Creates a timestamped PostgreSQL dump in ./backups/

set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.prod.yml}"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="dating_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: ${BACKUP_DIR}/${FILENAME}"

docker compose -f "$COMPOSE_FILE" exec -T pg \
    pg_dump -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-dating}" \
    | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup complete: ${BACKUP_DIR}/${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"

# Keep only last 30 backups
cd "$BACKUP_DIR"
ls -tp *.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
echo "Cleanup done (keeping last 30 backups)"
