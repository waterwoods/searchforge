# Accident Story — Timeout & Resource Bounds

| Control | Default | Bound | Rationale |
|---------|---------|-------|-----------|
| Story length | 2000 chars | 200–8000 | Cost + normalize parity |
| Follow-up questions | 3 | hard max 3 | Product contract |
| LLM timeout | 8s | 0.5–30s | Keep mobile UX responsive |
| LLM retries | 1 | 0–2 | No unbounded agent loop |
| Payload size | 32 KiB | ≤128 KiB | Reject abuse safely |
| Idempotency | in-process cache | per command key | Duplicate protection |
| Deterministic fallback | always on | cannot disable | Safety contract |

Env knobs: `ACCIDENT_STORY_MAX_STORY_CHARS`, `ACCIDENT_STORY_LLM_TIMEOUT_SECONDS`, `ACCIDENT_STORY_LLM_MAX_RETRIES`, `ACCIDENT_STORY_MAX_PAYLOAD_BYTES`.
