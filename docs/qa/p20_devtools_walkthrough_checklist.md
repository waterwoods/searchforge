# P20 DevTools Walkthrough Checklist — First Complete Manual QA

**Sprint:** P20 Stabilization & Freeze (checklist still binds human DevTools)  
**Date:** 2026-07-13  
**Scope:** Manual WeChat DevTools QA only. Do not mark PASS from automated tests alone.  
**Leave all PASS rows unchecked until a human verifier completes that row in DevTools.**  
**Freeze note (2026-07-13):** Gate1/Gate2 automated PASS; Gate3 (G3) and journey rows remain unchecked — see `docs/evidence/p20_stabilization_freeze_2026_07_13.md`.

---

## Pre-flight (before Entry)

| # | Check | Notes / expected | PASS |
|---|-------|------------------|------|
| P1 | Local API running on expected base URL | `bash scripts/run_demo_local.sh` → `curl http://127.0.0.1:8001/healthz` OK | □ |
| P2 | Fresh QA token minted | `PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --cloud-sql --api-base http://127.0.0.1:8001` | □ |
| P3 | WeChat DevTools open on `miniapp/` | Tourist AppID OK | □ |
| P4 | 不校验合法域名 enabled | Required for localhost / LAN HTTP | □ |
| P5 | Launch mode has `token=h5t1…` (or `devTaskToken`) | Cold open uses this token | □ |
| P6 | Screenshot folder ready | Attach to bug records if FAIL | □ |

---

## Journey map

```
Entry → Task Home → Story → Basics → Photos → Review → Receipt
         ↑_______________________________________________|
                         resume / return hub
```

Reference nav titles (from page JSON):

| Page | Nav title |
|------|-----------|
| Entry | 事故资料 |
| Task Home | 事故资料 |
| Story | 事故经过 |
| Basics | 基本资料 |
| Photos | 事故照片 |
| Review | 检查资料 |
| Receipt | 提交结果 |
| Error (edge) | 暂时无法继续 |

---

## 1. Entry

**Expected:** Loading shell opens task; success navigates to Task Home (or Receipt if already submitted). Failure shows recoverable or contact-broker error — never blank forever.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| E1 | Page opens correctly | Entry mounts; no white screen / crash | □ |
| E2 | Title correct | Nav: **事故资料** | □ |
| E3 | Instruction understandable | Loading copy clear (e.g. 「正在打开您的资料…」 / resume 「正在恢复…」) | □ |
| E4 | Primary CTA | Healthy path auto-continues; on error, primary is Retry / reopen path | □ |
| E5 | Secondary action | On recoverable failure, customer can reach 联系陈总 | □ |
| E6 | Loading state | Shell shows loading; busy clears after success or failure | □ |
| E7 | Retry state | Retry after transient failure re-opens task (bounded; cooldown toast if spam) | □ |
| E8 | Contact Broker | Modal title **联系陈总**; guidance to return to WeChat and message 陈总 | □ |
| E9 | Resume | Relaunch with saved resume token → restore loading → Task Home or Receipt + resume toast | □ |
| E10 | Error handling | Missing/expired token → non-retryable Chinese copy; network → retryable Chinese copy (no IP/script dump) | □ |
| E11 | Navigation | Success → `task-home` (or `receipt` if submitted) | □ |
| E12 | Return path | No dead end: Retry and/or 联系陈总 always available on failure | □ |
| E13 | Success feedback | Arrives on Task Home / Receipt without silent hang | □ |

---

## 2. Task Home

**Expected:** Hub titled **我的事故资料** (card), progress + status + next action, single primary CTA, secondary「查看全部资料」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| H1 | Page opens correctly | Hub content visible after load | □ |
| H2 | Title correct | Nav **事故资料**; card title **我的事故资料** (or contract title) | □ |
| H3 | Instruction understandable | Status + next-action instruction readable; missing items sensibly labeled | □ |
| H4 | Primary CTA | Submitted state primary CTA is **补充或修改资料** only; tap opens unified action sheet (修改事故经过/修改基本资料/修改车辆及对方信息/补充照片) | □ |
| H5 | Secondary action | Submitted state shows only one secondary action: **查看提交结果** (no duplicate 「继续补充资料」/「继续补充照片」 buttons on Task Home) | □ |
| H6 | Loading state | 「正在加载我的资料…」 then content; CTA not stuck spinning | □ |
| H7 | Retry state | Inject load fail → inline/blocking error + **重试** works | □ |
| H8 | Contact Broker | On error chrome: **联系陈总** modal (not safety disclaimer). Note: healthy hub may lack always-visible contact — record if absent | □ |
| H9 | Resume | Kill/reopen → toast **已恢复您上次填写的内容** (once) | □ |
| H10 | Error handling | Customer-safe mapped message only | □ |
| H11 | Navigation | Primary CTA routes to Story / Basics / Photos / Review / Receipt correctly. Submitted + missing → first missing page; submitted + no missing → Receipt | □ |
| H12 | Return path | Section pages return here; footer CTA remains usable; after supplement save, hub refreshes and drops resolved missing items | □ |
| H13 | Success feedback | Progress / received / missing update after section save or photo upload | □ |
| H14 | Post-submit supplement (no dead end) | After submit: unified CTA「补充或修改资料」always opens actionable edit sheet; no inert Review dead-end; formal re-submit stays blocked | □ |
| H15 | No duplicate post-submit CTAs | Task Home submitted footer has one primary + one secondary only (no overlapping supplement/photo CTAs) | □ |

