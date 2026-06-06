# Reply policy spec — post-handoff variety + truth

## Current weakness

- **Add-car handoff** often used a **single** `handoff.add_car` line for every post-handoff turn, so repeated “资料已到办公室…” style closures felt canned.
- **Follow-up type** (`follow_up_type`) already existed for non–add-car keys, but **add-car** did not branch on intent (except special stitched paths: materials sent, doc clarification, coverage side question).

## Target post-handoff reply families (Add-Car)

| Family | When (bounded rules) | Intent |
|--------|----------------------|--------|
| **supplement** | `new_info` from **turn 2+**, short, not a long question | Customer added a fact (e.g. driver, note) after the first bubble |
| **timeline_process** | Markers: 多久, 什么时候, 流程, 进度, how long, … | Customer asks timing / stage |
| **quote_detail** | Markers: deductible, 免赔, 保额, liability, … | Customer asks options / coverage detail |
| **correction** | `follow_up_type == correction` | Customer corrected prior info |
| **materials_sent** | Existing: completed-send + add-car | Customer claims materials already sent |
| **default** | Fallback | Office handoff without over-specific intent |

**Narrow coverage-adjust question** (“coverage 可以调吗” style) keeps **default** family so the existing stitched **coverage answer + suffix** path still applies without duplication.

## Truth constraints

- Do **not** imply name/phone are on file when `_add_car_structured_fields` still lists `name` or `phone` in `still_needed_fields` for quote-ready / almost-ready cases — append **`stitched.handoff_add_car_contact_gap_tail`** (one sentence).
- Do **not** promise a quote amount or full verification of materials; office remains the authority.
- **Corrections:** prefer “record updated to latest” framing without inventing old→new field audits when not available.

## Acceptance criteria

- Same turn with different intent produces **different** `client_reply_draft` (add-car) for at least: supplement vs timeline vs quote_detail vs default.
- **Guardrail** `scripts/guardrail_inbox_triage.sh` passes.
- New behavior is **config-driven** (client `handoff_phrases.json`); no cross-client wording bleed.
