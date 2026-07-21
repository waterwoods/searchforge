# P35.2 — Founder QA Console PAT

**Status:** Founder manual QA script (not production acceptance until PAT passes)  
**Surface:** `/internal/founder-qa` (internal Workbench; QA Tools builds only)  
**Backend BFF:** `/api/internal/founder-qa/*`  
**Harness (unchanged CLI):** `bash scripts/reset_p35_mp_qa.sh …`

## Preconditions

- Backend flags (all required for full PAT):
  - `ENABLE_P35_MP_QA_HARNESS=1`
  - `UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1`
  - `P20_SLICE1_REQUEST_MORE=1` (Request More / VIN preset)
- UI: Vite DEV or `VITE_ENABLE_QA_TOOLS=1`
- Mini Program session available (DevTools). Copy once:
  `wx.getStorageSync('mp_customer_session_id')` → must be exact `wx_*`
- Concise quick start: `docs/product/p35_founder_qa_console_quickstart.md`

---

## PAT steps

| # | Action | Expected UI | Expected server state | Failure signal |
|---|--------|-------------|----------------------|----------------|
| 1 | Open `/internal/founder-qa` (or Workbench → QA Tools → Open Founder QA Console) | Console loads with 5 sections | Status endpoint 200 | Blank page / 404 / route missing in product-only build without QA tools |
| 2 | Confirm environment banner | Shows **QA环境 · Founder QA 已启用** (or local + enabled) | `enabled=true`, not production forced-disabled | Red production disabled banner while you expected QA |
| 3 | Select exact Mini Program identity (paste `wx_*`, optional label) | Masked session + label shown; mutation buttons enable | Preference stored for actor+environment | Buttons stay disabled; `exact_wx_session_id_required` |
| 4 | View Current QA State | Compact metrics; no invented fields | Matches inspect/binding truth | Metrics contradict Mini Program / binding |
| 5 | Apply **Fresh Customer** → type `FRESH` → confirm | Success result; Active claim=No | Binding cleared; harness cases soft-archived for that identity only | Success toast with active case still Yes |
| 6 | Relaunch Mini Program (清缓存 optional) | — | Client clears stale resume | Still shows continue without server active case |
| 7 | Confirm empty Service Home | Primary **我要报案** | `has_active_case=false` | Active claim card still dominant |
| 8 | Apply **Active Claim** → type `ACTIVE` | Success; Case ID shown; Resume bound=Yes | Exactly one binding + harness claim | Duplicate bindings / no case id |
| 9 | Relaunch Mini Program | — | Resume issues for bound case | `case_not_found` / empty home |
| 10 | Continue same case | Service Home **继续处理当前报案** → same matter | One Active Case | Second claim created |
| 11 | Apply **Request More** → type `REQUEST_MORE` | VIN request-more in state/result | Open VIN item on case | Active without VIN request |
| 12 | Relaunch → complete VIN path | Task Home / missing item shows VIN | One Truth with Broker | Customer cannot open VIN item |
| 13 | Open Broker Case | Workbench broker tab opens that case | Same case id / request visible | Wrong case or empty detail |
| 14 | View Recent QA Audit Events | Recent fresh/active/request_more rows | Audit list scoped in-memory | Empty after successful mutations |
| 15 | Refresh page / revisit console | Same identity still selected (same API process) | Preference retained in process memory | Identity wiped unexpectedly mid-session |
| 16 | Change / Forget identity | Change updates status; Forget disables presets | Preference updated/cleared | Stale identity still mutates |
| 17 | Attempt access without intake key when key is configured | 401 / unauthorized message | Mutation refused | Anonymous mutation succeeds |
| 18 | Confirm production mutation rejected | Production banner; preset 403 | No binding change | Mutation succeeds in prod without gates |
| 19 | CLI fallback still works | — | `bash scripts/reset_p35_mp_qa.sh status` OK | CLI broken after console deploy |

---

## Timing gate

After initial identity selection, Fresh → Active → Request More (with confirmations) should complete in **under 30 seconds** of Founder interaction time (excluding Mini Program relaunch).

## Pass rule

Do **not** claim production readiness until this PAT is executed and recorded. CLI remains the fallback.
