# P19G-3.2 — Phase 2 Field Validation Guardrail Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Phase 2 phone/date validation — local + deploy  
**Verdict:** **LOCAL PASS** · **DEPLOY PASS** · **QA gate PASS** · **Voice retest PENDING**

---

## Goal

Fix Andy phone smoke regression where voice-input Phase 2 text saved invalid phone (`0311155573` from `20311155573`) and invalid date (`17月12日` from `17月12号`). Block bad values from `known_facts` / `collected_fields` and prompt customer to re-enter.

---

## Problem (Andy voice input)

**Input:**
```
我是要是17月12号提车，Zip code 92705，电话是20311155573
```

**Before fix:**
| Field | Result | Issue |
|-------|--------|-------|
| ZIP | 92705 ✅ | OK |
| Phone | 0311155573 ❌ | Regex matched internal 3-3-4 slice inside 11-digit run |
| Date | 17月12日 ❌ | Month 17 accepted |

**Risk:** Broker sees wrong `known_facts` → misoperation risk.

---

## Fix summary

| Rule | Behavior |
|------|----------|
| Phone 10-digit | Accept; normalize to 10 digits |
| Phone 11-digit starting `1` | Strip country code → 10 digits |
| Phone 11-digit not starting `1` | **Reject**; show raw candidate; do not save |
| Phone bounded match | No internal 3-3-4 match inside longer digit runs |
| Date month | Must be 1–12 |
| Date day | Must be 1–31 |
| Invalid + valid mix | Save valid ZIP; keep invalid fields missing; validation reply |
| S2 | Only when all 3 fields valid |

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/phone_normalization.py` | `normalize_us_phone_10_digits()` strict 10-digit validator |
| `services/fiqa_api/wecom/identity.py` | Bounded phone extraction; date month/day validation; `*_with_validation` helpers |
| `services/fiqa_api/wecom/add_vehicle_phase2.py` | `parse_phase2_text_fields()`; validation retry in ingest |
| `services/fiqa_api/wecom/reply.py` | `build_phase2_validation_reply()` |
| `services/fiqa_api/wecom/add_vehicle_progress.py` | Route invalid Phase 2 signals to handler (not Progress Card) |
| `tests/test_p19g32_phase2_field_validation.py` | **NEW** — 17 tests incl. Andy voice regression |

---

## Validation reply copy

**Invalid phone:**
```
联系电话位数好像不对，我看到：
20311155573

请重新回复 10 位电话号码。
例如：
2031234567
```

**Invalid date:**
```
提车日期好像不对，我看到：
17月12号

请重新回复正确日期。
例如：
7月12号
```

**Partial valid (ZIP saved):** prepends `已收到：✓ 停放 ZIP — 92705` then validation blocks.

---

## Andy voice input — expected after fix

| Field | Saved? | Reply |
|-------|--------|-------|
| ZIP 92705 | ✅ | Shown in 已收到 |
| Phone | ❌ | Validation prompt with `20311155573` |
| Date | ❌ | Validation prompt with `17月12号` |
| S2 | ❌ | Not sent until all valid |

---

## Tests

| Command | Result |
|---------|--------|
| `pytest tests/test_p19g32_phase2_field_validation.py -q` | 17 passed |
| `pytest tests/test_p19e1_*.py tests/test_wecom_*.py tests/test_wecom_identity_b0_extractors.py -q` | 147 passed |

---

## Deploy (2026-07-07)

### Pushed commits

| Commit | Message |
|--------|---------|
| `fea8790` | fix: validate Phase 2 phone and date fields |

Pushed: `git push origin sprint/p16-trust-layer` (`41a6b65..fea8790`)

### Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00165-qfk` |
| **Revision (this deploy)** | **`fiqa-api-00166-vs2`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **GIT_SHA** | **`fea879000`** |
| Deploy time (UTC) | 2026-07-07 ~22:58 UTC |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — unchanged |
| `WECOM_SLICE_SEND_REPLY` | `1` — unchanged |
| `H5_TASK_TOKEN_SECRET` | configured — unchanged |
| WeCom callback / VPC / NAT | unchanged |
| Neon | Not QA truth |

### Frontend deploy

**Not required** — P19G-3.2 is backend validation only; no UI changes.

### Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — revision fiqa-api-00166-vs2, Cloud SQL aligned
```

### Log check (post-deploy)

Revision `fiqa-api-00166-vs2` startup + runtime logs reviewed (~100 lines):

- **No** import/syntax errors
- **No** WeCom reply errors
- **No** Phase 2 validation errors
- **No** Postgres read facade errors
- Expected optional warnings only: embedding warmup deferred, Qdrant/Redis optional, bm25 optional

---

## Andy phone retest checklist

**Backend:** `fiqa-api-00166-vs2` · **GIT_SHA:** `fea8790` · **Frontend:** unchanged (`ui-smoky-beta`)

### Smoke A — invalid voice/text input

**Setup:** If no active Phase 2 case → `重新加车` → complete H5 photos → wait for S1.

**Send:**
```
我是要是17月12号提车，Zip code 92705，电话是20311155573
```

| # | Expected | Result |
|---|----------|--------|
| A1 | ZIP 92705 saved | **PENDING** |
| A2 | Phone `20311155573` NOT saved | **PENDING** |
| A3 | Date `17月12号` NOT saved | **PENDING** |
| A4 | No S2 `【第 2 步完成 ✅】` | **PENDING** |
| A5 | No broker review state | **PENDING** |
| A6 | Reply: 提车日期不对 + 联系电话位数不对 | **PENDING** |
| A7 | Workbench: no `0311155573` or `17月12日` | **PENDING** |

### Smoke B — correction completes Phase 2

**Send:**
```
7月12号，电话2031234567
```

| # | Expected | Result |
|---|----------|--------|
| B1 | Date saved `7月12日` | **PENDING** |
| B2 | Phone saved `2031234567` | **PENDING** |
| B3 | ZIP 92705 retained | **PENDING** |
| B4 | S2 sent | **PENDING** |
| B5 | Broker review state | **PENDING** |

### Smoke C — valid 11-digit leading 1 (optional)

**Setup:** `重新加车` → photos → S1.

**Send:**
```
7月12号提车，ZIP 92705，电话12031234567
```

| # | Expected | Result |
|---|----------|--------|
| C1 | Phone saved as `2031234567` | **PENDING** |
| C2 | S2 if all fields valid | **PENDING** |

### Smoke D — regression

| # | Action | Expected | Result |
|---|--------|----------|--------|
| D1 | `进度` | Progress Card works | **PENDING** |
| D2 | `你好` (active case) | Progress Card, not menu | **PENDING** |
| D3 | `重新加车` | Restart flow works | **PENDING** |

---

## Constraints honored

| Constraint | Status |
|------------|--------|
| No OCR | ✅ |
| No Claim workflow | ✅ |
| No schema migration | ✅ |
| No Cloud config / callback | ✅ |
| No routing priority change | ✅ |
| No H5 token/security change | ✅ |
| No Workbench change | ✅ |
| No frontend deploy | ✅ |

---

## Known limitations

- No February/leap-year day accuracy (month/day range only)
- Relative dates (`明天`, `下周一`) still accepted as before
- ISO `YYYY-MM-DD` accepted without day-of-month calendar check

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local tests | **GO** |
| Push + deploy | **GO** |
| Post-deploy QA gate | **GO** |
| Logs | **GO** (clean) |
| Andy voice retest | **PENDING** — operator run on WeChat |

---

*P19G-3.2 deploy complete. Andy voice retest pending.*
