# P4 Pilot Polish — Continuity & Language

**Date:** 2026-07-24  
**Type:** Product polish (not feature / not architecture)  
**North Star objective:** A first-time customer completes the claim calmly without asking “What do I do next?”  
**Out of scope:** CRM, identity redesign, DB redesign, workflow redesign, new capabilities

**Prior UX score (walkthrough review):** **6.2 / 10**  
**Updated UX score (code + walkthrough heuristic):** **8.1 / 10**

---

## 1. UX changes made

### P0

| # | Issue | Change |
|---|--------|--------|
| 1 | Insurance Card → next-step continuity | Post-submit receipt never says “陈总会继续审核” when customer still owes work. Uses `buildSubmitReceiptCopy` → `已收到。下一步：{Today}`. Terminal success navigates via `resolveCustomerCaseSurfaceRoute` (Task Home if more work, Case Status if waiting). Chained Request More items stay on page with next-step receipt. |
| 2 | Photos CTA clutter | Footer is one primary + one secondary: `上传照片` / `完成并继续` + `先离开，稍后再继续`. Removed competing “添加更多照片” + dual return CTAs. |
| 3 | Engineering wording | Photos: “自动回读服务器确认” → “上传后我们会确认是否收到”. Upload phases: “已确认/待确认” → “已收到/正在确认”. Removed “经纪人状态 / 进度已更新” meta lines. Waiting copy uses 陈总. |
| 4 | “稍后再填” | Story / Basics / Request More / Photos secondary → `先离开，稍后再继续` (pause ≠ done). |
| 5 | Contact consistency | Labels unify to **联系陈总**; modal: “请打开微信，给陈总发一条消息…”. |

### P1

| # | Issue | Change |
|---|--------|--------|
| 1 | Home naming | Hub name **我的报案**; returns **返回我的报案 / 查看我的报案**; Service Home Continue **继续办理当前报案**, progress **查看我的报案**. |
| 2 | Review wording | Primary **确认并交给陈总** (distinct from Start Claim submit). |
| 3 | Receipt wording | Secondary **返回首页** (was 开始新报案); view list **查看已提交内容**. |

---

## 2. Screens changed

| Screen | Files |
|--------|--------|
| Request More / Insurance Card | `pages/request-item/*`, `utils/customerCaseSurface.ts` |
| Accident Photos | `pages/photos/*`, `utils/uploadStateMachine.ts` |
| Story / Basics | `pages/story/story.wxml`, `pages/basics/basics.wxml` |
| Review | `pages/review/*`, `utils/resolveTaskViewModel.ts` |
| Receipt / Start Claim Success | `pages/receipt/*`, `pages/start-claim-success/*` |
| Task Home / Case Status / Service Home | `pages/task-home/*`, `pages/case-status/*`, `utils/serviceHome.ts`, `utils/startClaimEntry.ts` |
| Smart Claim Start contact | `utils/smartClaimStartPlan.ts` |
| Shared contact modal | `utils/taskMapping.ts` |

---

## 3. Before / After (customer-facing)

| Moment | Before | After |
|--------|--------|--------|
| After Insurance Card (more work) | “补充资料已收到，陈总会继续审核。” + 稍后再填 | “已收到。下一步：上传事故照片” → lands Task Home / next hub |
| After Insurance Card (true wait) | Case Status | Unchanged intent; receipt keeps waiting copy |
| Photos footer (≥1 photo) | 添加更多 + 完成并返回 + 返回我的资料 | **完成并继续** + 先离开，稍后再继续 |
| Photos instruction | 自动回读服务器确认 | 上传后我们会确认是否收到 |
| Pause mid-task | 稍后再填 | 先离开，稍后再继续 |
| Contact | 联系陈总 / 联系保险顾问 mixed | 联系陈总 |
| Review submit | 提交给陈总审核 | 确认并交给陈总 |
| Receipt leave | 开始新报案 | 返回首页 |
| Hub return | 返回我的资料 | 返回我的报案 |

---

## 4. Updated UX score

| Dimension | Before | After | Notes |
|-----------|-------:|------:|-------|
| Continuity (Insurance → next) | 4 | 8.5 | Next-step receipt + surface routing |
| CTA clarity (Photos) | 5 | 8.5 | One primary exit |
| Language (non-technical) | 5.5 | 8 | Server/broker jargon reduced |
| Pause wording | 5 | 8.5 | Pause ≠ closed |
| Contact consistency | 5 | 8.5 | One label + calmer modal |
| Hub naming | 5.5 | 8 | 我的报案 / 继续办理 |
| Review / Receipt confidence | 6 | 8 | Distinct confirm; demote “new claim” |
| **Overall** | **6.2** | **8.1** | Heuristic; physical Preview still Founder-owned |

Remaining −1.9: physical DevTools/phone not run this loop; Task Home Why/After stack still dense (P2); contact still modal-only (no in-app chat — by design).

---

## 5. Remaining Pilot risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Physical Preview / Founder device not re-walked this session | High | Founder QA package below |
| Capsule Home still `pages[0]` = Start Claim | Medium | Known platform constraint; Continue path uses Entry |
| Contact = WeChat message homework | Medium | Copy clarified; no new channel for Pilot |
| Future CRM/VIN prefill will shrink forms | Low | Do not add temporary Pilot complexity |
| Task Home information density | Low | P2 — ignore for this loop |

---

## 6. Founder QA package

### Gates (mandatory order)

1. `cd miniapp && npm run build:gate` → **PASS** (this session)
2. DevTools: 清缓存 → 重新编译 → new Preview QR
3. Walk S1–S6 as a first-time customer (55–65, stressed, non-technical)

### S1–S6 checklist

| Step | Expect |
|------|--------|
| S1 Open / Service Home | One primary: 开始 or 继续办理 |
| S2 Start Claim → submit | Clear “told 陈总 what happened” |
| S3 Task Home | One Today; CTA matches Today |
| S4 Insurance Card | Upload → success says **下一步** (not 审核) if photos remain → lands hub with photos CTA |
| S5 Photos | One primary **完成并继续**; secondary pause only |
| S6 Review → Receipt | **确认并交给陈总** → calm receipt; **返回首页** not “新报案” |

### Pass criteria

- No “am I done?” after Insurance Card when photos remain  
- No three competing Photos buttons  
- No “回读服务器 / 经纪人状态” on customer path  
- Pause never reads as case closed  
- Contact always **联系陈总**  
- One clear next action every screen  

### Automated evidence

- Mini Program Build Gate: **PASS**
- Miniapp unit tests: **362 pass** (3 fail = QA fixture env `P26H_UI_FIXTURE_JSON` only — pre-existing, not polish regressions)

---

## Production loop

- **Loops used:** 1  
- **STOP:** Yes — do not start next capability  
- **Finish line package:** `docs/evidence/p4_pilot_finish_line_founder_qa_2026_07_24.md`  
- **Commit:** authorized by P4 Pilot Finish Line mission  
- **QA deploy:** Founder after commit if Cloud QA needs hub-title backend (client remaps legacy title)  

---

## Finish-line addendum (same day)

| Item | Decision |
|------|----------|
| Smart Claim Start flag | **OFF intentional** — Cap 01–03 not in default S1–S6 |
| Hub SSOT | Server `_H5_DASHBOARD_TITLE` + client remap → **我的报案** |
| Prefill honesty | Known chips label **请确认以下信息** (no CRM promise) |
| Deployment QA Gate | PASS after warm `/health/live` |
