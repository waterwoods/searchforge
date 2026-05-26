# Add-Car Post-Handoff Hard Boundary Sprint Report

## 1. Sprint theme

- **Evaluated / fixed:** Post-handoff Add-Car customer experience (closure clarity, same-request vs new-issue separation, broker-visible boundaries) and append rule brain (premium/renewal as cross-issue from add-car).
- **Why now:** Add-Car quality upstream was strong; the remaining maturity gap was **thread soup after handoff**—customers had no first-class “same ticket” lane on the customer entry screen, and 续保 pivots were under-detected vs claim/账单/删车.

## 2. Document set created

| Doc | Path |
|-----|------|
| Blueprint | `docs/sprints/ADD_CAR_POST_HANDOFF_HARD_BOUNDARY/POST_HANDOFF_HARD_BOUNDARY_BLUEPRINT.md` |
| Same vs new spec | `.../SAME_CASE_VS_NEW_ISSUE_AFTER_HANDOFF_SPEC.md` |
| Customer UX spec | `.../CUSTOMER_POST_HANDOFF_UX_SPEC.md` |
| Broker workbench spec | `.../BROKER_WORKBENCH_BOUNDARY_CLEANLINESS_SPEC.md` |
| Scenario pack (index) | `.../BOUNDARY_SCENARIO_PACK.md` |
| Execution outline | `.../EXECUTION_OUTLINE.md` |
| Acceptance criteria | `.../ACCEPTANCE_CRITERIA.md` |
| Founder inspection | `.../FOUNDER_INSPECTION_NOTES.md` |
| Scenario data | `configs/case_boundary_append_scenarios.json` |
| Runner | `scripts/run_case_boundary_battery.py` |

## 3. Baseline audit

- **Biggest post-handoff boundary weakness:** Customer entry **hid** the composer after handoff with only “提交新问题”—no **structured same-request append**, so real users either started over or relied on the workbench only.
- **Biggest broker cleanliness risk:** Follow-ups that **look like a new ticket** but land on the same `case_id` without obvious UI differentiation (partially mitigated before by `case_boundary`; list cards still said generic “已更新”).
- **Biggest customer confusion risk:** **续保/保费** after Add-Car handoff was easy to treat as “still quoting” because **premium** was not in the add-car cross-domain set.
- **Safest high-value fix:** Reuse existing `append-message` API on the closure card behind a collapsed “same record” lane + tighten **premium** boundary + strengthen reroute copy.

## 4. Scenario battery overview

- **Count:** **23** append scenarios (was 18; added **CB-19–CB-23** for post-handoff 续保、VIN 询问、混合账单、模糊 pivot、全险跟进).
- **Types:** same-case materials/corrections/quote follow-ups; new-issue 账单/理赔/删车/续保; borderline vague + office hours; mixed intent.
- **Use:** Regression lock for `triage_for_append` + customer/broker boundary semantics without LLM drift (`LLM_GENERATION_ENABLED=0`).

## 5. Iteration loop 1

- **Tested:** Baseline `run_case_boundary_battery.py` (18/18) + code read of customer closure vs workbench append.
- **Expected vs actual:** Baseline all **OK**; audit confirmed UX gap (no customer append lane) and premium cross-domain gap.
- **Weak / chatty:** Forced “new conversation only” felt **WeChat-thread**-like; backend already had boundary drafts but customer CTA did not reinforce **工单式** separation.
- **Worth it:** **Yes** — pinpointed two concrete fixes (UX lane + premium domain).

## 6. Iteration loop 2

- **Changed:**
  - `triage.py`: `_last_message_issue_domains` adds **premium**; add-car cross sets include **premium**; zh/en **new_issue** drafts include **续保** branch; add-car **portal suffix** mentions 「提交新问题」/ Start a new request; marker **不是这个加车**.
  - `UnifiedIntakePage.tsx`: handoff **status chip**; **Collapse** “同一服务记录” append calling `appendFollowUpMessage`; **提交新问题** as `primary ghost`; toasts for `new_issue` / `borderline`.
  - `ui_copy.json` + `config_loader.py` + `clientConfig.ts`: new strings for status, panel, placeholder, submit label; stronger `handoff_new_issue_hint`.
  - Workbench recent-case **追加** tags by `case_boundary`.
  - `case_boundary_append_scenarios.json`: **CB-19–CB-23**.
- **Why:** Highest ROI, lowest risk—no new persistence model; uses existing append route; rules-only tests stay stable.
- **Improved:** Clear **“已提交 · 处理中”** signal; explicit **same-ticket** lane; **续保** pivots become **new_issue**; customer drafts **tell users to open a new request** for unrelated items; brokers see **追加 · 疑似新事项** vs **同一条服务记录**.
- **Worth it:** **Yes.**

## 7. Iteration loop 3

- **Retested:** `bash scripts/guardrail_inbox_triage.sh` (**PASS**), `run_case_boundary_battery.py` (**23/23**), `run_add_car_transaction_clarity_scenarios.py` (**8/8**), `npm run build` (**OK**).
- **Improved:** End-to-end guardrails green with expanded boundary pack; UI compiles.
- **Still weak:** **Automatic case split** still does not exist—`new_issue` remains **one case** with broker confirmation; **borderline** still needs humans; customer append lane requires **`case_id`** (if case creation ever fails, lane hidden).
- **More bounded / mature:** **Yes** for founder demo and broker clarity, within MVP scope.
- **Worth it:** **Yes.**

