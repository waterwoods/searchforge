# Stitched Copy Externalization Priority Spec

## Decision table

| Candidate | Priority | Decision | Location |
|-----------|----------|----------|----------|
| Add-car materials-sent handoff | P0 | **Externalize now** | `stitched.add_car_materials_sent` |
| Why-still-chasing + other_received | P0 | **Externalize now** | `stitched.why_still_chasing_reassurance` |
| Prospective-send lead (zh/en variants) | P0 | **Externalize now** | `stitched.prospective_send.*` |
| Append-case boundary continuity (中文) | P1 | **Defer** | `_apply_append_case_boundary` in `triage.py` |
| Coverage adjust + handoff suffix | P1 | **Defer** | `triage_conversation` overlay |
| Append borderline / new-issue full block | P2 | **Defer** | same function family |
| Price sensitivity “办公室算出来” (collecting) | P2 | **Keep / later** | `_build_client_reply_draft` add-car branch |

## Schema (implemented)

Inside `configs/clients/<id>/handoff_phrases.json`:

```json
"stitched": {
  "add_car_materials_sent": { "zh": "...", "en": "..." },
  "why_still_chasing_reassurance": { "zh": "...", "en": "..." },
  "prospective_send": {
    "zh_wechat": "...",
    "zh_screenshot": "...",
    "zh_bundle": "...",
    "en_wechat": "...",
    "en_screenshot": "...",
    "en_bundle": "..."
  }
}
```

Missing keys → **previous engine defaults** (no cross-client merge).

## Rules

- No DSL, no logic in JSON — **phrases only**.
- Do not change handoff gating or slot rules in this sprint.
