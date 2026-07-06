#!/usr/bin/env bash
# Reset Chen Kui P18 demo cases only (workbench_test + demo_name=chen_kui_p18).
#
# Usage:
#   bash scripts/reset_chen_kui_demo.sh                    # local JSON (dev)
#   bash scripts/reset_chen_kui_demo.sh --qa               # GCP Cloud SQL (QA truth)
#   bash scripts/reset_chen_kui_demo.sh --cloud            # alias for --qa
#   bash scripts/reset_chen_kui_demo.sh --qa --reseed        # reset + QA seed
#   bash scripts/reset_chen_kui_demo.sh --dry-run
#
# Does NOT truncate service_records or touch non-demo data.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

TARGET="local"
DRY_RUN=0
RESEED=0
for arg in "$@"; do
  case "$arg" in
    --qa|--cloud) TARGET="qa" ;;
    --legacy-neon) TARGET="legacy-neon" ;;
    --dry-run) DRY_RUN=1 ;;
    --reseed) RESEED=1 ;;
  esac
done

echo "=========================================="
echo "Chen Kui P18 Demo Reset (target=${TARGET})"
echo "=========================================="

if [[ "$TARGET" == "local" ]]; then
  export UNIFIED_INTAKE_CASES_PATH="${UNIFIED_INTAKE_CASES_PATH:-data/unified_intake_cases.json}"
  unset UNIFIED_INTAKE_DB_PRIMARY_READS UNIFIED_INTAKE_DB_PRIMARY_WRITES
  export UNIFIED_INTAKE_JSON_CASE_WRITES=1
  echo "[INFO] Local JSON mode (dev only — not QA demo path)"
elif [[ "$TARGET" == "legacy-neon" ]]; then
  echo "[WARN] legacy-neon — NOT Cloud Run QA DB; prefer --qa"
else
  echo "[INFO] QA GCP Cloud SQL (same DB as Cloud Run API) — demo-tagged rows only"
fi

DRY_FLAG=()
if [[ "$DRY_RUN" == "1" ]]; then
  DRY_FLAG=(--dry-run)
fi

echo "[1] Removing demo-tagged cases (demo_name=chen_kui_p18, workbench_test only)..."
PYTHONPATH=. python3 -c "
from scripts.seed_chen_kui_demo import remove_existing_demo_cases
import sys
dry = '--dry-run' in sys.argv
if '--legacy-neon' in sys.argv:
    target = 'legacy-neon'
elif '--qa' in sys.argv or '--cloud' in sys.argv:
    target = 'qa'
else:
    target = 'local'
n = len(remove_existing_demo_cases(dry_run=dry, target=target))
print(f'Removed demo cases: {n}')
" "${DRY_FLAG[@]}" $([[ "$TARGET" == "qa" ]] && echo --qa) $([[ "$TARGET" == "legacy-neon" ]] && echo --legacy-neon)

if [[ "$TARGET" == "qa" ]] || [[ "$TARGET" == "legacy-neon" ]]; then
  echo "[2] WeCom queue — status only (no sync_cursor reset)"
  if [[ "$TARGET" == "qa" ]]; then
    PYTHONPATH=. python3 -c "from scripts.demo_db_resolve import apply_qa_postgres_env; apply_qa_postgres_env()" 2>/dev/null || true
  elif [[ -f ".env.cloudrun" ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env.cloudrun
    set +a
  fi
  if [[ -n "${SERVICE_RECORD_DATABASE_URL:-${DATABASE_URL:-}}" ]]; then
    PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status 2>/dev/null | head -8 || echo "[SKIP] queue status unavailable"
  else
    echo "[SKIP] No DATABASE_URL in env"
  fi
else
  echo "[2] WeCom queue — skipped (local JSON dev)"
fi

if [[ "$RESEED" == "1" ]]; then
  echo "[3] Re-seeding demo cases..."
  PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target "$TARGET" "${DRY_FLAG[@]}"
else
  cat <<EOF

To restore demo cases:
  PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target ${TARGET}

One-shot reset + seed:
  bash scripts/reset_chen_kui_demo.sh --qa --reseed

QA Workbench (primary):
  https://ui-smoky-beta.vercel.app/workbench/unified-intake

Runbook:
  docs/CHEN_KUI_DEMO_ENVIRONMENT.md

EOF
fi

echo "Done."
