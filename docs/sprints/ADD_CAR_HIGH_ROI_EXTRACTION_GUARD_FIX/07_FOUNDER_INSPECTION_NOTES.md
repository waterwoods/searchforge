# Founder Inspection Notes

## What to spot-check in the workbench

1. **ZIP** — Send a second bubble that only adds `邮编95131` after a Model Y / Camry add-car opener. The UI should show zip in collected / still-needed logic consistent with “quote can move.”
2. **Driver** — Short bubble `我自己开` after year + zip should move driver from missing to collected.
3. **already_sent** — Type `要不要发你` in an add-car thread: reply should **not** sound like “you said you already sent everything.”

## Why this sprint is “industrial”

Each fix names a **failure mode**, a **deterministic rule**, and a **regression case**. No prompt-only change.

## Red flags if something regresses

- Add-car threads suddenly **LLM-only** on short turns (check `triage_path` and message length).
- True “我发你了” flows no longer get verify-with-carrier tone (check `follow_up_type` on `材料发你微信了`).

## One-line broker pitch

“We fixed three ways messy WeChat text could make the assistant look almost right but unreliable: postal codes stuck to Chinese, short driver phrases, and questions about sending mistaken for ‘already sent.’”
