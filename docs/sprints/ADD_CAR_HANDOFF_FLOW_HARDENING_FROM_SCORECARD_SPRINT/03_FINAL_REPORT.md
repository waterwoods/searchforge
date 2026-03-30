# ADD-CAR HANDOFF + FLOW HARDENING FROM SCORECARD — Final report

## What changed

- **Chen Kui handoff phrases** (`handoff_phrases.json`): flagship add-car closure emphasizes **资料已到办公室**; **materials-sent**, **clarification follow-up**, and **why still chasing** lines shortened and de-duplicated (“收到” stacking reduced).
- **Industry templates + add-car rules**: first-turn add-car copy frames **office quote flow**; rule asks reference **办公室报价** without lengthening every reply.
- **Triage** (`triage.py`): Chinese add-car acknowledgements use **收到，** / **收到，按 … 继续** (and EN **Thanks,** / **Noted—**) instead of **好的，** / **Got it,**; **append** continuity for prior add-car is **本条加车记录办公室在跟进中**; engine fallbacks for stitched paths aligned with new copy.
- **Portal defaults** (`clientConfig.ts` + `chen_kui/ui_copy.json`): closure **processing** line states **下一步由办公室…** and **您…无需重复发送**; toast and **case created** lines stress **本条加车记录**; flow track steps **收齐报价要点** / **转交办公室处理**; result-card hint mentions **进入办公室队列**.
- **Guardrail battery** (`small_batch_ab_scenario_battery.json`): regression check allows new flagship substring **加车资料已到办公室**.

## What improved

- **HANDOFF:** More **received → office owns verification/pricing** language; **already-sent** and **materials-sent** paths read as **desk workflow**, not repeated reassurance stacks.
- **FLOW:** Portal **post-submit** and **step labels** better separate **customer intake** vs **office processing**; append **same-record** continuity is more explicit for add-car.

## What remains

- **FLOW** still **chat-shaped** at the UX level (scorecard: needs stronger non-thread metaphor to reach 4+).
- **STATE:** Workbench parity (record id / status strip) not addressed.
- **LLM path** not guardrail-equivalent; spot-check optional.
- `scripts/run_pre_broker_targeted_acceptance.py` **PBTA-10** (`quote_incomplete` vs `quote_ready` on one Tesla message) **failed** in this environment—**not caused by copy edits** this sprint; treat as **separate triage/expectation** follow-up.

## Scorecard movement (conservative)

| Dimension | Before | After (estimate) | Note |
|-----------|--------|------------------|------|
| HANDOFF | 3 / 5 | **~3.5 / 5** | Copy + ack tone; no persistence/auth leap |
| FLOW | 3 / 5 | **~3.25 / 5** | Portal/step framing only; thread UX unchanged |
| PAGE / STATE | unchanged | unchanged | Out of sprint focus |

## Recommended next sprint

1. **STATE / workbench parity** — same **服务记录编号 + status strip** on queue cards as customer closure (scorecard runner-up).
2. **PBTA-10 / quote_ready** — reconcile **delivery_date** extraction vs acceptance expectation.
3. Optional: **LLM-on** spot-check for handoff-adjacent turns.

## Validation run (this sprint)

- **Directly verified:** `bash scripts/guardrail_inbox_triage.sh` **PASS**; `scripts/run_inbox_triage_scenarios.py` **64/64**; `scripts/run_handoff_timing_simulations.py` **13/13**; append boundary **12/12**; pre-broker **10/11** (PBTA-10 only).
- **Inferred:** HANDOFF feel from draft text review on **还缺什么** continuation (uses clarification-follow-up stitched line).
- **Not verified:** Live **8001** HTTP path; **LLM_ENABLED=1** behavior.

## Sprint timing

- **End (recorded):** 2026-03-27T21:38:17-07:00  
- **Elapsed (rough):** ~25–40 minutes implementation + validation (single session)
