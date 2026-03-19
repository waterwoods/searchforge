# SR-22 / Proof Activation Verification Report

**Sprint**: SR-22 / Proof Activation Verification Sprint  
**Date**: 2026-03-07  
**Duration**: ~25 min closed loop

---

## 1. Activation status

**Recent changes are live in the running system.**

| Check | Result |
|-------|--------|
| Backend restarted | Yes — `USE_LOCAL_QDRANT=1 TRANSLATION_ENABLED=1 python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001` |
| Code path in use | `_apply_broker_demo_answer_fixes` in `query.py` — SR-22 fallback and broker hint logic |
| LT03 / LT04 stronger | **Yes** — both pass with SR-22 content, broker hint, DMV authority note |

**Exact commands run:**
```bash
# Restart backend (with local Qdrant)
USE_LOCAL_QDRANT=1 QDRANT_HOST=localhost QDRANT_PORT=6333 \
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos \
python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001

# Run regression
python3 scripts/broker_regression_all5.py --port 8001 --longtail --out /tmp/broker_regression_results.json --report /tmp/broker_validation_report.md
```

**LT03 / LT04 behavior:**
- **LT03** (什么是 SR-22？谁需要？怎么办理？): Retrieval returns insurance.ca.gov (no DMV SR-22). LLM would refuse. Fallback replaces with full SR-22 answer + broker hint. ✅
- **LT04** (客户需要提供什么保险证明？电子卡可以吗？): When retrieval has DMV sources → LLM answer + broker hint appended. When thin → same fallback. ✅

---

## 2. Corpus status

| Item | Status |
|------|--------|
| DMV financial-responsibility URL in config | ✅ In `configs/broker_demo_urls.txt` and `broker_demo_urls.json` |
| DMV financial-responsibility in current corpus | ❌ Not present — corpus has 15 points; none from `.../financial-responsibility-insurance/` |
| Re-ingest needed | Optional — fallback provides good broker value; corpus would improve retrieval for SR-22 when DMV content exists |

**Current corpus URLs (sample):** dmv.ca.gov/insurance-requirements, dmv.ca.gov/suspended-vehicle-registration, insurance.ca.gov/*, geico.com/*, progressive.com/*.

**Recommendation:** To add DMV SR-22 content to corpus:
```bash
python3 scripts/build_demo_core_collection.py --url-list configs/broker_demo_urls.txt --limit 25
```
This will include the financial-responsibility URL. Not required for current demo — fallback is sufficient.

---

## 3. Re-test results

| Scenario | Before (pre-sprint) | After (this sprint) |
|----------|---------------------|----------------------|
| LT03 | LLM refusal or thin answer | Full fallback: SR-22 definition, DUI/lapse, 3-year, broker hint ✅ |
| LT04 | Variable | Proof + electronic card + broker hint ✅ |
| Q1–Q5 | — | All pass (Q2 $14, Q5 claims, Q4 discounts) ✅ |

**Summary:** 7/7 ok, Q2 $14=OK, Q5 claims=OK, Q4 discounts=OK, LT03 SR-22=OK.

---

## 4. Business usefulness check

| Criterion | Assessment |
|-----------|------------|
| Understandable to broker | ✅ Clear SR-22 definition, who needs it, how to get it |
| Customer-shareable | ✅ General guidance; carrier-dependent details deferred |
| Next-step guidance | ✅ 客户可准备, 经纪人可进一步询问 |
| Separation of guidance | ✅ General (SR-22) + DMV (官网为准) + carrier (各公司政策不同) |
| Reduces broker lookup | ✅ Brokers get structured answer instead of "无法回答" |

**Weak point:** When retrieval lacks DMV SR-22 content, we rely on fallback. Corpus refresh would allow LLM to cite DMV when available. Fallback is sufficient for demo and broker value-validation.

---

## 5. Demo safety / regression check

| Check | Result |
|-------|--------|
| Offline fallback | ✅ Unchanged — demo_fallback.json for Q1–Q3; LT03/LT04 use live backend |
| Q1–Q5 regression | ✅ All pass |
| Broker demo usability | ✅ Mode=demo, top_k=5, collection=auto_insurance_demo_core |
| Unified validation path | ✅ `broker_regression_all5.py --longtail` passes |

---

## 6. Manual-work reduction

| What Andy no longer needs to do manually | What Cursor/OpenClaw can do |
|------------------------------------------|----------------------------|
| Manually verify LT03/LT04 answers | Run `python3 scripts/broker_regression_all5.py --port 8001 --longtail` |
| Restart backend and guess if SR-22 is active | Run `bash scripts/verify_sr22_active.sh` |
| Re-check SR-22 fallback logic | Validation pack in `configs/broker_sr22_validation.json` |

**Reusable assets added/improved:**
- `scripts/verify_sr22_active.sh` — one-command SR-22 activation check
- `broker_regression_all5.py --longtail` — already existed; confirmed working
- `configs/broker_sr22_validation.json` — validation criteria for LT03/LT04

---

## 7. Remaining blocker(s)

None. SR-22 / proof improvements are active and useful.

---

## 8. Recommended next sprint

**Target:** Optional corpus refresh to include DMV financial-responsibility page.

**Why:** Fallback works; adding the URL to corpus would allow LLM to cite DMV when retrieval surfaces it, improving answer authority. Low risk, small ingest.

**Command:**
```bash
python3 scripts/build_demo_core_collection.py --url-list configs/broker_demo_urls.txt --limit 25
```
