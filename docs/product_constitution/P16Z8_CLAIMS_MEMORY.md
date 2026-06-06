# P16-Z8 Phase 5 — Claims Retention Archaeology

**Date:** 2026-06-02  
**Sprint:** P16-Z8 Memory Hardening Archaeology  
**Search terms:** `claim_intake`, plate, photos, police report, carrier, adjuster, damage estimate  
**Sources:** `triage.py` L5271–5347, Role D claims battery (CL01–CL10), P16-Z6 claims validation, P16-Z7 claims report

---

## Executive summary

Claims Turn 1 is **pilot-ready** — FNOL templates, category routing, and boolean field extractors work. Turn 2+ retention is **~36% keyword survival** — corrections, plates, dollars, and injury context drop from summary and often from collected.

**No separate claims service.** All in `_extract_claim_fields()` + `_claim_structured_fields()`.

---

## What survives across turns?

| Fact type | Turn 1 | Turn 2+ | In collected | In summary headline | Evidence |
|-----------|--------|---------|--------------|---------------------|----------|
| FNOL / accident reported | ✅ | ✅ | `accident_reported` | ✅ Claim intake | CL01, CL05 |
| Hit-and-run | ✅ | ✅ | `hit_and_run` | ✅ | CL01 |
| Photos mentioned | ✅ | ⚠️ | `photos` | ⚠️ | CL03, CL08 |
| Other driver / plate | ⚠️ | ⚠️ | `other_driver_info` | ❌ headline | CL01, CL03 |
| Police report | ⚠️ | ⚠️ | `police_report` | ❌ until T3 | CL01 |
| Injuries | ⚠️ | ❌ | `injuries` | ❌ | CL06 fail |
| Policy number | ✅ | ✅ | via policy hint | ✅ | CL04 |
| Dollar amounts ($18k) | ❌ | ❌ | **No field** | latest snip only | CL10 |
| Total loss / 全损 | ⚠️ | ❌ | **No field** | lost | CL02 **0%** |
| Adjuster wait | ⚠️ prose | ⚠️ prose | ❌ | ❌ | CL04 |
| Glass-only → full claim | ⚠️ | ❌ | pivot lost | ❌ | CL08 |
| Correction flag | N/A | ✅ | summary tag | ✅ | CL05, CL09 |
| Multi-turn count | ✅ | ✅ | N/A | ✅ all 10 | Built |

---

## What disappears?

| Disappearance | Cases | Mechanism |
|---------------|-------|-----------|
| Total loss context on correction | CL02 | Summary overwrite; no 全损 field |
| Injury / MRI thread | CL06 | → `unclear`; fields cleared |
| Wrong lane (missing_document) | CL03 | DL markers beat claim on T2 |
| Plate correction in headline | CL01 | Latest bubble only for snip |
| Dollar amounts | CL02, CL10 | No `$` extractor in claim fields |
| Rental extension | CL10 | No structured token |
| Hail / roof leak | CL04 | Weak markers |
| Glass-only prior context | CL08 | Full claim pivot |
| Adjuster → waiting_on | CL04, CL05 | Manual only |
| Police # early turns | CL01 | Lands collected T3 only |

---

## Retention map

```
                    TURN 1          TURN 2          TURN 3
                    ──────          ──────          ──────
FNOL routing        ████████████    ████████████    ████████████
Templates/copy      ████████████    ████████░░░░    ██████░░░░░░
accident_reported   ████████████    ████████████    ████████████
photos              ████████████    ████████░░░░    ████████░░░░
plate/other_driver  ██████░░░░░░    ██████░░░░░░    ████████░░░░
police_report       ████░░░░░░░░    ████░░░░░░░░    ████████░░░░
injuries            ████░░░░░░░░    ░░░░░░░░░░░░    ░░░░░░░░░░░░
dollar amounts      ░░░░░░░░░░░░    ░░░░░░░░░░░░    ██░░░░░░░░░░
total loss          ████████░░░░    ░░░░░░░░░░░░    ░░░░░░░░░░░░
summary headline    ████████████    ██████░░░░░░    ████░░░░░░░░
collected merge     ████████░░░░    ████░░░░░░░░    ████░░░░░░░░
correction prepend  N/A             ████████░░░░    ████████░░░░
category stable     ████████████    ██████░░░░░░    ██████░░░░░░

Legend: █ = retained  ░ = lost/weak
```

---

## Existing claim memory code

| Function | Role | Gap |
|----------|------|-----|
| `_is_claim_intake_request()` | Lane detect | Beaten by missing_doc on doc chains |
| `_extract_claim_fields()` | 6 boolean flags | No plate #, $, total_loss |
| `_claim_structured_fields()` | collected/still | Re-extract only; no merge |
| Claim templates | Turn 1 copy | Strong |
| `claim_intake_hit_and_run` template | Plate emphasis | Turn 1 only |
| `_prepend_prior_customer_turn_on_correction` | Z6 | Helps CL05/CL09 not CL02 |
| `_last_customer_turn_blocks_add_car` includes claim | L3015 | Blocks add-car only |

---

## TOP 10 claims retention fixes (reuse-first)

| # | Fix | Effort |
|---|-----|--------|
| 1 | `plate_number` extracted field | 2 hr |
| 2 | `claim_amount` / `damage_estimate` field | 2 hr |
| 3 | `total_loss` boolean | 1 hr |
| 4 | Persisted collected merge on claim append | 4 hr |
| 5 | Claim lane guard (block missing_doc eat) | 2 hr |
| 6 | Prior-turn prepend for claim corrections | 2 hr |
| 7 | Injury markers → `injuries` stable | 2 hr |
| 8 | Adjuster wait → suggest `waiting_on: carrier` | 2 hr |
| 9 | Plate in summary headline | 1 hr |
| 10 | CL01–CL10 regression battery | 0 (exists) |

---

## Phase 5 verdict

**Turn 1: ship it. Turn 2+: tune memory, don't rebuild FNOL.** Extend `_extract_claim_fields()` + generic collected merge. **~1 engineer-day** for commercial claims continuity.
