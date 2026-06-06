# Add-Car Clear Submission + Confirmation + Office Handoff Sprint Report

Sprint folder: `docs/sprints/ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF/`  
Execution date: 2026-03-22 (agent run)

## 1. Sprint theme

- **Evaluated/fixed:** Add-Car customer perception at handoff—submission formality, confirmation of recorded fields, and office wait expectations.
- **Why now:** Intake logic was strong, but the **closure moment** dropped the structured progress view, weakening “formal request” and “what you recorded” trust exactly when the customer finishes.

## 2. Document set created

| Doc | Path |
|-----|------|
| Blueprint | `01_BLUEPRINT.md` |
| Customer submission confirmation spec | `02_CUSTOMER_SUBMISSION_CONFIRMATION_SPEC.md` |
| Office follow-up expectation spec | `03_OFFICE_FOLLOWUP_EXPECTATION_SPEC.md` |
| Customer UX options | `04_CUSTOMER_UX_OPTIONS_SPEC.md` |
| Broker/assistant operational clarity | `05_BROKER_ASSISTANT_OPERATIONAL_CLARITY_SPEC.md` |
| Founder scenario pack (narrative) | `06_FOUNDER_SCENARIO_PACK.md` |
| Founder scenario pack (machine) | `founder_scenario_pack.json` |
| Execution outline | `07_EXECUTION_OUTLINE.md` |
| Acceptance criteria | `08_ACCEPTANCE_CRITERIA.md` |
| Founder inspection notes | `09_FOUNDER_INSPECTION_NOTES.md` |
| This report | `10_ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF_SPRINT_REPORT.md` |

**Runner:** `scripts/run_add_car_submission_confirmation_sprint_scenarios.py`

## 3. Baseline audit

**Audit answers (pre-change):**

1. **Formal submission feel?** Partially—closure headline + toast helped, but primary CTA was generic “提交,” and reply text alone did not always read as a **business submission**.
2. **Obvious what was received?** **Weak at handoff:** progress card hid after `handoff_ready`; customer relied on scrolling chat.
3. **Complete enough?** Pre-handoff OK via tags; **post-handoff** same signal missing.
4. **Office handoff real vs chat-like?** Medium—strong boundary copy, but timing was vague (“尽快”).
5. **Follow-up timing clear?** **Weak**—no business-day framing.
6. **Weakest trust pillar:** **Confirmation at closure** > office timing > submission CTA label.

**Biggest weaknesses:** (a) confirmation at handoff, (b) office-wait realism, (c) first-turn submission wording.  
**Safest high-value fix:** Re-show triage snapshot on closure card + config-driven timing + tighten handoff phrase + Add-Car submit label.

## 4. Design options

- **A — Stronger closure only:** Single dense card. **Cons:** reply digest competes with structure.
- **B — Confirmation + office banner (chosen):** Snapshot block + timing `Alert` + existing reply digest. **Pros:** clarity, low risk, matches “intake form + office queue” mental model.
- **C — Stepper UI:** **Cons:** extra chrome, no new server truth.

**Winner:** **Option B** — best clarity / implementation risk tradeoff.

## 5. Founder scenario pack

- **6** automated scenarios in `founder_scenario_pack.json` (+ 8 narrative checks in markdown).
- Covers: clean handoff, partial→complete, correction, materials-sent, delivery-only path, formal wording in draft.
- **Useful** because it locks **handoff_ready**, **collected_fields**, and **draft substrings** without LLM.

## 6. Iteration loop 1

- **Designed** options A/B/C; **chose** B in `04_CUSTOMER_UX_OPTIONS_SPEC.md`.
- **Worth it:** Yes—prevented stepper overbuild and avoided duplicating all content into the reply card.

## 7. Iteration loop 2

- **Changed:**  
  - `UnifiedIntakePage.tsx` — Add-Car closure: **received snapshot** (quote readiness, collected/needed tags, optional human-confirmation note), **office timing** info banner, first-turn **提交加车请求** when intent is add-car.  
  - `configs/clients/chen_kui/ui_copy.json` — new copy keys + tightened transaction subtitle, processing line, toast.  
  - `configs/clients/chen_kui/handoff_phrases.json` — add-car **正式提交** + business-day caveat.  
  - `config_loader.py` — whitelist new `ui_copy` keys.  
  - `ui/src/api/clientConfig.ts` — types + defaults.  
  - `scripts/run_add_car_submission_confirmation_sprint_scenarios.py` — pack runner.
- **Why:** Close the gap where confirmation disappeared at the most important moment; make timing **believable** without fake precision.
- **Business clarity improved:** Customer sees **the same structured receipt** brokers infer; office wait is **explicitly time-bounded in business days**.
- **Worth it:** Yes.

## 8. Iteration loop 3

- **Tested:** `scripts/run_add_car_submission_confirmation_sprint_scenarios.py` (6/6), `scripts/test_client_aware_handoff.py --direct`, `bash scripts/guardrail_inbox_triage.sh`, `cd ui && npm run build`.
- **Improved:** Formal intake feel, closure confirmation, timing copy, Add-Car submit CTA; all guardrails green.
- **Still weak:** Snapshot shows **field presence**, not parsed values (by design, no OCR). **Materials-sent** branch keeps a different handoff sentence (still operational; slightly less “正式” than default add-car line).
- **More like formal request?** Yes, materially.
- **Worth it:** Yes.

