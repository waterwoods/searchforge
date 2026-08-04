# LangSmith Redaction Policy — Accident Story (PR B)

**Signed:** 2026-08-04  
**Scope:** `accident_story_langgraph_v1` traces only (QA / lab)  
**Code SSOT:** `services/fiqa_api/inbox_triage/accident_story_assistant/tracing.py`

## Never send to LangSmith (inputs / outputs / metadata)

- Full raw accident story text
- Normalized story / incident summary prose
- Customer phone / name / OpenID
- Resume tokens / session secrets / dit tokens
- Photo URLs or file paths

## Allowed

- `story_char_len`, `story_lang_hint` (zh / en / mixed_zh_en)
- Field keys, missing key lists, question counts
- Injury enum (`yes` | `no` | `unknown`)
- Boolean flags (`used_fallback`)
- `fallback_reason_category` (not raw exception blobs with customer text)
- `latency_ms`, model provider/name
- `command_id_prefix` (≤12 chars)
- `case_id_hash_prefix` (sha256[:12])
- `scenario` fixture id
- `assistant`, `schema_version`, `proposal_version`

## Metadata allow-list

See `META_ALLOWLIST` in tracing.py. Evaluators fail if any other key appears.

## Default posture

Tracing is **opt-in**. No API key → silent no-op. Production/waterwoods remain untouched by this PR.

## LangGraph auto-trace suppression

When `LANGCHAIN_TRACING_V2` is on, LangGraph `compile().invoke()` otherwise uploads
**full** `AccidentStoryState` (including `raw_story`) under bare node names.

Pilot safety requires:

1. `process_inputs` / `process_outputs` on `@maybe_traceable` wrappers
2. `tracing_context(enabled=False)` around `app.invoke` so nested auto-traces never ship prose
3. Kill switch `ACCIDENT_STORY_LANGSMITH_TRACING=0` (call-time, no reimport)

See online validation evidence under `docs/evidence/langsmith-pr-b/online-validation/`.
