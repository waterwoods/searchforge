# Reply routing spec — formal submit aware (Add-Car)

## Prior weakness

- `triage_conversation` always composed Add-Car handoff copy as if the customer were still **pre-submit**, unless packs happened to be manually tuned.
- `triage_for_append` did not pass persisted truth into triage, so **office follow-up** on an existing case could still read like “wait until you formally submit.”

## Target routing model

| Phase | Truth gate (examples) | Reply intent |
|--------|-------------------------|--------------|
| **A — Pre-submit (`handoff_pending`)** | No `formal_submitted_at`; not `formal_submit_this_turn`; lifecycle not `handed_off` / `office_followup` | Information may be ready; **invite** formal submit; do **not** claim office already has the durable record. |
| **B — Formal submit this request** | `formal_submit_this_turn` + Add-Car lane | Office-visible persist is happening **now**; may state record is **formally delivered** (aligned with same-request persist). |
| **C — Post-submit follow-up** | Persisted `formal_submitted_at` and/or lifecycle `handed_off` / `office_followup` (append) | Updates are **on an existing office-visible record**; stronger in-queue / continuation wording; no quote/verification overclaim. |

## Allowed vs forbidden (oracles)

**Allowed only with B or C gates**

- Strong office-receipt / in-queue language, e.g. 已正式送达办公室、已在办公室处理中、按当前服务记录继续核对.

**Forbidden without B or C**

- Wording that implies the office already holds the customer-committed record when only `handoff_ready` / pre-submit truth holds.

**Always forbidden in Stage 1 replies (unchanged)**

- Quote bound / verification complete / all materials confirmed—unless structured truth supports it per industrial spec.

## Implementation hooks

- `triage_conversation(..., reply_truth_context=...)`
- `POST /api/inbox/triage`: optional `case_id` + existing `formal_submit` → builds context
- `triage_for_append`: `reply_truth_context` from loaded case
- Packs: `add_car_*_submitted` handoff keys; stitched `*_submitted` variants; engine `_POST_SUBMIT_ADD_CAR_FALLBACK_ZH_EN` if pack omits keys

## Acceptance criteria

1. Pre-submit Add-Car handoff still **does not** claim formal office receipt without truth context.
2. With `formal_submit_this_turn` or persisted case context, Add-Car replies use **post-submit** families (pack or fallback), not “请先正式提交” tails.
3. Append flow (`/cases/{id}/append-message`) uses post-submit phrasing for Add-Car when case has normalized `formal_submitted_at`.
4. `bash scripts/guardrail_inbox_triage.sh` passes.
