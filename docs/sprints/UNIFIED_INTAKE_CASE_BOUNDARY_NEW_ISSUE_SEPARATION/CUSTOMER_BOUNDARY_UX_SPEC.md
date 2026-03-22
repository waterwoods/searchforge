# Customer Flow / Boundary UX Spec

## Principles

- **Short** (≤2 sentences), no salutation spam, **portal tone**: prior work continues with the office; new items are **routed**, not debated in chat.
- **No extra back-and-forth** to “discover” intent when rules already see a cross-domain pivot.

## Copy patterns (ZH)

| Situation | Direction |
|-----------|-------------|
| New issue after add_car + **claim** | 加车这边办公室会继续跟进。您这条理赔我先转给办公室… |
| + **billing** | …账单问题我也一起转给办公室核实。 |
| + **remove_car** | …删车/卖车我也转给办公室一并处理。 |
| Other new_issue | …您这条新问题我也转给办公室一并处理。 |
| Borderline | 收到。我先按您这条整理给办公室；如果和前面不是同一件事，也请简单说明… |

Prior domain adjusts the **first sentence** (add_car / claim / remove / payment / missing_doc / premium / generic).

## Copy patterns (EN)

Single template family with optional claim/billing/remove/add_car tails (see `triage.py`).

## Non-goals

- Long educational paragraphs.
- Asking the customer to “open a ticket” in jargon—keep **办公室** as the anchor.
