# P20 Product Polish P1 — Entry / Error / Resume + UX Audit

| Field | Value |
|-------|-------|
| **Date** | 2026-07-14 |
| **Sprint** | Product Polish P1 |
| **Scope** | Polish `pages/entry`, `pages/error`; audit full customer journey UX |
| **Out of scope** | Backend, contract, new components, TDesign, deploy |

## Principles (benchmarks only — do not copy UI)

Drawn from Spark Driver / McDonald's Mini Program / TurboTax / Lemonade / mature China insurance MPs:

1. Always show **where you are** and **what happens next**.
2. Loading must explain itself — never a bare spinner.
3. Primary CTA is singular and verb-led.
4. Recovery is obvious: retry when useful; contact when not.
5. Resume should feel continuous, not like restarting the app.
6. Success is confirmed by server truth, then clearly celebrated.
7. Wording is consistent across states (同一件事用同一句话).

---

## Code delivered this sprint

- Entry → `taskPage` + `TaskShell` (loading / blocking error / contact recovery).
- Error → `taskPage` + `TaskShell` + `TaskError` + `TaskCTA`.
- Shared contact copy via `contactBrokerModalCopy()`.
- Resume-aware Entry loading: “正在恢复您上次填写的资料…”.
- Retryable vs non-retryable error split (`token_missing` / expired link → contact; network → retry).
- Entry/Error unit tests added.

---

## Top 20 UX observations

### 1. Entry used a custom loading/error card, not Task Runtime chrome

**Current:** Plain loading text + ad-hoc error card + duplicated buttons.  
**Problem:** Feels like a different product from Story/Basics/Photos.  
**Suggested improvement:** Host Entry on `TaskShell` / `TaskError` (done in P1).  
**Priority:** H

### 2. Error page looked like a dead-end branded “出错了”

**Current:** Nav title “出错了”; raw card; redirect retry inconsistently.  
**Problem:** Alarm language + weaker recovery than Entry.  
**Suggested improvement:** Title “暂时无法继续”; `reLaunch` Entry; TaskCTA primary (done in P1).  
**Priority:** H

### 3. Contact-broker wording drifted across surfaces

**Current:** “返回微信联系陈总” / “联系陈总” / modal variants.  
**Problem:** Same action, three phrasings → eroded trust.  
**Suggested improvement:** One modal copy helper (done); align secondary buttons later to “联系陈总”.  
**Priority:** H

### 4. Missing/expired token still offered a hopeful Retry

**Current:** Retry always visible even when retry cannot help.  
**Problem:** False hope; loops back to same dead end.  
**Suggested improvement:** Non-retryable codes route to contact (done in P1).  
**Priority:** H

### 5. Resume loading used the same copy as cold open

**Current:** Always “正在打开您的资料…”.  
**Problem:** Returning user doesn’t get continuity signal (Spark/TurboTax style).  
**Suggested improvement:** Resume source → “正在恢复您上次填写的资料…” (done).  
**Priority:** M

### 6. Task Home “联系陈总” opens safety disclaimer instead of contact guidance

**Current:** `onContactBroker` → `onShowDisclaimer`.  
**Problem:** User asking for help gets legal copy.  
**Suggested improvement:** Use `contactBrokerModalCopy()` from Entry/Error.  
**Priority:** H

### 7. Return CTAs: “返回任务首页” vs “返回我的资料”

**Current:** Photos uses “任务首页”; Receipt uses “我的资料”.  
**Problem:** Inconsistent mental model for the hub page.  
**Suggested improvement:** Standardize on **返回我的资料** everywhere.  
**Priority:** M

### 8. Secondary postpone: “稍后再填” only on Story/Basics

