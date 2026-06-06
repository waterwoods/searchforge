# ADD_CAR_REPLY_POLISH_ALREADY_SENT_LLM_SPOTCHECK — Final report

## What changed

- **Industry** `reply_templates.json`: shorter Add-Car baseline; missing-document “already sent” branches emphasize **verify / no full resend**.
- **`add_car_rules.json` + `config_loader.py` defaults**: shorter next-step asks (vehicle / zip / delivery).
- **`triage.py`**: shorter progressive Add-Car asks (EN/ZH); **no acknowledgement echo** when the last customer message is a **completed material-send** claim; shorter default `add_car_materials_sent` fallbacks; shorter prospective-send ZH leads; extended **clarification** markers (`还缺什么`, `你先看看`, etc.); **new handoff branch** for Add-Car + clarification when **`[系统]`** already appears (ongoing thread).
- **`chen_kui/handoff_phrases.json`**: shorter `add_car` and `add_car_materials_sent`; aligned `prospective_send` ZH; new `add_car_clarification_followup`.
- **AB batteries** (`residual_copy_ab_scenario_battery.json`, `small_batch_ab_scenario_battery.json`): allow new flagship handoff substring **加车报价已交办公室**.

## What was tested

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (scenarios, multi-turn, adversarial, cross-client, residual, small-batch).
- `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_realistic_intake_scenarios.py` — **PASS** (structural / path).
- Manual draft samples: one-shot handoff; materials-sent handoff; post-system “还要补什么吗” follow-up.

## What improved

- **Brevity** and **office-review** framing on Add-Car handoffs and materials-sent path.
- **Less echo** on “发过了 / 微信发了” turns (ack suppressed).
- **Better follow-up** when the customer asks what is still missing after the assistant has already replied.

## What remains

- **LLM path** not exercised: no `OPENAI_API_KEY` / `LLM_API_KEY` in this environment (`_is_llm_enabled()` false).
- **R4-style** single bubble without model year still lands `need_more` (pre-existing extraction limitation; not this sprint’s scope).
- **Other clients** (e.g. `socal_precision`) use their own handoff JSON; only Chen Kui got optional `add_car_clarification_followup` (others use triage defaults for that branch).

## Recommended next sprint

- **LLM-on regression slice**: 10–15 fixed Add-Car prompts with mandatory `triage_path` tagging and max-length caps on `client_reply_draft`.
- Or **pilot polish**: align `ui_copy.json` closure headlines with shorter backend handoff wording for end-to-end consistency.
