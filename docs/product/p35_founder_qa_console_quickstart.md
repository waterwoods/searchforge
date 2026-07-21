# P35 — Founder QA Console Quick Start

**Purpose:** Run Fresh / Active / Request More without terminal commands.  
**Route:** `/internal/founder-qa`  
**Not:** customer Mini Program · production acceptance (until PAT recorded)

---

## Required QA runtime flags

Set on the **API** (local or shared QA). All three are required for full PAT:

| Flag | Value | Why |
|------|-------|-----|
| `ENABLE_P35_MP_QA_HARNESS` | `1` | Enables Founder QA reset harness |
| `UNIFIED_INTAKE_QA_FIXTURE_SURFACE` | `1` | QA fixture surface / environment label |
| `P20_SLICE1_REQUEST_MORE` | `1` | Request More (VIN) preset — without this, Active may succeed but VIN step fails |

Also required in practice:

- Case store reachable (Cloud SQL / QA DB) for **Active** and **Request More**
- Intake API key configured when the deployment uses `UNIFIED_INTAKE_INTAKE_API_KEY` (UI must send the same via `VITE_UNIFIED_INTAKE_INTAKE_API_KEY`)
- UI: Vite DEV **or** `VITE_ENABLE_QA_TOOLS=1`

CLI fallback (unchanged):

```bash
bash scripts/reset_p35_mp_qa.sh status
```

---

## Exact startup commands

### Local (demo + console)

```bash
# From repo root — product demo (Cloud SQL when available)
ENABLE_P35_MP_QA_HARNESS=1 \
UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1 \
P20_SLICE1_REQUEST_MORE=1 \
bash scripts/run_demo_local.sh
```

Then open:

```text
http://localhost:5173/internal/founder-qa
```

Or: Workbench → **办公室工作台** → QA Tools → **Open Founder QA Console**.

### Shared QA (Cloud Run / Vercel)

1. Confirm the three API flags above are set on the QA API service.
2. Open the QA Workbench UI with QA Tools enabled.
3. Go to `/internal/founder-qa`.

### Get Mini Program session id (once)

In WeChat DevTools console (same customer session you will test):

```js
wx.getStorageSync('mp_customer_session_id')
```

Must be an exact `wx_…` string. Paste once into **Select QA Identity**. Preference is server-side for this API process (re-paste after API restart).

---

## Founder PAT checklist

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `/internal/founder-qa` | Console loads (banner + identity + state + 3 presets + result) |
| 2 | Read environment banner | **QA环境 · Founder QA 已启用** (or local + enabled) — not production forced-disabled |
| 3 | Select `wx_*` identity | Masked ID shown; preset buttons enabled |
| 4 | Refresh Status | Metrics update; no invented fields |
| 5 | **切换为新客户** → type `FRESH` → confirm | Success; Active claim=No; Resume bound=No; no open request-more |
| 6 | Relaunch Mini Program → Service Home | Primary **我要报案** (empty / first-use) |
| 7 | **生成进行中案件** → type `ACTIVE` → confirm | Success; one Case ID; Resume bound=Yes |
| 8 | Relaunch → Continue | **继续处理当前报案** → same case (One Active Case) |
| 9 | **生成 VIN 补件场景** → type `REQUEST_MORE` → confirm | Success; status shows VIN / 补充车架号; still one active case |
| 10 | Relaunch → Continue → VIN path | Missing-item / Task Home surfaces VIN |
| 11 | Open Broker Case | Same case; VIN request visible (One Truth) |
| 12 | View Recent QA Audit Events | fresh / active / request_more rows present |
| 13 | Refresh browser | Same identity still selected (same API process) |
| 14 | Forget identity | Preset buttons disabled |
| 15 | CLI fallback | `bash scripts/reset_p35_mp_qa.sh status` still works |

**Timing:** After identity selection, Fresh → Active → Request More (UI only) should be &lt; 30s excluding Mini Program relaunch.

**Pass rule:** Do not claim production readiness until this checklist is executed and recorded.

---

## Common failures and fixes

| Message / symptom | Fix |
|-------------------|-----|
| Banner: Founder QA 未启用 / harness disabled | Set `ENABLE_P35_MP_QA_HARNESS=1` and `UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1` on API; restart |
| 生产环境 · QA Reset 已强制禁用 | Wrong environment — use QA/local, not production |
| 未授权 / `intake_api_unauthorized` | Align `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` with API `UNIFIED_INTAKE_INTAKE_API_KEY` |
| Preset buttons disabled | Select exact `wx_*` identity first |
| `exact_wx_session_id_required` / wildcard forbidden | Paste full `wx_…` only — no fuzzy match |
| `confirm_fresh_required` / `ACTIVE` / `REQUEST_MORE` | Typed phrase must match exactly |
| `request_more_failed:slice1_not_enabled` / 部分失败…Slice1 | Set `P20_SLICE1_REQUEST_MORE=1` on API; retry (case may already exist — use Fresh then Request More) |
| `p20_case_intake_requires_service_record_database_url` | Point API at QA case DB (not empty JSON-only for Active) |
| Identity gone after refresh | API process restarted — re-paste session id (in-memory preference) |
| Route 404 / “Console 未对当前构建开放” | Use DEV UI or `VITE_ENABLE_QA_TOOLS=1`; not product-only without QA tools |
| MP still shows Continue after Fresh | Relaunch / 清缓存; confirm console Active claim=No before blaming client |
| CLI needed | `bash scripts/reset_p35_mp_qa.sh fresh\|active\|request-more --session-id wx_… --confirm …` |

---

## Related

- Full step table: `docs/product/p35_2_founder_qa_console_pat.md`
- Simulation evidence: `docs/evidence/p35_3_simulation_audit.md`
