# Operator Ignore List — Unified Intake (Paid Pilot)

**Purpose:** Reduce cognitive overload. If you are running a **paid broker pilot** or answering **2am pages**, treat this as permission to ignore the rest of the repo.

**Runtime truth:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)  
**Do-this path:** [`OPERATOR_CHEAT_SHEET.md`](./OPERATOR_CHEAT_SHEET.md)

---

## SAFE TO IGNORE (paid pilot / production)

| Item | Why safe |
|------|----------|
| `GET /ready` | Legacy **full-stack RAG** gate — needs Qdrant+embedding. Use `/readyz` + `intake_path_ready` |
| `/readyz` with `ok:false` when `intake_path_ready:true` | Vectors down; **triage still runs** on Postgres + keys |
| Qdrant red in dashboard | Optional wedge for notice/knowledge — **not** intake triage |
| `docs/sprints/*` (unless linked from CURRENT_PRODUCT_SHAPE) | Historical execution notes |
| `docs/archive/platform/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md` | Future exploration — not deploy truth |
| `docs/archive/platform/*BLUEPRINT*.md` | Architecture speculation — archived |
| `docs/archive/sprint_reports/` | 71 historical sprint reports — not daily reading |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint — not daily ops |
| Sidebar routes: RAG Lab, Agent Studio, Graph Lab, tuner | Hidden when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| `http://localhost:5173/demo` | RAG Q&A wedge — **not** the intake workbench |
| ETF / `/api/query` smoke examples in old scripts | Lab path — deploy_paid_pilot prints intake manifest curl instead |
| Embedding warming on `/demo` only | Workbench intake does not need live `/api/query` |
| `platform_inline_route_leak_count` in logs | Auditor metric — 0 expected in product_only |

---

## NOT FOR PAID PILOT (forbidden or misleading)

| Item | Class |
|------|-------|
| `DEMO_MODE=1` with `ENV=prod` | Forbidden — fakes readiness |
| `platform_full` on public broker URL | Lab API surface exposed |
| JSON case files as authority when PG URL set | Forbidden — use Postgres |
| `deploy_rag_demo.sh` as operator entry | Deprecated wrapper |
| `deploy_cloud_run_core.sh` direct | Impl only — use `deploy_paid_pilot.sh` |
| `ALLOW_ALL_CORS=1` on prod | Permissive demo CORS |
| Anonymous intake/support (missing API keys) | Perimeter failure |
| `UNIFIED_INTAKE_PG_DUAL_WRITE=1` | Two write paths — pick Postgres |

---

## LAB ONLY (explicit opt-in)

| Item | When |
|------|------|
| `platform_full` (no `UNIFIED_INTAKE_PRODUCT_ONLY`) | Local SearchForge/RAG experiments |
| `docker compose up rag-api` on port 8000 | Legacy container path |
| `POST /api/query` | RAG retrieval lab |
| `USE_LOCAL_QDRANT=1` + seed scripts | Vector wedge / demo page |
| `docs/sprints/` platform closure specs | Engineering archaeology |
| V6 OCR / tuner / black_swan routes | Not mounted in product_only |
| `scripts/dev_local.sh` | SearchForge local dev branding |

---

## HISTORICAL (archive mindset)

| Item | Note |
|------|------|
| SearchForge naming in README Quick Start | Repo heritage — broker product is Unified Intake |
| [`docs/archive/README_LEGACY_SEARCHFORGE_LAB.md`](../archive/README_LEGACY_SEARCHFORGE_LAB.md) | Old 1,500-line README — GPU, AutoTuner, Metrics Hub |
| `deploy_cloud_run.sh` | Legacy SearchForge deploy name |
| Sprint reports under `docs/archive/` | Point-in-time |
| FUTURE_SAAS / LONG_HORIZON archived docs | Investor framing |
| Old broker regression scripts hitting `/api/query` | Pre–Unified Intake emphasis |

---

## Quick mental model

```
Paid pilot = Unified Intake SaaS
  → UNIFIED_INTAKE_PRODUCT_ONLY=1
  → Postgres cases (SERVICE_RECORD_DATABASE_URL)
  → /health/live + /readyz (intake_path_ready)
  → deploy_paid_pilot.sh

Lab = optional
  → platform_full, Qdrant, /api/query, /demo page
```

---

## Related

- [`DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md) — which script to run
- [`SUPPORT_TRUTH_MAP.md`](./SUPPORT_TRUTH_MAP.md) — manifest keys
- [`docs/DEPRECATED_PATHS.md`](../DEPRECATED_PATHS.md) — removed flags
