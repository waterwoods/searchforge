# P19G-3.2 — Phase 2 Field Validation Guardrail Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Phase 2 phone/date validation — local only  
**Verdict:** **LOCAL PASS** · **HOLD deploy**

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
| No deploy (this loop) | ✅ |

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
| Commit | **GO** |
| Deploy | **HOLD** — separate deploy loop |
| Andy re-test | **HOLD** — after deploy |

---

*P19G-3.2 local implementation complete. Next: deploy + Andy voice-input retest.*
