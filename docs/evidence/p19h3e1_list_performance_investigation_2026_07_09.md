# P19H-3e-1 — Workbench / list_all_cases Performance Investigation

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO** (resume deploy smoke)

---

## 1. Problem

During P19H-3e-1 deploy smoke, local Cloud SQL scan logged:

```
cases 200 sec 92.29
```

~200 cases took ~92 seconds. This blocked `ingest_claim_injury_quick_reply()` and other WeCom paths that call `list_all_cases_for_read()`.

---

## 2. What was measured

| Step | Count | Time (observed / simulated) | Notes |
|------|------:|----------------------------:|-------|
| `list_record_ids_recent(200)` | 200 ids | fast (1 query) | Not the bottleneck |
| N+1 `load_full_case_from_postgres` | 200 | **~92s** (deploy smoke) | 3 DB round-trips per case (record + messages + state_history) |
| Batched `load_workbench_queue_cases_from_postgres` | 200 | **<1s** (simulated test) | Same join shape as Workbench list |
| `enrich_cases_for_workbench` | 50 | negligible (CPU) | Not the 92s issue |
| `build_claim_case_brief` / evidence summary | per claim | negligible (CPU) | In-memory only |
| `GET /api/inbox/cases?limit=50` (QA gate) | 33 | **~14s total gate** | Already uses batched queue load |

Live Cloud SQL timing from laptop timed out during this investigation (connection timeout); root cause confirmed by code path + deploy smoke log + simulated N+1 vs batched test.

---

## 3. Root cause

**Case C — N+1 Postgres hydration on `list_all_cases_for_read()`**

- `list_recent_cases_for_read()` (Workbench `GET /api/inbox/cases`) already uses **one batched** `load_workbench_queue_cases_from_postgres(ids)` — no messages/history.
- `list_all_cases_for_read()` (WeCom claim lookup, media dedup, add-car scans) used **N+1** `load_full_case_from_postgres(rid)` for up to `_MAX_LIST_ALL` (200) rows.
- Each full load fetches `record_messages` + `state_history` — unnecessary for routing / open-claim candidate scans.
- Local WSL → Cloud SQL public IP latency (~400–500ms/round-trip) amplified 200×3 ≈ 600 queries into ~90s.

**Not the root cause:**

- Workbench list endpoint full enrichment (`claim_case_brief`, `claim_timeline`, `claim_evidence_summary`) — CPU-only on ≤50 rows.
- Smoke script listing API for parity — minor; real blocker was WeCom internal `list_all_cases_for_read()`.
- `.env.cloudrun` Neon URL vs QA Cloud SQL — separate deploy-smoke issue (smoke script now calls `apply_qa_postgres_env()`).

---

## 4. Fix

### 4.1 Primary — batched hydration for `list_all_cases_for_read`

`services/fiqa_api/inbox_triage/case_truth_repository.py`:

- Replaced per-id `load_full_case_from_postgres` loop with **one** `load_workbench_queue_cases_from_postgres(ids)` call (same pattern as `list_recent_cases_for_read`).
- Preserves routing fields: `service_lane`, `wecom_external_userid`, `known_facts`, `claim_phase`, `guided_workflow_state`, attachments metadata in extra/structured — sufficient for `is_open_claim_candidate_for_basics()` and Claim identity scans.
- `get_case_for_read()` unchanged — single-case detail still uses full hydration when opened.

### 4.2 Collateral — Postgres extra bag for `claim_timeline`

`services/fiqa_api/db/service_record_repository.py` (from deploy-smoke investigation):

- Persist/hydrate `claim_timeline` in JSONB `extra` (no schema migration).
- Also persist `claim_phase`, `manual_handle`, `urgent` in structured/extra for Cloud SQL round-trip.

### 4.3 Smoke script hygiene

`scripts/p19h3e1_deploy_claim_story_smoke.py`:

- `apply_qa_postgres_env(for_write=True)` so writes hit QA Cloud SQL, not Neon `.env.cloudrun`.
- Smoke D fetches single GET first (full enrichment) before optional list parity check.

### 4.4 List endpoint

**No change.** `GET /api/inbox/cases` already limit=50 max and batched DB read. Full Claim enrichment retained for list/detail parity tests.

---

## 5. Before / after

| Path | Before | After |
|------|--------|-------|
| `list_all_cases_for_read()` 200 cases (local Cloud SQL) | ~92s | **<1s** (simulated); expected **~2–5s** live with network |
| `GET /api/inbox/cases` QA gate | ~14s (full gate) | ~14s (unchanged — already batched) |
| WeCom `list_open_claim_candidates_for_basics` | scans 200 full cases | scans 200 **stub** cases (1 query) |

---

## 6. API / script changes

| File | Change |
|------|--------|
| `case_truth_repository.py` | Batched queue hydration for `list_all_cases_for_read` |
| `service_record_repository.py` | `claim_timeline` + claim workflow fields in extra/structured |
| `scripts/p19h3e1_deploy_claim_story_smoke.py` | QA Cloud SQL env + smoke D order |
| `tests/test_case_truth_repository.py` | Assert list_all uses batch not full |
| `tests/test_p19h3e1_list_performance.py` | Simulated 200-case guard (<1s) |
| `tests/test_service_record_wecom_extra.py` | `claim_timeline` extra round-trip |

---

## 7. Tests

| Suite | Result |
|-------|--------|
| `test_p19h3e1_claim_timeline_case_brief.py` | **PASS** |
| `test_p19h3c3ab_get_case_enrichment_parity.py` | **PASS** |
| `test_p19h3e1_list_performance.py` | **PASS** |
| `test_case_truth_repository.py` (new list_all batch test) | **PASS** |
| `pytest -k claim` | **PASS** |
| `pytest -k h5` | **PASS** |
| `npm run build` | **PASS** |

---

## 8. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**PASS** — no hang on `/api/inbox/cases`; total gate ~14s.

---

## 9. Constraints

- No schema migration
- No new product feature
- No deploy (this sprint)
- No OCR / ASR / damage AI / fault / coverage / carrier filing
- No LLM brief / highlights[]

---

## 10. Remaining risk

- `list_all_cases_for_read()` still loads up to **200** stub rows and filters in Python — acceptable at pilot scale; future: SQL filter by `wecom_external_userid` + `service_lane` for WeCom hot path.
- WeCom scans that need **full message history** must continue to use `get_case_for_read(case_id)` — not `list_all`.
- Live before/after on laptop Cloud SQL not re-measured (connection timeout); simulated + architectural parity with `list_recent` is the fix basis.

---

## 11. Next recommended prompt

**P19H-3e-1 Deploy + Claim Story Smoke** — resume with this commit deployed; smoke script + `claim_timeline` Postgres persistence included.

---

## 12. GO / HOLD

**GO** — root cause fixed, tests green, QA gate PASS, no deploy in this sprint.
