# Workbench echo + broker dry-run spec

## Current customer entry vs workbench difference

**Customer entry** communicates (via `portal_*`, `add_car_*`, pilot alert, quick-start):

- Add-car quote is the **recommended flagship** path for the pilot.
- Submissions become a **服务记录** handed to the office; same thread can be continued.
- Non–add-car is possible but **not equally mature**.

**Workbench (prior)** communicated:

- Operational mechanics: paste raw message → triage → next step / fields / draft.
- Tab label: “办公室工作台 — 办公室” with no Add-Car or continuity cue.
- Queue titled “最近 case” / “工作队列” with no explicit link to **customer portal submissions**.

## Desired Add-Car-first workbench echo

1. **Tab bar**: Broker tab uses a **suffix** parallel to customer tab, e.g. Add-Car priority + **same service record queue** as customer entry.
2. **Hero block**: Subtitle states: same **服务记录** world as customer报送; **加车报价** as strongest pilot path; paste workflow unchanged.
3. **Queue & paste cards**: Titles use **服务记录** language and “与客户报送同源” where appropriate.
4. **In-case hint** (add-car focus): Wording matches customer CTA (**办理加车报价**), not legacy “获取报价 / 加车”.
5. **Document title**: Reflects pilot framing (Add-Car workbench), not generic “统一收件” only.

## Desired broker reading model

When opening the workbench after (or instead of) watching customer entry, the broker should read:

1. **What this product is**: Add-Car-first intake pilot; office confirms before external action.
2. **What came in**: A **服务记录** aligned with what the customer sees (same case id concept).
3. **What to do next**: Unchanged: `broker_next_step`, collection stage, drafts — already strong; framing around them should not compete.

## Dry-run acceptance criteria

1. **Coherence**: Read portal hero + pilot alert, then switch to workbench tab — narrative does not feel like a different product.
2. **Same-case feel**: Tab suffix or hero mentions **与客户报送同一服务记录 / 同源** (or equivalent in copy).
3. **Flagship path**: Add-car is visibly **primary** in workbench chrome without claiming other flows are as mature.
4. **Operator scan**: In under 30 seconds, a broker can answer: “Is this the desk view of what customers submit?” → Yes.
5. **Build**: `cd ui && npm run build` succeeds after UI changes.

## Example dry-run scenarios

**A. Add-car (Tesla)**  
Customer tab: 办理加车报价 → handoff. Broker tab: queue shows service record; open case — add-car hint matches customer language; case id visible.

**B. Pasted broker message (same content)**  
Paste “客户要加一台 2021 Tesla…” — focus tag 加车报价; hero/subtitle still frame pilot as Add-Car-first.