## 8. Optional loop 4

- **Used:** **No.**
- **Reason:** Guardrails fully green; further gains (auto-split cases, richer LLM ranking) are **higher cost / scope creep** vs this sprint’s boundary MVP.

## 9. Validation summary

| Check | Result |
|-------|--------|
| `scripts/guardrail_inbox_triage.sh` | PASS |
| Case boundary battery | 23/23 |
| Add-car transaction clarity | 8/8 |
| `cd ui && npm run build` | Success |
| API test on :8001 | SKIPPED (no server) |

## 10. Deployment / release judgment

- **Backend:** **Redeploy required** (`triage.py`, `config_loader.py` copy whitelist). Not run from this environment (no production deploy executed).
- **Frontend:** **Redeploy / rebuild static assets required** (`UnifiedIntakePage.tsx`, `clientConfig.ts`).
- **Founder can inspect locally:** **Yes** after `bash scripts/run_demo_local.sh` (or your usual stack) with this branch.

## 11. Rule-brain / product-boundary summary

| Concern | Location |
|---------|----------|
| Same vs new vs borderline | `services/fiqa_api/inbox_triage/triage.py` — `_classify_append_case_boundary`, `_apply_append_case_boundary`, `triage_for_append` |
| Append persistence | `services/fiqa_api/inbox_triage/case_store.py` — `append_follow_up_message` |
| API | `POST /api/inbox/cases/{case_id}/append-message` — `routes/inbox_triage.py` |
| Customer closure + same-lane UI | `ui/src/pages/UnifiedIntakePage.tsx` |
| Customer copy | `configs/clients/chen_kui/ui_copy.json` (+ defaults in `ui/src/api/clientConfig.ts`) |
| Broker list tags | `UnifiedIntakePage.tsx` recent-case renderer |
| **Rule-based enough** | Materials, clear pivots (claim/billing/remove/premium), second vehicle, quote follow-ups |
| **Human confirmation better** | Vague pivots, office hours on quote thread, “另一个保险问题” without domain |
| **Future LLM assist** | Subtle mixed-intent ranking, auto-split suggestions (not implemented) |

## 12. Final judgment

- **Biggest gain:** **Customer-visible “closed ticket + optional same-lane append”** plus **premium/renewal** treated as **cross-issue** from Add-Car.
- **Biggest remaining weakness:** **No hard case fork**—`new_issue` still shares one `case_id` until broker acts.
- **Mature portal after handoff:** **Closer**—especially when `case_id` exists; still MVP, not enterprise ticketing.
- **Best next step:** Optional **server-driven “suggested: open new request”** banner when `case_boundary=new_issue` is returned to the customer append lane (if product wants even stronger separation without true split).

## 13. 中文宏观总结

这轮把 **加车已经交办公室之后** 的客户体验，从「只能重新开始聊天」推进到更像 **工单/服务单**：有明确 **“已提交 · 处理中”**，并用折叠面板提供 **“同一服务记录追加”**（更正、补 VIN/截图等），同时把 **续保/保费** 从加车线程里更干净地划到 **新事项** 规则里。客户侧 **新事项** 的自动回复会 **提醒用「提交新问题」**，经纪人侧列表会出现 **追加 · 疑似新事项 / 同一条服务记录** 的标签。自动拆 case 仍未做，边界模糊时仍依赖人工确认。

## 14. COPY/PASTE FOUNDER BLOCK

- **Biggest post-handoff boundary improvement:** Customer closure shows **处理中状态** + optional **same-case append** lane (uses existing append API).
- **Biggest reroute improvement:** **续保/保费** pivots classify as **new_issue**; zh drafts add **「提交新问题」** suffix for add-car-originated threads; **提交新问题** button promoted (ghost primary).
- **Biggest remaining weakness:** **No automatic new `case_id`** for clear new issues—still one record until broker splits manually.
- **Redeploy needed:** **Yes** — backend + frontend both changed.
- **Andy can inspect now:** **Yes locally** after running the usual demo stack; production requires deploy.

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车资料齐并移交办公室后，入口仍像「同一串微信」，缺少 **已结案/处理中** 的边界感，也缺少 **同一工单内补充** 与 **新工单分流** 的对照。

### 主要用了什么方法/技术

文档化蓝图 + 扩展现有 **`triage_for_append` 规则** + **`configs/case_boundary_append_scenarios.json` 电池** + 客户入口 **Ant Design Collapse** 调用既有 **`append-message` API** + 全仓 **`guardrail_inbox_triage.sh`** 回归。

### 这轮最大的提升

**客户侧**有明确的处理中状态与「同一服务记录」补充通道；**规则侧**把 **续保** 从加车后续消息里更稳定地判为 **新事项**，并在回复里 **强提示「提交新问题」**；**经纪人侧**追加消息标签更可读。

### 现在还差什么

**真正拆 case / 自动开新工单** 仍未实现；模糊话题仍建议 **人工确认**；若未生成 `case_id`，客户侧补充面板不会出现。