---

## 3. Story

**Expected:** Title「请简单说一下发生了什么」; primary「保存并返回我的资料」; secondary「稍后再填」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| S1 | Page opens correctly | Textarea and CTAs visible | □ |
| S2 | Title correct | Nav **事故经过**; card title **请简单说一下发生了什么** | □ |
| S3 | Instruction understandable | Subtitle example + placeholder understandable | □ |
| S4 | Primary CTA | **保存并返回我的资料** — saves, toast **已保存**, returns to hub | □ |
| S5 | Secondary action | **稍后再填** returns hub without requiring save | □ |
| S6 | Loading state | 「正在加载事故经过…」; saving shows CTA loading | □ |
| S7 | Retry state | Save/network fail → error + retry / contact; typed text preserved | □ |
| S8 | Contact Broker | Error path **联系陈总** → shared guidance modal (not postpone) | □ |
| S9 | Resume | Leave mid-edit → reopen Task Home → Story recovers server or local expectation clearly | □ |
| S10 | Error handling | Too-short story blocked client-side; API fail mapped Chinese | □ |
| S11 | Navigation | Save success → Task Home | □ |
| S12 | Return path | 稍后再填 / back → hub; no stuck saving | □ |
| S13 | Success feedback | Toast **已保存**; hub reflects story complete | □ |

---

## 4. Basics

**Expected:** Title「补充基本资料」; injury / police choices; datetime / location / vehicle; primary「保存并返回我的资料」; secondary「稍后再填」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| B1 | Page opens correctly | All fields visible | □ |
| B2 | Title correct | Nav **基本资料**; card **补充基本资料** | □ |
| B3 | Instruction understandable | Subtitle「这些信息帮助陈总快速了解情况。」 | □ |
| B4 | Primary CTA | **保存并返回我的资料** after required fields | □ |
| B5 | Secondary action | **稍后再填** → hub | □ |
| B6 | Loading state | 「正在加载基本资料…」; save busy disables CTA / secondary | □ |
| B7 | Retry state | Mid-save / patch fail → message + retry path; values preserved | □ |
| B8 | Contact Broker | Error **联系陈总** → shared modal | □ |
| B9 | Resume | Prefill from server on reopen | □ |
| B10 | Error handling | Empty required → field toasts; customer-safe save errors | □ |
| B11 | Navigation | Success → Task Home | □ |
| B12 | Return path | 稍后再填 / save-and-return both exit cleanly | □ |
| B13 | Success feedback | Toast **已保存**; hub missing list updates | □ |
| B14 | Post-submit supplement save | Submitted case进入 Basics 后保存成功（非 409）；回到 Hub/Review 后缺失项刷新 | □ |

---

## 5. Photos

**Expected:** Title「补充事故照片」; upload to target count; primary「上传下一张」then「完成并返回我的资料」; secondary「返回我的资料」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| PH1 | Page opens correctly | Slots + copy visible | □ |
| PH2 | Title correct | Nav **事故照片**; card **补充事故照片** | □ |
| PH3 | Instruction understandable | Count「已上传 N/M 张」and required-first guidance clear | □ |
| PH4 | Primary CTA | **上传下一张** until complete; then **完成并返回我的资料** | □ |
| PH5 | Secondary action | **返回我的资料** (hub escape; wording differs from Story/Basics「稍后再填」— acceptable if intentional) | □ |
| PH6 | Loading state | 「正在加载照片资料…」; upload busy disables add / CTA | □ |
| PH7 | Retry state | Failed slot **retry** reuses local image without re-pick | □ |
| PH8 | Contact Broker | Error **联系陈总** → shared modal (not hub escape) | □ |
| PH9 | Resume | Reopen shows server-confirmed slots; count matches hub | □ |
| PH10 | Error handling | Upload fail / unconfirmed → Chinese toast; no engineer dump | □ |
| PH11 | Navigation | Done → Task Home; preview works | □ |
| PH12 | Return path | Secondary return during incomplete upload leaves hub usable | □ |
| PH13 | Success feedback | Toast **上传成功**; count increments only after read-back | □ |

---

## 6. Review

