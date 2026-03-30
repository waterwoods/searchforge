# State / flow micro-spec

## Current weak points (pre-change)

| Area | Issue |
|------|--------|
| Customer progress (Add-Car, pre-submit) | Status strip present, but **no single “您这边下一步”** block; next step buried in generic section or only in chips. |
| Post-handoff result card (Add-Car) | State strip + record ID strong; **broker_next_step** appeared **after** long “下一步” divider and processing copy—harder to scan as **office action**. |
| Workbench queue | Many tags + lifecycle chip; **no `AddCarCaseStatusStrip`** matching customer closure → weaker **record continuity**. |
| Workbench detail | Same—Add-Car context relied on inline tags, not the **same strip component** as customer side. |

## Target state-first improvements

1. **Customer next lane (pre-handoff, Add-Car only)**  
   - One bordered block under the status strip, heading configurable (`add_car_customer_next_lane_heading`).  
   - Body driven by state: `handoff_pending` → explicit submit CTA (uses actual submit button label); `still_needed_fields` → short enumerated gap list; else `next_best_question`.  
   - Suppress duplicate “下一步（系统建议）” when this lane is shown.

2. **Post-handoff Add-Car**  
   - Move **办公室侧下一步** immediately **after 服务记录编号** (before “当前请求与类型” / structured panel).  
   - Non–Add-Car path unchanged (broker block stays in the “下一步” section).

3. **Workbench parity**  
   - Queue card: render `AddCarCaseStatusStrip` for Add-Car-shaped cases (`triageResultLooksLikeAddCar`), phase from `lifecycle_status` (`handed_off` / `office_followup` → submitted, else intake).  
   - Detail panel: same strip under record ID.  
   - Drop redundant standalone lifecycle `Tag` on queue rows when strip is shown (avoid duplicate lifecycle chip).

## Flow lift through state

Flow feels more **task-like** because:

- The **next customer action** is tied to **lifecycle and gaps** in one place.  
- The **next office action** is **adjacent to record ID** on closure.  
- **Office list + detail** use the **same state strip** as the customer journey.

## Acceptance criteria

- [x] Add-Car pre-handoff shows **您这边下一步** lane when derivable body exists.  
- [x] Add-Car post-handoff shows **办公室侧下一步** above category / structured summary.  
- [x] Workbench queue + detail show **AddCarCaseStatusStrip** for Add-Car-shaped cases.  
- [x] `cd ui && npm run build` succeeds.  
- [ ] End-to-end visual QA in browser (not run in this sprint window).
