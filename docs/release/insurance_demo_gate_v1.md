# Insurance Demo Gate v1 — Release Checklist

**Created**: 2026-03-06  
**Purpose**: Exact checks required before showing the demo to a broker

---

## Gate: Live Demo Ready

**Do NOT show the demo to a broker until all checks pass.**

---

## 1. Demo Runnable

| Check | Command / Action | Pass Criteria |
|-------|------------------|---------------|
| 1.1 | `bash scripts/run_demo_local.sh` | Script exits 0; prints "Demo ready" and Demo URL |
| 1.2 | Open `http://localhost:5173/demo` | Page loads; no white screen |
| 1.3 | Status bar shows "Live" or "Offline" | Badge visible; not stuck on "..." |

---

## 2. Validation Pass/Fail Logic

| Check | Command / Action | Pass Criteria |
|-------|------------------|---------------|
| 2.1 | `bash scripts/demo_quick_validate.sh` | Exit code 0 |
| 2.2 | Read `results/demo_quick_validate/<timestamp>/REPORT.md` | "Overall: PASS" |
| 2.3 | All 3 questions pass: results>=3, gov_domain, insurer_domain | Per-question ✅ |

**If FAIL**: Run `bash scripts/run_demo_ingest_oneclick.sh` if collection is thin; re-run validate.

---

## 3. Collection Readiness

| Check | Command / Action | Pass Criteria |
|-------|------------------|---------------|
| 3.1 | `python3 scripts/check_qdrant_env.py` | Exit 0; QDRANT_URL set |
| 3.2 | Query Qdrant for `auto_insurance_demo_core` count | ≥20 points |
| 3.3 | `bash scripts/run_demo_ingest_oneclick.sh` (if needed) | Ingest completes; no errors |

---

## 4. Fallback Readiness

| Check | Command / Action | Pass Criteria |
|-------|------------------|---------------|
| 4.1 | `ui/src/assets/demo_fallback.json` exists | File exists |
| 4.2 | `demo_fallback.json` has `items` array | `items.length >= 3` OR `DEFAULT_FALLBACK_ITEMS` in DemoPage |
| 4.3 | Stop backend; click 3 sample questions | Offline mode loads answers; no error |

**Refresh fallback**: `python3 scripts/snapshot_demo_answers.py` (backend must be running).

---

## 5. Env Readiness

| Check | File / Var | Pass Criteria |
|-------|------------|---------------|
| 5.1 | `.env` or `.env.cloudrun` | Exists; loaded by run_demo_local.sh |
| 5.2 | `QDRANT_URL` | Set; valid URL |
| 5.3 | `QDRANT_API_KEY` | Set (required for Qdrant Cloud) |
| 5.4 | `TRANSLATION_ENABLED=1` | In run_demo_local.sh or .env (run_demo_local.sh sets it) |
| 5.5 | `TRANSLATION_PROVIDER=argos` | In run_demo_local.sh or .env |

**Note**: `run_demo_local.sh` sets `TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos` inline; no .env change needed for local.

---

## 6. Deploy Readiness (For Cloud Run)

| Check | Command / Action | Pass Criteria |
|-------|------------------|---------------|
| 6.1 | `cp configs/demo.env.example .env.cloudrun` | .env.cloudrun exists |
| 6.2 | Edit .env.cloudrun: QDRANT_URL, QDRANT_API_KEY | Filled |
| 6.3 | `bash scripts/deploy_rag_demo.sh` | Deploy succeeds |
| 6.4 | `curl -sf $SERVICE_URL/healthz` | 200 OK |
| 6.5 | `curl -X POST $SERVICE_URL/api/query -d '{"question":"加州最低保险","mode":"demo"}'` | Returns sources |

---

## 7. Sample Question Readiness

| Check | Location | Pass Criteria |
|-------|----------|---------------|
| 7.1 | `ui/src/pages/DemoPage.tsx` — SAMPLE_QUESTIONS | ≥3 questions |
| 7.2 | `scripts/demo_quick_validate.py` — questions list | Matches SAMPLE_QUESTIONS (first 3) |
| 7.3 | `scripts/snapshot_demo_answers.py` — QUESTIONS | Matches SAMPLE_QUESTIONS (first 3) |
| 7.4 | Recommended: add Q4 (SR-22), Q5 (续保/折扣) | Optional for v1; 3 is minimum |

---

## 8. Broker-Specific UI Readiness

| Check | Location | Pass Criteria |
|-------|----------|---------------|
| 8.1 | Header | "加州汽车保险智能助手" or broker name (e.g., "陈奎专属") |
| 8.2 | Subtitle | Data sources note visible |
| 8.3 | "复制给客户（可直接发微信）" button | Present; copies bullets+steps+sources |
| 8.4 | Status bar | Live/Offline, Backend, Translation, Citations |
| 8.5 | Scenario buttons | Expandable; click sends question |

---

## Quick Pre-Demo Command Sequence

```bash
cd /home/andy/searchforge

# Night before
bash scripts/demo_prepare_tomorrow.sh

# Day of demo
bash scripts/run_demo_local.sh
# In another terminal:
bash scripts/demo_quick_validate.sh
# Must see: Overall: PASS
```

---

*End of release gate*
