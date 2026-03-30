#!/usr/bin/env bash
# Apply Stage 1 service-record DDL to Postgres.
# Requires: psql, SERVICE_RECORD_DATABASE_URL or DATABASE_URL
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL="${SERVICE_RECORD_DATABASE_URL:-${DATABASE_URL:-}}"
if [[ -z "$URL" ]]; then
  echo "Set SERVICE_RECORD_DATABASE_URL or DATABASE_URL" >&2
  exit 1
fi
SQL="$ROOT/services/fiqa_api/db/schema/stage1_service_record.sql"
exec psql "$URL" -v ON_ERROR_STOP=1 -f "$SQL"
