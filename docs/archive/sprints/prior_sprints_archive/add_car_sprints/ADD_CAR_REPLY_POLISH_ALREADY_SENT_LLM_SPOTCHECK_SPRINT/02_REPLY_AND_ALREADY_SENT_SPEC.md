# Reply quality, already-sent handling, LLM spot-check spec

## Add-Car reply principles

1. **Short** — one primary job per message (collect next field, hand off, or reassure).
2. **Office-grounded** — “办公室核对 / 出价 / 联系您”, not chatbot filler.
3. **Low echo** — acknowledge structure without repeating the customer’s whole sentence; **no** ack string for completed “材料已发” statements.
4. **Useful next step** — say what to send **next** or what the office **will** do.
5. **Configurable layers** — industry templates + `add_car_rules.json` + client `handoff_phrases` / `stitched`.

## Already-sent / materials principles

1. **Received + reviewing** — explicitly that the office will **verify** what was sent.
2. **No blanket re-request** — “不用整套重发” / “only ask if still missing” (EN).
3. **Missing-doc flow** — “already sent” branch should **not** sound like the system forgot; prefer verify language over “再发我全套”.

## Office-style tone

- Prefer **收到**, **核对**, **缺什么会再跟您说** over long formal announcements unless the product explicitly needs “正式提交” language.
- **Chen Kui** flagship handoff may stay slightly more formal than industry defaults but **shorter** than before.

## Ongoing-thread clarification (add-car)

When the thread already contains a **`[系统]`** message and the customer asks **还缺什么 / 你先看看 / anything else** (clarification class), the reply should be a **short verify line**, not a repeat of the full add-car flagship handoff.

## LLM spot-check plan

**When `OPENAI_API_KEY` or `LLM_API_KEY` is set and `LLM_GENERATION_ENABLED=1`:**

1. Run the same 2–3 multi-turn Add-Car scenarios **twice**: force contexts where `triage_path` is `fast` vs `llm` (e.g. long mixed-intent first message → LLM).
2. Compare: length, tone, handoff vs collect, already-sent handling.

**When no key:** record **not verified**; rule/fast path evidence stands.

## Acceptance criteria

- `bash scripts/guardrail_inbox_triage.sh` **PASS**
- Spot-check scenarios: full-spec add-car handoff; materials-sent handoff; VIN-pending one-shot; correction turn; mixed ZH/EN; “还缺什么” follow-up after system — **drafts shorter and more review-oriented** than pre-change baselines
- No new weak/acceptable regressions in multi-turn packs
