# ADD_CAR_REPLY_POLISH_ALREADY_SENT_LLM_SPOTCHECK — Blueprint

## Sprint goal

Improve **Add-Car** customer-visible quality in three lanes: **shorter office-like replies**, **stronger already-sent / materials-under-review handling**, and **documented LLM vs rule alignment** (spot-check when API keys exist).

## Why now

Simulation work improved understanding and rule-path stability, but replies could still feel **verbose**, **echo-heavy**, and **light on “office is reviewing what you already sent”**. Pilot trust depends on this tone.

## Scope

**In scope**

- Add-Car reply brevity and progressive asks
- Already-sent / materials-sent handoff and missing-doc “already sent” templates
- Follow-up clarification in an ongoing add-car thread (e.g. “还缺什么”)
- Industry `reply_templates`, `add_car_rules`, client `handoff_phrases` where needed
- Minimal triage logic: no-echo ack for completed material-send; clarification follow-up branch
- Guardrail + AB battery string updates where they encode old flagship handoff text

**Out of scope**

- Engine rewrite, new eval framework, broad non–Add-Car flows, UI redesign, deployment

## Current weaknesses (pre-sprint)

- Long flagship add-car handoff and materials-sent paragraphs
- `_get_add_car_acknowledgement` could **echo** short “发过了”-style lines
- Add-car thread + clarification follow-up reused **full flagship handoff** instead of a short “we’ll verify” line
- Missing-document “already sent” copy re-asked for **full notice + everything** in a heavy way

## Target outcome

- Replies read like a **broker desk**: short, directional, minimal parroting
- “已发 / 微信发了” paths stress **review**, **no full resend**, **only missing items if any**
- Rule path remains **guardrail-green**; LLM path spot-check recorded honestly when keys unavailable