## 9. Optional loop 4

- **Not used.** Unifying materials-sent handoff wording with “正式提交” would be cosmetic and risks lengthening or conflicting with the reassurance-first pattern already tuned in `triage.py`.

## 10. Validation summary

| Check | Result |
|--------|--------|
| Sprint scenario runner | PASS (6/6) |
| Client-aware handoff | PASS |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` | PASS |
| API test on :8001 | SKIP (no server) |

## 11. Deployment / release judgment

- **Backend:** Config and phrase files changed (`handoff_phrases.json`, `ui_copy.json`, `config_loader.py`). **Redeploy or restart** any API process that serves `/api/inbox/client-config` and loads triage config from disk so customers get new drafts and UI copy.
- **Frontend:** `UnifiedIntakePage.tsx` and `clientConfig.ts` changed. **Rebuild and redeploy** the UI bundle for customer entry.
- **Live inspect:** After deploy, Andy can verify in Unified Intake (Add-Car → handoff) without code changes.

*This run did not execute a cloud deploy (no remote target in scope); validation was local.*

## 12. Rule-brain / product-surface summary

| Concern | Where |
|---------|--------|
| When handoff fires, collected/still_needed/quote_ready | `services/fiqa_api/inbox_triage/triage.py` |
| Handoff **customer reply** text (`client_reply_draft` at handoff) | Phrase merge in `triage.py` + `configs/clients/chen_kui/handoff_phrases.json` |
| Customer **ribbon / closure / snapshot / timing / CTA** strings | `configs/clients/chen_kui/ui_copy.json` (served via `get_ui_copy` → `ClientConfigContext`) |
| Customer **UI assembly** | `ui/src/pages/UnifiedIntakePage.tsx` (progress card pre-handoff; closure card post-handoff) |
| API whitelist for new copy keys | `services/fiqa_api/inbox_triage/config_loader.py` |

**How the formal-intake feel is assembled:** Rules compute structure → backend selects handoff phrase → UI shows **headline + snapshot + timing banner + reply digest + boundary hint**, so the customer gets **record confirmation** and **office expectation** alongside the conversational line.

## 13. Final judgment

- **Biggest gain:** **Closure-time confirmation** aligned with broker-visible fields.
- **Biggest remaining weakness:** **Value-level** confirmation (showing exact VIN text, etc.) still out of scope; field tags only.
- **More formal intake?** Yes.
- **Best next step:** Optional English parity pass for new UI strings if English customer entry is prioritized; otherwise broker trial notes on whether timing copy should reference **California hours** explicitly.

## 14. 中文宏观总结

这轮把「加车」在 **提交完成那一瞬间** 的体验补齐：以前进度卡在手off后消失，客户只能靠聊天猜「你们到底记下了什么」。现在在结案卡里重新展示 **整理度 + 已记录项 + 可能还缺的项**，并加上 **工作日维度的跟进预期**，同时把手off话术改成 **正式提交办公室**，首屏在选加车意图时按钮改为 **提交加车请求**。整体上，「已提交 / 已收到 / 办公室在处理」三条线更清晰，客户和陈奎助手之间的信任链条更对齐业务现实。后续若要再磨，可以考虑是否在 **材料已发** 分支也统一「正式提交」措辞（要小心别变长或冲淡安抚语气），以及是否要英文界面同步这些结构化文案。

## 15. COPY/PASTE FOUNDER BLOCK

- **Submission / confirmation:** Handoff closure now includes a **structured “系统记录到的要点”** block (tags mirror triage); first Add-Car send CTA **提交加车请求**; handoff draft says **正式提交办公室**.
- **Office processing:** New **business-day timing** line (一至两个工作日，假期顺延) + processing line clarifies office will verify/price without asking customer to resend what’s already in-thread.
- **Biggest remaining weakness:** Tags are **presence-based**, not full value echo; **材料已发** handoff uses the existing shorter reassurance sentence.
- **Redeploy:** **Yes** — backend (config + triage loader) and frontend (UI bundle) if you want this live outside your dev machine.
- **Inspect now:** **Local yes** (build passes); **production** only after your usual deploy.

## 16. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车流程规则已强，但客户在「结束提交」时缺少 **结构化确认** 和 **可相信的等待预期**，容易退回「只是在聊天」的感觉。

### 主要用了什么方法/技术

文档驱动的选项比较（A/B/C）→ 在 `UnifiedIntakePage` 手off卡中增加 **确认快照 + 时间预期 Alert** → 更新 `ui_copy.json` / `handoff_phrases.json` → `config_loader` 白名单 → 自动化场景脚本 + 全量 `guardrail_inbox_triage.sh`。

### 这轮最大的提升

**手off瞬间** 重新展示与规则一致的 **已记录要点**，并用 **工作日跟进** 语言替代模糊的「尽快」。

### 现在还差什么

**字段值级** 的展示仍不做（避免 OCR/解析范围膨胀）；**材料已发** 分支话术与默认「正式提交」句式仍可择机统一。
