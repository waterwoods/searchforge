# State parity + record identity spec

## Current record / state mismatch (pre-sprint)

| Surface | Record identity | Lifecycle / state language |
|--------|------------------|----------------------------|
| Customer progress + result | Strong: `add_car_case_record_id_label` + `AddCarCaseStatusStrip` | Uses `LIFECYCLE_STATUS_LABELS` + quote-ready chips |
| Workbench queue | **Weak:** case id not shown on cards; preview text only | **Inconsistent:** only `已移交` / `办公室跟进` binary, not full lifecycle map |
| Workbench open case | Case id not echoed at top of detail | Same binary lifecycle tags in Case 整理 row |

## Target parity model (practical, no new engine states)

Reuse existing API fields only:

- `case_id` — **服务记录编号** (same label family as customer closure).
- `lifecycle_status` — map through one shared vocabulary:

| API value | Target label (customer + office) |
|-----------|----------------------------------|
| `collecting` | 信息收集中 |
| `handoff_pending` | 资料已齐 · 可提交 |
| `handed_off` | **已交办公室** (replace office-only “已移交” for parity) |
| `office_followup` | 办公室跟进 |

Quote readiness (`quote_ready_status`) remains **整理度：可报价 / 差一点 / 信息不足** on strips where already shown; queue cards keep existing quote-ready tags without duplicating the full strip.

## Target record identity model

1. **Queue card:** first line under tags — `{服务记录编号}：{case_id}` with **copyable** text (same pattern as customer closure).
2. **Opened case:** same line + short hint that the id matches the customer **受理结果卡** (configurable via `office_workbench_case_id_hint`).
3. **CTA:** `office_workbench_open_record_cta` default **打开本条服务记录** (replaces English “case” in primary action).

## Target next-action consistency

Unchanged in this sprint: `broker_next_step` preview on queue cards and **您的下一步** in detail remain the office truth. Record id + lifecycle parity **frame** that text as the same ticket.

## Acceptance criteria

- [x] Workbench queue card shows copyable **服务记录编号** for every saved case.
- [x] Workbench open case shows the same id + configurable cross-surface hint.
- [x] Lifecycle tags on queue + detail use `getOfficeLifecycleTag` / `LIFECYCLE_STATUS_LABELS` (no orphaned “已移交” for `handed_off`).
- [x] `npm run build` (UI) succeeds; `bash scripts/guardrail_inbox_triage.sh` passes.
- [ ] Manual browser confirmation of tab switch Customer → Workbench with same `case_id` (recommended operator check).
