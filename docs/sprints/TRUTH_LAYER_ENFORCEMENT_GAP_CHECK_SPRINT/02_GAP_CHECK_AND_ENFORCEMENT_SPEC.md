# Gap check and enforcement spec

## Current compliance review

### Already compliant

- Structured fields: `collected_fields`, `still_needed_fields`, `next_best_question`, `quote_ready_status` for Add-Car; contact-gap tail when name/phone still missing.
- Persistence: Add-Car lane requires `formal_submit` for `save_case`; `formal_submitted_at` vs `updated_at` in case store.
- Flow explanation (`AddCarFlowExplanation`): `handoff_pending` copy already distinguishes “可提交” vs “送达办公室”.
- Materials-sent path: “办公室正核对 / will verify” style copy matches truth better than receipt claims.

### Partially compliant

- `handoff_ready` / `lifecycle_status: handoff_pending` vs customer reply: engine used pack lines that sounded like office receipt (`已到办公室`, `已提交办公室`) while truth is still pre–formal submit.
- `isFormalSubmissionToOfficeComplete`: `handoff_pending` correctly blocked step 3, but a bare `case_id` could still mark step 3 in odd API shapes—tighter gate needed.

### Non-compliant / violating

- Chen Kui (and second-broker) handoff families: explicit office receipt / desk queue language on the default Add-Car handoff path before formal submit.
- `triage.py` hardcoded stitched fallbacks: “已提交办公室跟进” / “with our office for follow-up” as defaults for doc-clarification and coverage suffixes—stronger than `handoff_pending` truth.

## Chosen bounded fixes (this sprint)

1. **Client packs:** Rewrite Add-Car handoff + stitched suffixes to separate **record prepared / ready to formally submit** from **office queue receipt** (Chen Kui + SoCal precision).
2. **Engine fallbacks:** Align `triage.py` default strings with the same constraint when config is missing.
3. **UI truth gate:** `isFormalSubmissionToOfficeComplete` — require `formal_submitted_at` or post-handoff lifecycle; **do not** treat `case_id` alone as office-visible completion.

## Acceptance criteria

- Add-Car default handoff customer draft does not claim office receipt or durable queue placement before formal submit (spot-check zh/en).
- Right rail does not show “办公室已收到本条服务记录” unless formal timestamp or `handed_off` / `office_followup`.
- `bash scripts/guardrail_inbox_triage.sh` passes (including residual + small-batch copy A/B batteries updated to match the new doctrine).
