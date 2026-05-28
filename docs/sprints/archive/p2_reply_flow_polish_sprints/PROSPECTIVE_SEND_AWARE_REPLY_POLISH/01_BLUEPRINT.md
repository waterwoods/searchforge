# Prospective-Send-Aware Reply Polish — Blueprint

## Product goal

When a customer asks whether to send materials (e.g. 要不要发你, 要不要先发给你, 要不我发你微信, 要不要把截图发你, 我先发给你看看行吗), the system already classifies this as **not** “already sent.” The gap is **voice**: the customer-facing reply should briefly answer that question in a short office tone, then continue normal Add-Car collection or handoff.

## Non-goals

- Frontend, OCR, carrier APIs, new non–Add-Car scenarios, architecture rewrites.

## Design principles

1. **Trust**: Do not change `already_sent` vs prospective-send classification semantics.
2. **Brevity**: One short lead sentence; no FAQ.
3. **Single injection point family**: Reply assembly in rule-based Add-Car paths (`_get_next_ask_for_add_car`, `_build_client_reply_draft` add-car branch, `triage_conversation` handoff overlays).

## Success signal

Founder/broker reads the reply and feels the customer’s question was heard, without slowing handoff or slot collection.
