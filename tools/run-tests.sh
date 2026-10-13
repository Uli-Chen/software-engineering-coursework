#!/usr/bin/env bash
set -euo pipefail
SECD_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SECD_ROOT/02-源代码"
docker compose up -d db
if ! docker compose exec -T db psql -U course -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='course_test'" | grep -q 1; then
  docker compose exec -T db createdb -U course course_test
fi
docker compose run --rm --no-deps -v "$PWD/backend:/app" api python -m pytest -v --junitxml=/app/test-results.xml > "$SECD_ROOT/03-测试证据/pytest.txt" 2>&1
cp backend/test-results.xml "$SECD_ROOT/03-测试证据/pytest.xml"
cat "$SECD_ROOT/03-测试证据/pytest.txt"
