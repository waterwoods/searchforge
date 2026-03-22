# ZIP Extraction Hardening Spec

## Problem

`_extract_add_car_fields` used `\b9[0-9]{4}\b`. In Python, `\b` is a **word** boundary; Chinese characters are not “word” characters, so digits **glued** to 中文 (e.g. `邮编95131`) often **fail** the pattern.

## Approach

1. **Extract**: Single compiled regex with digit-aware boundaries (not `\b`):
   - `(?<![0-9])(9[0-9]{4})(?![0-9])`
2. **Normalize**: Lowercase for search; optional `zip` keyword still compatible.
3. **Validate**: Keep CA-oriented **9xxxx** assumption (existing product scope).

## Supported examples (minimum)

- `邮编95131`
- `邮编 95131`
- `zip 95131`
- Standalone `95131` adjacent to Chinese
- Mixed CN/EN in one bubble (same line as other tokens)

## Code hooks

- `_text_has_ca_zip_signal(t)` — boolean slot signal for `_extract_add_car_fields` and fast-path detection.
- `_extract_ca_zip_from_message(msg)` — acknowledgement snippets when echoing zip back.

## Out of scope

- Full US ZIP database validation.
- Non-9xxxx geographies (explicitly not expanded in this sprint).