**Current:** Photos uses “返回任务首页”; Review has edit links.  
**Problem:** OK functionally, but postpone verb not shared where deferral exists.  
**Suggested improvement:** Keep “稍后再填” for incomplete section exits; hub return uses hub wording (see #7).  
**Priority:** L

### 9. Success toast language is thin vs confirmation screens

**Current:** Story/Basics “已保存”; Photos “上传成功”; Review jumps to Receipt.  
**Problem:** Fine at step level, but Review could briefly acknowledge before redirect.  
**Suggested improvement:** Optional brief “提交成功” toast only after read-back, before Receipt.  
**Priority:** L

### 10. Loading messages are good per page but lengths/tone vary

**Current:** “正在加载事故经过…” vs “正在加载当前任务和资料状态…”.  
**Problem:** Uneven verbal density; hub message feels internal.  
**Suggested improvement:** Short template: `正在加载{section}…` (Hub → `正在加载资料进度…`).  
**Priority:** M

### 11. Disabled CTA reasons are excellent on Review, sparse elsewhere

**Current:** Review shows why submit is blocked; Story/Basics rely on toast after tap.  
**Problem:** TurboTax-style “why can’t I continue?” missing on section pages.  
**Suggested improvement:** Surface disabledReason when validation fails preemptively (length/required).  
**Priority:** M

### 12. Photos primary CTA flips between “上传下一张” and “完成并返回…”

**Current:** Conditional primary based on count.  
**Problem:** Good progressive disclosure; label “任务首页” still mismatch (#7).  
**Suggested improvement:** Keep flip; rename completion CTA to hub standard.  
**Priority:** M

### 13. Supplement after submit is easy to miss

**Current:** Receipt shows secondary “继续补充照片” when allowed.  
**Problem:** Next-step text and supplement button can disagree in emphasis.  
**Suggested improvement:** If supplement required, promote next-step copy to mention photos explicitly.  
**Priority:** M

### 14. Navigation stack: mix of `navigateTo` / `navigateBack` / `redirectTo` / `reLaunch`

**Current:** Hub spoke navigateTo; Entry reLaunch; Receipt redirectTo hub.  
**Problem:** Mostly correct; Error used redirectTo (weaker stack clear than reLaunch).  
**Suggested improvement:** Entry/Error recovery always `reLaunch` (Error done); document matrix for engineers.  
**Priority:** M

### 15. App `pages/error` is rarely routed — recovery lives mostly on Entry/shell

**Current:** Error page exists; journey often stays on page TaskError.  
**Problem:** Orphan surface creates dual recovery metaphors.  
**Suggested improvement:** Keep Error as thin host (done); prefer in-page TaskError; only deep-link Error for fatal codes.  
**Priority:** L

### 16. Safety / disclaimer appears both as footer and tappable disclaimer

**Current:** Task Home duplicate safety copy (card footer + disclaimer line).  
**Problem:** Lemonade-like clarity diluted by repetition.  
**Suggested improvement:** One safety placement (shell footer OR disclaimer tap — not both as long text).  
**Priority:** L

### 17. Review edit escapes (“修改…”) compete with primary Submit

**Current:** Three secondary edit buttons under primary.  
**Problem:** Visual noise before submit (McD Mini keeps one secondary).  
**Suggested improvement:** Collapse edits into “修改资料” that returns to Task Home, or inline link row.  
**Priority:** M

### 18. Resume after kill: Entry → Receipt if submitted, else Task Home

**Current:** Logic correct; no toast explaining where you landed.  
**Problem:** Silent routing can confuse (“why am I on result page?”).  
**Suggested improvement:** One-time toast: “已恢复上次提交结果” / “已恢复未完成的资料”.  
**Priority:** M

### 19. Broker-unreachable copy is engineer-facing in `backend_unreachable`

**Current:** Mentions `run_demo_local.sh` and LAN IP.  
**Problem:** Fine for prototype/DevTools; wrong for customer/trial.  
**Suggested improvement:** Customer-safe message + hide script hints behind `prototypeMode`.  
**Priority:** H

### 20. Progress reality: total/completed numbers can feel artificial on Task Home

**Current:** Contract or legacy progress shown prominently.  
**Problem:** If numbers jump odd ways, trust drops (insurance MP trap).  
**Suggested improvement:** Prefer qualitative status (“还差照片”) when progress math is prototype-rough.  
**Priority:** L

---

## High-priority backlog (not all shipped in P1)

| # | Item | Status |
|---|------|--------|
| 1 | Entry Task Runtime | Done |
| 2 | Error Task Runtime | Done |
| 3 | Contact copy helper | Done |
| 4 | Non-retryable Entry/Error codes | Done |
| 6 | Task Home contactBroker misuse | **TODO** |
| 19 | Customer-safe backend_unreachable | **TODO** |
| 7/12 | Unify return CTA wording | **TODO** |
| 18 | Resume landing toast | **TODO** |

---

## Recommended next Sprint

**Polish P2 — Hub/CTA consistency:** fix Task Home contactBroker, standardize “返回我的资料”, customer-safe network copy behind prototypeMode, resume landing toast, Review edit declutter.