**Expected:** Title「请确认资料」; ready / missing summary; primary「提交给陈总审核」; when missing Basics fields, recovery CTA「去补充基本资料」+ tappable missing rows; escape「返回我的资料」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| R1 | Page opens correctly | Summary card loads | □ |
| R2 | Title correct | Nav **检查资料**; card **请确认资料** | □ |
| R3 | Instruction understandable | Ready label + summary (齐全 / 还需补充) clear | □ |
| R4 | Primary CTA | **提交给陈总审核** enabled only when ready; disabled reason when not | □ |
| R5 | Secondary action | When missing Basic fields: **去补充基本资料** → Basics. Escape **返回我的资料** → hub (does not submit). Hub escape must not be the only recovery path | □ |
| R5a | Missing-item edit path | Missing rows such as **是否有人受伤** / **是否报警** are tappable → Basics. Multiple Basics items share one recovery CTA (no duplicate competing buttons) | □ |
| R5b | Post-submit on Review | If customer lands on Review after submit with missing items: rows + supplement CTA still actionable; primary submit stays disabled (「资料已提交，无需重复提交」); no dead end | □ |
| R6 | Loading state | 「正在加载提交前检查…」; submit shows CTA loading | □ |
| R7 | Retry state | Submit fail stays on Review; retry / contact available | □ |
| R8 | Contact Broker | Error **联系陈总** → shared modal | □ |
| R9 | Resume | Incomplete journey cannot fake-submit; submitted state routes away sensibly | □ |
| R10 | Error handling | Not-ready tap explains; submit fail Chinese only; duplicate submit blocked | □ |
| R11 | Navigation | Success after read-back → Receipt only; supplement → Basics | □ |
| R12 | Return path | Basics save → back to Review via stack / hub; Review `onShow` refreshes and clears resolved missing items; no double-submit | □ |
| R13 | Success feedback | Toast **提交成功** then Receipt | □ |

---

## 7. Receipt

**Expected:** Success status「资料已提交」; next step; broker contact note; possible supplement; primary「返回我的资料」; optional「继续补充照片」.

| # | Check | Expected | PASS |
|---|-------|----------|------|
| RC1 | Page opens correctly | Status pill + title visible | □ |
| RC2 | Title correct | Nav **提交结果**; title **资料已提交** (or contract) | □ |
| RC3 | Instruction understandable | Message + **下一步** + **陈总会联系您** + **可能还需补充** | □ |
| RC4 | Primary CTA | Submitted state primary CTA is **补充或修改资料** and opens same unified action sheet as Task Home | □ |
| RC5 | Secondary action | Submitted state shows one secondary action **查看全部资料** | □ |
| RC6 | Loading state | 「正在加载提交结果…」 then clear | □ |
| RC7 | Retry state | Load fail → retry / contact | □ |
| RC8 | Contact Broker | Error **联系陈总** → shared modal | □ |
| RC9 | Resume | Kill/reopen submitted task → Receipt (not new claim); resume toast once | □ |
| RC10 | Error handling | Customer-safe messages only | □ |
| RC11 | Navigation | Unified supplement action routes to Story/Basics/Vehicle(Basics)/Photos correctly; secondary「查看全部资料」does not submit | □ |
| RC12 | Return path | Hub shows submitted / status coherent with Receipt | □ |
| RC13 | Success feedback | Clear submitted confirmation (pill / title / time) | □ |

---

## Edge scenarios (must run once)

| # | Scenario | Steps | Expected | PASS |
|---|----------|-------|----------|------|
| X1 | Full cold journey | Entry → … → Receipt | Every page checklist above | □ |
| X2 | Resume mid-task | Partial fill → kill → reopen | Toast + correct hub next action | □ |
| X3 | Resume after submit | From Receipt kill → reopen | Receipt, no duplicate claim | □ |
| X3a | Post-submit unified supplement routing | Submitted task → Task Home「补充或修改资料」| Action sheet routes to Story/Basics/Vehicle(Basics)/Photos; save refreshes status; re-submit blocked | □ |
| X3b | Post-submit supplement persistence/audit | Submitted task修改 Story/Basics 并保存 | 保存成功；任务仍 submitted；无第二次 formal submit；Broker 侧可见补充时间线（before/after） | □ |
| X4 | Network fail | Point `apiBaseUrl` unreachable or offline | Chinese network copy + Retry + 联系陈总 | □ |
| X5 | Expired / invalid token | Bad or expired `h5t1` | Non-retryable; contact path; no hopeful loop | □ |
| X6 | Double-tap CTA | Mash primary on save/submit/nav | Single navigation / single submit | □ |
| X7 | Workbench readback | Find case by QA label | Broker sees injury/police/photos + 我方车辆 + 对方车牌 + 对方信息 + supplement timeline | □ |

---

## Component Three Gates (pre-commit + pre-upload)

| # | Gate | Expected | PASS |
|---|------|----------|------|
| G1 | File completeness | Every component has `index.ts/json/wxml/wxss`; `index.json` contains `"component": true` | □ |
| G2 | Path validation | `usingComponents` paths exist, casing matches, required files exist, untracked components reviewed by validator | □ |
| G3 | Real DevTools compile | Cache cleared + full compile; no `component not found`; no `module ... is not defined` | □ |

---

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Executor | | | PASS / FAIL / BLOCKED |
| Reviewer | | | |

**Evidence:** Attach screenshots per FAIL to `docs/qa/p20_bug_record_template.md` rows. Update `docs/qa/p20_pilot_blockers.md` Status fields when confirmed.

**Related:** Pilot readiness score lives in [`p20_pilot_blockers.md`](./p20_pilot_blockers.md#pilot-readiness-score).
