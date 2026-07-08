# P19H-2.1 — Claim Interrupt / Lane Switch Policy

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Status:** **DEPLOYED** (`fiqa-api-00168-644`) · **PHONE SMOKE PENDING**

---

## 1. Goal

Fix routing so Claim / accident / injury intents are **not swallowed** by Add Vehicle secondary-topic deferral when a user has an active Add Vehicle case.

---

## 2. User-found issue (phone retest)

**Context:** P19H-2' deployed (`fiqa-api-00167-mnk`, `GIT_SHA=5b993a7`). Claim start basics flow works with no active case.

**Repro:** User in active Add Vehicle workflow sends:

- `开始理赔`
- `我要理赔`
- `我发生车祸了`

**Actual reply:**

> Got it — I noted your other question. Let's finish your current request first; your broker will follow up on the other topic.  
> 收到，我已记录您的其他问题。我们先完成当前请求，陈总会人工跟进其他事项。

**Expected:** Claim lane-switch prompt or Claim safety/start — not generic secondary-topic deferral.

---

## 3. Root cause

`ingest_claim_basics_message()` in `claim_basics.py` had an early branch:

```python
if find_open_add_car_case_by_external_userid(ext) and intent_result.intent == "claim_intake":
    return secondary_topic_deferred
```

This ran **before** Claim guided workflow could start, so high-confidence Claim intents during active Add Vehicle were treated as a secondary topic instead of a high-priority interrupt.

---

## 4. New routing priority (while Add Vehicle active)

Documented in `slice.py` and implemented in `claim_basics.py`:

1. **Injury / safety markers** → immediate safety/manual reply (no deferral, no C1)
2. **High-confidence Claim start** → lane-switch prompt OR confirmed Claim start (`开始理赔`)
3. **Claim question intent** → safe claim question reply (Add Vehicle–aware copy)
4. **Lane-switch follow-up** → continue Add Vehicle / contact broker
5. **Existing Add Vehicle** handling (progress, Phase 2, draft merge)
6. **Secondary-topic deferral** fallback (non-Claim topics only)

---

## 5. Claim lane switch copy

When active Add Vehicle + Claim start (non-injury, non-confirm):

```
【理赔资料收集】

您当前还有一个加车资料流程正在进行。

如果这是新的事故 / 理赔事项，我们可以先开始理赔资料收集。

请回复：
1. 开始理赔
2. 继续加车
3. 联系陈总

我们只会先帮您整理资料，陈总会人工确认。
这不代表已经正式报案。
```

No Claim case created until user confirms (`开始理赔` / `1` / `start claim`).

---

## 6. Injury / manual behavior

If injury markers present (`有人受伤`, `hospital`, `ambulance`, etc.) during active Add Vehicle:

- Immediate `【安全提醒】` reply
- Claim case may be created with manual-handle flags
- No secondary-topic deferral
- No C1
- No “already filed” language

---

## 7. Confirm switch behavior

| User reply | Behavior |
|------------|----------|
| `开始理赔` / `1` / `start claim` | Starts P19H-2' Claim guided flow (creates Claim case + start/safety reply) |
| `继续加车` / `2` | Resume Add Vehicle (progress card if available, else simple continue copy) |
| `联系陈总` / `3` | Broker contact / manual follow-up ack |

**Limitation:** No persistent lane-switch pending marker in case schema. `开始理赔` works via high-confidence intent on the next turn, not saved confirmation state.

---

## 8. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h21_claim_interrupt_lane_switch.py -q
# 9 passed
```

Regression suites (P19H-2, P19H-1, P19I-2b/c, P19G Phase 2, P19E progress, WeCom slice/reply/active_case): **all passed**.

---

## 9. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
# Revision still fiqa-api-00167-mnk (pre-deploy)
```

---

## 10. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ STOP after commit |
| No schema change | ✅ |
| No OCR | ✅ |
| No H5 Claim photos | ✅ |
| No Workbench Claim drawer | ✅ |
| No callback / Cloud SQL / VPC changes | ✅ |

---

## 11. Known limitations

- No persistent lane-switch pending marker — confirmation is intent-based on the next message.
- Claim case creation requires explicit start phrase (`开始理赔`) after lane-switch prompt; accident phrases alone show the prompt first.
- Full multi-case UI not implemented; Add Vehicle + Claim parallel management remains basic.
- Generic secondary-topic deferral still applies to non-Claim topics (e.g. renewal question during Add Vehicle).

