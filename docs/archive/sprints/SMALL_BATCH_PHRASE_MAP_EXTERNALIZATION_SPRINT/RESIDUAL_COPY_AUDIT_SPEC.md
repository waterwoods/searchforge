# Residual Copy Audit Spec

## Audit method

1. Inspect customer-facing assembly points in `services/fiqa_api/inbox_triage/triage.py`.
2. Cross-check existing externalized sets in:
   - `configs/clients/*/handoff_phrases.json` (`handoff`, `stitched`)
   - `configs/industries/insurance/reply_templates.json`
   - `configs/clients/*/reply_overrides.json`
3. Rank by:
   - customer visibility
   - frequency likelihood
   - cross-client leak risk
   - safety of wording-only externalization

## Residuals found pre-sprint

| Candidate family | Example engine line | Visibility | Frequency | Leak risk | Verdict |
|---|---|---:|---:|---:|---|
| Doc-clarification handoff suffix | `本次加车报价资料已提交办公室跟进...` / `. Our office will process...` | High | Medium-high | High | Move now |
| Add-car coverage side-question overlay | `保额可以调整，报价时办公室会跟您确认。` + `...办公室会尽快出价...` | High | Medium-high | High | Move now |
| Payment correction urgency handoff | `最要紧的是等办公室确认付款...` | High | Medium | High | Move now |
| Generic one-liners (`unclear`/`informational`/`policy_delay_pending`) | category replies | Medium | Medium | Lower | Defer |
| Marker/detection text | marker tuples and regex cues | N/A | N/A | N/A | Keep in code |

## Selected 2-4 families for this sprint

Selected exactly 3 families (above) because they are:
- clearly customer-visible
- repeated in high-traffic handoff contexts
- easy to externalize without touching business logic

## Keep-in-code now (explicit)

- Intent detection markers and regex conditions
- Handoff timing/routing decisions (`handoff_ready`, follow-up type, category)
- Slot extraction and stage transitions
- Business-state flags (`collection_stage`, `lifecycle_status`)
