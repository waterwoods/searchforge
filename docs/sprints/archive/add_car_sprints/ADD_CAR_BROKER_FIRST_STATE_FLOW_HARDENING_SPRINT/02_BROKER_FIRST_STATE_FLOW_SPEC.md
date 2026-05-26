# Broker-first state + flow spec (Add-Car)

## Current first-impression weaknesses (evidence-based)

| Weakness | Evidence |
|----------|----------|
| Thread read before task state (pre-handoff) | `UnifiedIntakePage.tsx`: progress card rendered **after** thread when `turns.length > 0`. |
| Result card: headline before record anchor | Handoff closure: eyebrow/headline preceded **服务记录编号**; ID felt secondary to prose. |
| Workbench queue: ID below tag cloud | `renderRecentCaseCard`: Add-Car status strip then many tags, then monospace ID—same record harder to match at a glance vs customer card. |
| Status strip caption slightly timid | `AddCarCaseStatusStrip` caption at 11px—state label competed with bubble chrome. |

## Target state-first improvements

- **Pre-handoff Add-Car:** **Progress card (status strip + customer next lane + fields)** renders **above** “报送过程” so brokers/customers see **state before transcript**.
- **Status strip:** Caption **12px / semibold** so “当前状态” reads as a **section label**, not fine print.
- **Post-handoff:** **服务记录编号** immediately after lifecycle/status strip—**record → then** eyebrow/headline/broker next—mirrors Zendesk-style ticket header.

## Target next-step clarity improvements

- Customer **您这边下一步** lane unchanged logically; it **moves up** with the progress card so it is not **below** the scrollable thread.
- Office **broker_next_step** on result card remains; ordering keeps **record ID + state** as the anchor before narrative blocks.

## Target same-record continuity improvements

- **Workbench Add-Car queue cards:** **Strip → 服务记录编号 →** metadata tags—parallels customer **status strip + ID** order.
- **Default UI copy** (`clientConfig` fallback): result-card hint explicitly ties **编号** to office queue alignment.

## Acceptance criteria

1. With an active Add-Car session **before** handoff, the **加车报价 · 进度** card appears **above** the thread card.
2. Non–Add-Car sessions keep **thread above** progress card (no scope expansion).
3. After handoff, **服务记录编号** appears **directly under** the status strip in the green result card.
4. Add-Car workbench queue rows show **服务记录编号** **directly under** `AddCarCaseStatusStrip`, not after the tag row.
5. `cd ui && npm run build` succeeds.
