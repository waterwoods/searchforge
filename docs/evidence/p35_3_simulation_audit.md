# P35.3 — Founder QA Console E2E Simulation Audit

**Date:** 2026-07-20  
**Verdict:** Safe to begin Founder PAT (simulation PASS). Founder PAT itself is **not** claimed passed.

## Simulation method

Closest available end-to-end path in this environment:

1. **Live BFF HTTP simulation** of the exact UI routes (`/api/internal/founder-qa/*`) via `scripts/p35_3_founder_qa_console_e2e_sim.py`
2. **Vite route reachability** from WSL (`GET /internal/founder-qa` → 200)
3. **Isolated TestClient** for harness-disabled / production rejection
4. **Static checks:** Mini Program grep, console client source leak check, CLI `reset_p35_mp_qa.sh status`
5. **UI state HTML captures** from normalized status JSON (not a substitute for Founder visual PAT)

**Browser GUI blocked in this environment:**

| Tool | Result |
|------|--------|
| Cursor IDE browser → `localhost:5173` | `ERR_CONNECTION_REFUSED` / unreachable from host |
| Windows Chrome headless → WSL/`localhost` | `ERR_CONNECTION_RESET` / `ERR_CONNECTION_TIMED_OUT` |
| Playwright Chromium in WSL | Missing system libs (`libnspr4`); `sudo` unavailable |

Evidence of host-browser failure: `docs/evidence/p35_3_browser_host_unreachable.png`

## Required runtime flags (shared QA / local)

```text
ENABLE_P35_MP_QA_HARNESS=1
UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1
P20_SLICE1_REQUEST_MORE=1          # required for Request More preset
UNIFIED_INTAKE_INTAKE_API_KEY=...  # UI + BFF perimeter
# Cloud SQL / case store required for Active + Request More
```

## Results

Machine-readable: `docs/evidence/p35_3_e2e_results.json` — **30 PASS / 0 FAIL** (final run).

UI state captures:

- `p35_3_state_initial.html`
- `p35_3_state_fresh.html`
- `p35_3_state_active.html`
- `p35_3_state_request_more.html`

## Bugs fixed during audit

1. **Status panel missed open VIN after Request More** — inspect only looked at `p20_slice1`/`slice1`; live cases store `p20_slice1_request_summary` / projections. Fixed in `p35_mp_qa_harness._open_request_summary` / `_case_task_summary`.
2. **Partial failure copy** — added explicit mapper for `request_more_failed:slice1_not_enabled`.

## PAT blockers assessed

| Issue | Blocks Founder PAT? |
|-------|---------------------|
| No real Founder/Admin IAM | **No** for local/shared-QA (intake key + flags) |
| Identity preference in-memory only | **No** if same API process; re-paste after restart |
| Host browser automation unavailable here | **No** — Founder uses real browser on their machine |
| Missing `P20_SLICE1_REQUEST_MORE` | **Yes** for Request More step — must be on QA |

## Safe to begin Founder PAT?

**YES** — after confirming QA runtime has the flags above.

Do not mark Founder PAT complete until `docs/product/p35_2_founder_qa_console_pat.md` is executed manually.
