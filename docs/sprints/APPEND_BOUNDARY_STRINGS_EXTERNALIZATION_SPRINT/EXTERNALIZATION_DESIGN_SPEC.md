# Externalization Design Spec

## Pattern

Reuse the existing **`handoff_phrases.json` → `stitched`** mechanism (same file as `add_car_materials_sent`, `prospective_send`). New sibling key: **`append_boundary`**.

## Config location

`configs/clients/<client_id>/handoff_phrases.json`

```json
"stitched": {
  "append_boundary": {
    "continuity_zh": { "add_car": "…", "claim": "…", "remove_car": "…", "payment": "…", "missing_doc": "…", "premium": "…", "generic": "…" },
    "new_issue_tail_zh": { "claim": "…", "billing": "…", "remove_car": "…", "premium": "…", "add_car": "…", "default": "…" },
    "continuity_en_add_car": "… ",
    "continuity_en_other": "… ",
    "new_issue_tail_en": { "claim": "…", "billing": "…", "remove_car": "…", "premium": "…", "add_car": "…", "default": "…" },
    "add_car_split_hint_zh": " …",
    "add_car_split_hint_en": " …",
    "borderline_zh": "…",
    "borderline_en": "…"
  }
}
```

## Merge / fallback

- Loader: `get_stitched_handoff_phrases` (unchanged contract); `triage._merged_append_boundary_copy` merges client `append_boundary` over `_APPEND_BOUNDARY_DEFAULTS`.
- **Nested maps** (`continuity_zh`, `new_issue_tail_*`): per-key override; omitted keys keep engine defaults.
- **String fields**: if missing or whitespace-only, use engine default.
- **No cross-client fallback** (same rule as other `stitched` keys).
- **Trailing spaces:** string overrides use `rstrip("\r\n")` only so intentional trailing spaces for EN stitching are preserved (`.strip()` would break `continuity + tail`).

## No-cross-client-leak rule

Only the **active** `client_id` (from `triage_for_append` / stitched load for that id) may supply boundary copy. There is no “read Chen Kui if key missing” for `append_boundary` (contrast: `handoff` block may still fall back to default client for incomplete packs—unchanged).

## Safe vs keep in code (summary)

| Keep in code | Externalize |
|--------------|-------------|
| `_classify_append_case_boundary`, markers, domain sets | Continuity + tail + split hint + borderline **customer** paragraphs |
| `broker_next_step` / `conversation_summary` boundary **prefixes** (broker English) | (Optional later if product wants localized broker UI) |
