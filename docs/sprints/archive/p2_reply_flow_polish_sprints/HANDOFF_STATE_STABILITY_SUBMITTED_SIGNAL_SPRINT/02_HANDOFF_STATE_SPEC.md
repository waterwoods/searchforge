# Handoff state spec — target vs ambiguity

## Ambiguity / stability issues (before)

1. **API `handoff_ready` conflates two moments:** “information sufficient for office work” and “customer has formally submitted / case persisted.” For Add-Car, `lifecycle_status === handoff_pending` still carries `handoff_ready: true`.
2. **Portal used `handoff_ready` to switch UI:** That hid the input + submit lane and showed the **post-handoff closure** while the customer was still in `handoff_pending` (no `case_id`)—the opposite of “ready but not yet formally submitted.”
3. **Flow step 3 fired on `handoff_ready`:** The Amazon-style track jumped to “办公室接手” before the office actually had a persisted record.
4. **Workbench queue:** Persisted Add-Car cases are stored as `handed_off`, but queue scan did not always surface “已报送办公室” before quote-ready heuristics.

## Target state model (customer + office)

| Phase | API signals (truthful) | Portal / product read |
|--------|-------------------------|------------------------|
| Collecting | `lifecycle_status: collecting` | 信息收集中；输入+提交继续补齐 |
| Ready, not formally submitted | `handoff_pending`, `handoff_ready: true`, **no `case_id`** | 资料已齐 · 可提交；**不**显示“已提交办公室”闭包 |
| Office received | **`case_id` present** or stored `lifecycle_status` in `{handed_off, office_followup}` | 闭包区、步骤 3、送达时间（若有 `created_at`） |

## Submitted observability goal

- Prefer **`case_id`** as the primary “formally submitted” signal (matches persistence).
- Show **`created_at`** as “送达办公室时间” when returned on the triage/case payload (no synthetic timestamps).

## Acceptance criteria

1. In `handoff_pending` without `case_id`, the customer still sees the **input + “正式提交办公室”** path and the **pre-handoff** progress/rail—not the green post-handoff closure.
2. After successful persist, `case_id` is set and the closure + office step 3 apply.
3. Add-Car queue row for Add-Car-shaped cases with `handed_off` / `office_followup` shows **已报送办公室** at scan level.
4. No new persistence contracts; guardrail `scripts/guardrail_inbox_triage.sh` passes.