---

## 12. GO / HOLD (pre-deploy)

| Gate | Verdict |
|------|---------|
| Code + tests + QA gate | **GO** |
| Deploy + phone retest | **HOLD** — deploy next revision, then retest Add Vehicle + Claim interrupt on phone |

---

## 13. Deploy Evidence

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed commit | `326fe3c` (`326fe3c3417de0a4890e3a756d128a92e02d7a35f`) |
| Backend revision | `fiqa-api-00168-644` |
| Previous revision | `fiqa-api-00167-mnk` |
| Backend URL | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| GIT_SHA (image) | `326fe3c34` |
| Deploy time (UTC) | 2026-07-08T05:35:00Z |
| Deploy script | `bash scripts/deploy_paid_pilot.sh` |
| `/health/live` | **200** `{"ok":true}` |
| `/readyz` | **200** `intake_core_readiness=true` |
| Pre-deploy QA gate | **PASS** |
| Post-deploy QA gate | **PASS** |
| Log check | **CLEAN** — no `claim_basics` / `claim_extractors` / `claim_state` / lane-switch / WeCom import errors on revision `fiqa-api-00168-644`; expected optional Qdrant/embedding warmup warnings only |
| Frontend deployed | **No** |
| Schema changed | **No** |
| Cloud config / callback changed | **No** |
| OCR | **No** |
| H5 Claim photos | **No** |
| Workbench Claim drawer | **No** |
| WeCom callback | https://fiqa-api-g7zatxrycq-uw.a.run.app/api/wecom/kf/callback (unchanged) |
| Cloud SQL | `caseiq` @ `10.73.0.3` (private VPC, unchanged) |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` (unchanged) |

**Status:** Deploy **GO** · Phone smoke **PENDING**

---

## 14. Andy Phone Retest Checklist

Test from WeCom customer account against production callback (revision `fiqa-api-00168-644`).

**Prerequisite:** Have an **active Add Vehicle case** open before running Smokes A–F and H.

### Smoke A — Active Add Vehicle + Claim start

**Input:** `我要理赔`

**Expected:**
- Does **NOT** reply “先完成当前请求” / “Let's finish your current request first”
- Shows Claim lane-switch prompt 【理赔资料收集】
- Mentions current Add Vehicle flow (加车资料流程正在进行)
- Offers: `1. 开始理赔` · `2. 继续加车` · `3. 联系陈总`
- Says not formal claim filing (不代表已经正式报案)

### Smoke B — Confirm Claim start

After Smoke A, **input:** `开始理赔`

**Expected:**
- Starts Claim guided flow
- Shows 【理赔资料收集】 safety/start reply
- Asks for accident time / location / description
- No generic menu
- No “already filed” language

### Smoke C — Accident phrase during Add Vehicle

**Input:** `我发生车祸了`

**Expected:**
- Claim lane-switch prompt
- **Not** secondary-topic deferral

### Smoke D — Injury during Add Vehicle

**Input:** `有人受伤了，我要理赔`

**Expected:**
- Safety/manual reply 【安全提醒】
- Prioritize safety / contact emergency service / Chen
- Does **NOT** say finish current request
- No C1
- No liability / coverage promise

### Smoke E — Claim question during Add Vehicle

**Input:** `出事故了怎么办`

**Expected:**
- Safe claim Q&A (Add Vehicle–aware copy)
- No liability judgment
- No coverage promise
- Offers start claim / continue Add Vehicle
- **Not** generic secondary-topic deferral

### Smoke F — Continue Add Vehicle

**Input:** `继续加车`

**Expected:**
- Add Vehicle continue/progress reply
- **Not** Claim

### Smoke G — Add Vehicle regression

**Input:** `重新加车`

**Expected:**
- Add Vehicle flow still works normally

### Smoke H — Generic non-Claim secondary topic

**Input:** `我还想问一下续保`

**Expected:**
- Existing secondary-topic deferral still works (“先完成当前请求…”)

---

## 15. GO / HOLD (post-deploy)

| Gate | Verdict |
|------|---------|
| Deploy | **GO** — `fiqa-api-00168-644` live |
| Phone smoke | **PENDING** — Andy to run checklist §14 |

**STOP** — await phone retest.
