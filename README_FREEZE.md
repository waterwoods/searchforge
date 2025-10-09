# FIQA API Freeze v1.0.0

**Freeze Date:** October 9, 2025  
**Version:** v1.0.0-fiqa  
**Tag:** `v1.0.0-fiqa-freeze`

---

## 🎯 Overview

This freeze establishes a **minimal, stable, testable API surface** for the FIQA API. All non-essential files have been archived to `_archive/20251009/` with preservation of directory structure for rollback capability.

---

## 📦 Retained Files (Minimal Surface)

Only **4 core files** are retained for the production API:

1. **`launch.sh`** - Service launcher with health checks (port 8080, 5s interval)
2. **`services/fiqa_api/app.py`** - FastAPI application (self-contained, includes inlined PipelineManager)
3. **`services/fiqa_api/settings.py`** - Configuration with environment variable support
4. **`logs/metrics_logger.py`** - CSV-based metrics logging

### Infrastructure Files (Testing & Validation)

- `scripts/contract_check.py` - API contract validation
- `scripts/freeze_check.sh` - Orchestration script for freeze validation
- `scripts/smoke_load.py` - Load testing script
- `docs/openapi_snapshot.json` - Frozen OpenAPI schema

---

## 🔧 Environment Variables (Stable Switches)

All configuration is controlled via environment variables with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_MAX` | `3` | Max requests per window per IP |
| `RATE_LIMIT_WINDOW_SEC` | `1.0` | Rate limit window in seconds |
| `API_VERSION` | `v1.0.0-fiqa` | API version identifier |
| `DISABLE_AUTOTUNER` | `1` | AutoTuner disabled by default |

### Usage

Override defaults by exporting before running:

```bash
export RATE_LIMIT_MAX=5
export API_VERSION="v1.0.1-fiqa"
./launch.sh
```

Or inline:

```bash
RATE_LIMIT_MAX=10 ./launch.sh
```

---

## 🚀 Quick Start

### 1. Start the Service

```bash
./launch.sh
```

Service will start on `http://localhost:8080` with automatic health checks every 5 seconds.

### 2. Validate the Freeze

Run comprehensive validation:

```bash
./scripts/freeze_check.sh
```

This will:
- Start the service (if not running)
- Run contract validation (`contract_check.py`)
- Run smoke load test (`smoke_load.py`)
- Print summary with pass/fail status

Expected output:

```
[CONTRACT] ✓ PASS - All endpoint contracts validated
[SANITY]   ✓ PASS - Load test passed (success_rate≥90%, P95<300ms)
```

---

## 📋 API Contract

### Endpoints

1. **`GET /health`** → `200 {"status": "ok"}`
2. **`POST /search`** → `200 {"answers": [...], "latency_ms": float, "cache_hit": bool}`
   - Validation errors: `422 {code, msg, hint, ts}`
   - Rate limit exceeded: `429 {code, msg, hint, ts}`
3. **`GET /metrics`** → `200 {count, avg_p95_ms, avg_recall, ..., window_sec, uptime_sec, version}`

### Unified Error Format

All `4xx` responses follow this structure:

```json
{
  "code": 422,
  "msg": "Validation error message",
  "hint": "Suggested fix or constraint info",
  "ts": "2025-10-09T12:34:56.789Z"
}
```

### OpenAPI Schema

Frozen schema available at: `docs/openapi_snapshot.json`

---

## ✅ Validation & Testing

### Contract Check

Validates all endpoint contracts:

```bash
python3 scripts/contract_check.py
```

Tests:
- ✓ `/health` returns 200
- ✓ `/search` with empty query returns 422 with `{code,msg,hint,ts}`
- ✓ `/search` rate limiting returns 429 with `{code,msg,hint,ts}`
- ✓ `/metrics` contains `{count,window_sec,uptime_sec,version}`

### Smoke Load Test

Runs 60 concurrent requests with rate limit respect:

```bash
python3 scripts/smoke_load.py
```

Success criteria:
- **Success Rate:** ≥90%
- **P95 Latency:** <300ms
- **QPS:** Measured and reported

### Full Freeze Check

Comprehensive orchestration:

```bash
./scripts/freeze_check.sh
```

Runs both contract and load tests with colored output and summary.

---

## 🔄 Rollback Instructions

### To Previous State (Pre-Freeze)

```bash
# Checkout the freeze tag
git checkout v1.0.0-fiqa-freeze

# Restore archived files if needed
cp -r _archive/20251009/* .
```

### To Restore Specific File

```bash
# Example: restore demo_calls.py
cp _archive/20251009/services/fiqa_api/demo_calls.py services/fiqa_api/
```

### To Complete Undo

```bash
# Reset to commit before freeze
git reset --hard HEAD~1

# Restore all archived files
cp -r _archive/20251009/* .
```

---

## 📊 Passed Checks (Freeze Validation)

### Pre-Freeze Validation ✓

- [x] Archive structure created: `_archive/20251009/`
- [x] Archive manifest generated: `ARCHIVE_MANIFEST.md`
- [x] Retained files: 4 core + infrastructure
- [x] OpenAPI snapshot: `docs/openapi_snapshot.json`
- [x] Environment variables: All defaults set in `launch.sh`

### Contract Checks ✓

- [x] `/health` → 200
- [x] `/search` empty query → 422 with unified error format
- [x] `/search` rate limit → 429 with unified error format
- [x] `/metrics` → contains required fields (count, window_sec, uptime_sec, version)

### Load Test ✓

- [x] Success rate: ≥90%
- [x] P95 latency: <300ms
- [x] Rate limiting respected: 3 req/sec per IP

### Git Operations ✓

- [x] Commit: `freeze(fiqa-api): v1.0.0 minimal surface sealed`
- [x] Tag: `v1.0.0-fiqa-freeze`

---

## 📁 Archive Details

**Archived Files Count:** 4 files

Files moved to `_archive/20251009/`:
- `services/fiqa_api/demo_calls.py`
- `services/fiqa_api/pipeline_manager.py` (inlined into app.py)
- `services/fiqa_api/logs/api_metrics.csv`
- `services/fiqa_api/reports/fiqa_api_live.csv`

See `ARCHIVE_MANIFEST.md` for complete details.

---

## 🎓 Best Practices

### Before Making Changes

1. Always validate current state: `./scripts/freeze_check.sh`
2. Check environment variables: `env | grep -E "(RATE_LIMIT|API_VERSION|DISABLE)"`
3. Review OpenAPI schema: `cat docs/openapi_snapshot.json`

### After Making Changes

1. Run contract check: `python3 scripts/contract_check.py`
2. Run load test: `python3 scripts/smoke_load.py`
3. Update OpenAPI snapshot if needed: `python3 scripts/generate_openapi.py`

### Deployment

1. Validate freeze checks pass
2. Set environment variables for production
3. Use `launch.sh` with appropriate overrides
4. Monitor `/metrics` endpoint for health

---

## 📞 Support

For issues or questions:
- Review archived files: `_archive/20251009/`
- Check OpenAPI schema: `docs/openapi_snapshot.json`
- Validate contracts: `python3 scripts/contract_check.py`
- Rollback if needed: `git checkout v1.0.0-fiqa-freeze`

---

**Status:** ✅ FREEZE COMPLETE  
**Validated:** October 9, 2025  
**Next Review:** As needed for production deployment

