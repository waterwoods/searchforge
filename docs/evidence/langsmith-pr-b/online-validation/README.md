# Online LangSmith validation (redacted)

**Status:** see `ONLINE_VALIDATION_REDACTED.json`

## What was checked

1. Local credentials present (`LANGCHAIN_API_KEY` + project) — values never printed/committed
2. Synthetic propose with unique story marker
3. Recent project runs scanned for that marker in inputs/outputs/metadata
4. After pilot-safety fix: LangGraph auto-trace suppressed; `@maybe_traceable` redacts I/O

## Optional Founder action (Cloud QA only)

Set on **fiqa-api-qa** only:

- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT=<approved project>`

Do not put keys in git. Do not touch Production or waterwoods.
