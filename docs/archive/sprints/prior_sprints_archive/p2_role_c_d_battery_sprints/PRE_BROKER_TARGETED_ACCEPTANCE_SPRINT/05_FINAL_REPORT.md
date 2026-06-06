# Pre-Broker Targeted Acceptance Report

## 1. Sprint theme
- what was tested: final broker-facing targeted Add-Car + boundary + client-isolation acceptance set, plus guardrail and trial-readiness checks
- why now: this is the final confidence gate before showing Unified Intake website to Chen Kui

## 2. Scenario set
- how many scenarios: 11 targeted scenarios
- which ones: clean path, partial->completion, correction, materials-sent, ask-to-send, price-sensitive, office/handoff clarity, append boundary, client-isolation spot check (2 variants), flagship one-message
- why they were chosen: highest broker relevance, highest demo visibility, and highest trust impact in live review

## 3. Validation summary
- what was run:
  - `PYTHONPATH=. python3 scripts/run_pre_broker_targeted_acceptance.py` -> 10/11 pass
  - `bash scripts/guardrail_inbox_triage.sh` -> PASS
  - `bash scripts/trial_readiness_check.sh` -> PASS
- what passed:
  - all required categories except one flagship consistency check passed
  - full guardrail chain passed (including multi-turn, adversarial, boundary, cross-client, residual-copy packs)
  - trial-readiness check passed (including UI build)
- what failed:
  - `PBTA-10` (flagship all-info one message) failed strict consistency assertion:
    - observed `quote_ready_status=quote_ready`
    - while `still_needed_fields` includes `delivery_date`
- what was directly verified vs inferred:
  - directly verified: targeted scenario JSON output, guardrail output, trial-readiness output
  - inferred: local code path is stable for founder demo because broad suites pass
  - not verified: production Cloud Run revision/live URL and Vercel production alias alignment in this sprint

## 4. Live readiness check
- backend status:
  - local backend was not running on `:8001` in this session (`/healthz` unreachable)
  - however readiness pipeline and API-related guardrails passed in direct mode
- frontend status:
  - UI build passed via `trial_readiness_check.sh`
- whether Vercel is ready enough to show now:
  - **partially yes for founder demo context**
  - **not fully proven for production claim** in this sprint because live Vercel alias and Cloud Run post-deploy checks were not executed

## 5. Broker-facing acceptance judgment
- strongest parts:
  - Add-Car intake coverage across clean/partial/correction/materials/prospective-send
  - boundary separation (`new_issue`) behavior is credible
  - client wording isolation spot check passed (`办公室` vs `本所`)
  - broad regression/guardrail suite is green
- main caveats:
  - one semantic consistency caveat on flagship one-message case (`quote_ready` with `delivery_date` still needed)
  - this sprint did not complete production URL-level alignment checks
- what not to oversell:
  - do not claim fully verified production deploy alignment
  - do not claim every quote-ready signal is perfectly semantically aligned in all dense one-message phrasing
- whether Andy should show it now:
  - **yes, show now for broker feedback**, with caveat framing and no production-overclaim

## 6. Best 2 demo cases
- exact text to paste:
  - case 1 (correction credibility):
    - `加一台2022宝马X5，邮编94506，明天提车，我开`
    - `不对，是2023宝马X5`
  - case 2 (prospective-send + office handoff realism):
    - `2024特斯拉Model 3，95131，明天提车，我自己开，要不要发你行驶证截图`
- what the broker should pay attention to:
  - case 1: system keeps transaction context and updates corrected vehicle before handoff
  - case 2: system distinguishes “ask to send” from “already sent” and still gives practical office flow

## 7. 中文宏观总结
- 现在是不是可以给陈奎看了:
  - **可以看了**。作为“经纪人反馈前最后一轮验收”，核心路径已经够稳。
- 我们最后这一轮主要测了什么:
  - 重点测了加车主路径（完整、补全、更正、材料已发/拟发送、价格敏感）、追加消息边界、以及跨客户话术隔离。
- 哪些地方现在最像真办公室流程:
  - 客户给齐信息后能进入办公室处理口径；更正车辆信息后能继续同一交易；“要不要发你”与“我已发你微信”能分开处理；边界场景能提示新问题分流。
- 还差什么:
  - 还需补一次**生产级别**的 Cloud Run + Vercel 对齐核验（不是代码逻辑问题，是发布确认问题）。
  - 还有一处“quote_ready 与 still_needed 字段并存”的语义一致性瑕疵，建议在对外叙述时避免过度承诺。
