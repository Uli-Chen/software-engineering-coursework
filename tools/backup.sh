#!/usr/bin/env bash
set -euo pipefail
SECD_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECD_BACKUP_DIR="$SECD_ROOT/backups"
mkdir -p "$SECD_BACKUP_DIR"
cd "$SECD_ROOT/02-源代码"
SECD_BACKUP_FILE="$SECD_BACKUP_DIR/course-$(date +%Y%m%d-%H%M%S).sql"
docker compose exec -T db pg_dump -U course -d course --clean --if-exists --no-owner --no-privileges > "$SECD_BACKUP_FILE"
printf 'Database backup saved: %s\n' "$SECD_BACKUP_FILE"
