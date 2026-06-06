# Boundary Copy Leak Audit Spec

## Scope

Customer-visible text emitted when `triage_for_append` sets `case_boundary` to `new_issue` or `borderline` (overriding `client_reply_draft` from the base triage pass).

## Pre-sprint leak inventory

| Location | What leaked | Frequency / visibility | Safe to externalize? |
|----------|-------------|------------------------|----------------------|
| `_apply_append_case_boundary` ZH continuity lines (`加车这边办公室会继续跟进` …) | Shared **办公室** narrative for all clients | **High** on any cross-topic append after add-car handoff | **Yes** — pure wording |
| ZH tails (`账单问题我也一起转给办公室核实` …) | Same | **High** | **Yes** |
| ZH add-car split hint (`提交新问题` …) | Same voice | **Medium** (add-car prior + new issue) | **Yes** |
| EN continuity / tails / split hint | Shared **office** phrasing | **Medium** (EN threads) | **Yes** |
| Borderline ZH/EN paragraphs | Shared **办公室 / office** | **Medium** | **Yes** |
| `broker_next_step` prefixes (`Case boundary:…`) | English, broker-facing | Lower for **customer** portability | **Keep in code** (this sprint) |
| `conversation_summary` tags (`Boundary: new_issue…`) | Broker/scanner facing | Same | **Keep in code** |
| `_classify_append_case_boundary` marker tuples | Detection policy | N/A | **Keep in code** — not “voice” |

## Highest priority

1. **ZH new_issue** continuity + tails + add-car split hint (known **ab_10** leak for Client B).
2. **Borderline** customer draft (ZH + EN).
3. **EN** new_issue strings for parity and future EN-first brokers.

## Post-sprint

- **Still engine-owned (intentionally):** boundary **classification**, broker `Case boundary:` prefixes, summary tags, `_SYSTEM_ADD_CAR_HANDOFF_MARKERS` used only for **prior-domain inference** (not shown to customer as a block).

## Optional checklist (before / after)

**Before:** Run `triage_for_append` as Client B on add-car thread → billing pivot; draft contained **办公室** despite B’s **本所** handoff pack.

**After:** Same call; draft uses **本所** / **本所同事** from `stitched.append_boundary` when configured; Client A unchanged if section omitted.
