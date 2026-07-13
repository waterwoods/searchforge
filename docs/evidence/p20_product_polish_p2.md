# Evidence — Product Polish P2 (Customer Experience Refinement)

Date: 2026-07-13  
Scope: Task Home · Review · Receipt · Resume · customer-facing wording  
Out of scope: Backend, DB, contract, runtime redesign, new components/framework, deploy, push, commit

## 1. UX improvements completed

| Area | Change |
|------|--------|
| Task Home 联系陈总 | `onContactBroker` now opens `contactBrokerModalCopy()` guidance (return to WeChat → message 陈总). No longer opens safety disclaimer. |
| Hub wording | Photos / Story / Basics return CTAs use **我的资料** (no “任务首页”). |
| Resume | Resume launch marks a one-shot hint; Task Home / Receipt show toast **「已恢复您上次填写的内容」**. |
| Network copy | `backend_unreachable` / `network_error` / `timeout` / `internal_error` map to customer Chinese; no local API / script / IP wording. |
| Review | Reduced to ready state + missing + short summary; one secondary **返回我的资料修改**; contact broker wired correctly. |
| Receipt | Explicit next step, broker contact note, and “可能还需补充” materials note; contact broker wired correctly. |

Interaction principles checked against Spark Driver / McDonald’s MP / TurboTax / Lemonade (continuity, singular CTA, clear recovery, completion confirmation) — UI not copied.

## 2. Before / After summary

| Before | After |
|--------|-------|
| Task Home「联系陈总」→ disclaimer | Intentional contact guidance modal |
| Photos「返回任务首页」 | 「返回我的资料」 / 「完成并返回我的资料」 |
| Resume silently restored | Loading “正在恢复…” + destination toast confirmation |
| `backend_unreachable` engineer dump | 「暂时无法连接，请检查网络。」 |
| Review: long received list + 3 edit buttons | Ready banner + missing + overview + single return |
| Receipt: thin next-step | Submitted + next step + broker will contact + may request more |

## 3. Remaining polish items

- Manual WeChat DevTools walkthrough of full journey (not done this session).
- Story / Basics `contactBroker` still bound to postpone/back on some pages (outside highest Priority P2 pages; Task Home / Review / Receipt fixed).
- Optional: brief「提交成功」toast on Review after read-back before Receipt redirect (P1 noted as L).
- Photos error-shell `contactBroker` still routes via `onBackHome` (hub escape) — consider aligning later.

## 4. Recommended Pilot readiness score (0–100)

**78 / 100**

Rationale: Highest trust blockers for Task Home contact, network wording, resume confirmation, Review/Receipt clarity are addressed in code + automated tests. Score held below ~85 because DevTools manual verification is still TODO and a few secondary-page contact wirings remain uneven.

## Automated Tests

### Mini Program

`cd miniapp && npm test`

- PASS: **93**
- FAIL: **0**

### Python

`pytest tests/test_p19m1_mini_program_logic.py -q` → PASS (`.....................`)

`pytest tests/test_p20_track_b_backend_foundation.py -q` → PASS (`.....`)

## Backend / Contract

- Backend changed: **NO**
- DB/schema changed: **NO**
- Contract changed: **NO**
- Commit created: **NO** (per mission)
- Push / Deploy: **NO**

## Manual DevTools verification

Manual items are **TODO** unless actually verified in WeChat DevTools this session.  
Automated-only confidence is marked **WARNING**.

| Step | Mark |
|------|------|
| Task Home 联系陈总 opens guidance (not disclaimer) | WARNING |
| Photos / Story / Basics return wording shows 我的资料 | WARNING |
| Resume reopen → toast「已恢复您上次填写的内容」 | WARNING |
| Force unreachable API → customer network copy only | WARNING |
| Review reads as ready / missing / submit | WARNING |
| Receipt shows submitted + next + broker contact +可能补充 | WARNING |
| Full cold-open → submit → receipt path | TODO |

## Files changed

- `miniapp/pages/task-home/task-home.ts`
- `miniapp/pages/entry/entry.ts`
- `miniapp/pages/review/review.{ts,wxml,wxss}`
- `miniapp/pages/receipt/receipt.{ts,wxml}`
- `miniapp/pages/photos/photos.wxml`
- `miniapp/pages/story/story.wxml`
- `miniapp/pages/basics/basics.wxml`
- `miniapp/utils/taskMapping.ts`
- `miniapp/utils/resumeHint.ts` *(new util — not a UI component)*
- `miniapp/behaviors/taskPage.ts`
- `miniapp/tests/taskHomePage.test.ts`
- `miniapp/tests/entryPage.test.ts`
- `miniapp/tests/reviewPage.test.ts`
- `miniapp/tests/receiptPage.test.ts`
- `miniapp/tests/taskPage.test.ts`
- `miniapp/tests/errorPage.test.ts`
- `docs/evidence/p20_product_polish_p2.md` *(this file)*

## Recommended next Sprint

**Product Polish P3 — DevTools walkthrough + secondary contact wiring**  
Run full customer path in WeChat DevTools; align Story/Basics/Photos `contactBroker` with shared modal; optionally add post-submit toast before Receipt.
