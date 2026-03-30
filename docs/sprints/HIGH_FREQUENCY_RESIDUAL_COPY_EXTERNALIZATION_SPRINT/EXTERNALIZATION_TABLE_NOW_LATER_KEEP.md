# Externalized Now / Later / Keep in Code

| Item | Now | Later | Keep in code |
|------|-----|-------|----------------|
| Add-car price caveat (zh/en) | ✅ `stitched.add_car_price_caveat` | — | Marker list for “ballpark” |
| Payment/premium doc-sent tail | ✅ `stitched.document_already_sent_tail` | — | Condition: doc markers + sent markers |
| Add-driver customer reply | ✅ `reply_templates.add_driver` | — | `_is_add_driver_request` |
| Bundling customer reply | ✅ `reply_templates.bundling` | — | `_is_bundling_request` |
| Missing_signature / UW / renewal one-liners | — | ⏳ template keys | ✅ until migrated |
| Handoff suffix “办公室…” on doc clarification | — | ⏳ stitched per path | ✅ |
| Coverage-adjust handoff line | — | ⏳ | ✅ |
| Intent markers / talk-to-agent fallbacks | — | — | ✅ |
