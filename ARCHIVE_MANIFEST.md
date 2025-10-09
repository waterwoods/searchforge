# Archive Manifest

**Archive Date:** 2025-10-08 22:30:17

**Total Files Archived:** 4

## Archived Files

Files moved to `_archive/20251009/` with preserved directory structure:

- `services/fiqa_api/demo_calls.py`
- `services/fiqa_api/logs/api_metrics.csv`
- `services/fiqa_api/pipeline_manager.py`
- `services/fiqa_api/reports/fiqa_api_live.csv`

## Retained Files (Minimal Surface)

- `docs/openapi_snapshot.json`
- `launch.sh`
- `logs/metrics_logger.py`
- `scripts/contract_check.py`
- `scripts/freeze_check.sh`
- `scripts/generate_openapi.py`
- `scripts/smoke_load.py`
- `services/fiqa_api/app.py`
- `services/fiqa_api/settings.py`

## Rollback

To restore archived files:

```bash
# Restore all archived files
cp -r _archive/20251009/* .

# Or restore specific file
cp _archive/20251009/services/fiqa_api/<filename> services/fiqa_api/
```
