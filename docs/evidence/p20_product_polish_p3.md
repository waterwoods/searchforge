# Evidence — Product Polish P3 (Complete DevTools Walkthrough & Pilot Alignment)

Date: 2026-07-13  
Scope: Entry → Task Home → Story → Basics → Photos → Review → Receipt  
Focus: Contact Broker · Resume · Error recovery · Navigation · CTA wording · Loading · Success feedback  
Out of scope: Backend, DB, contract, new components, runtime redesign, deploy, push, commit

## Overall status

**Code polish + consistency alignment COMPLETE.**  
**Manual WeChat DevTools cold-path walkthrough NOT executed this session** — checklist rows that require DevTools remain **TODO** / **WARNING** (never marked PASS without live verification).

---

## 1. Complete walkthrough checklist

Marks: **PASS** = verified in DevTools · **WARNING** = code/tests support OK, DevTools pending · **TODO** = not verified · **FIXED** = addressed in P3 code (automated only)

### Entry

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「事故资料」 | Clear hub open branding | WARNING |
| Instruction / loading | Cold「正在打开您的资料…」; resume「正在恢复您上次填写的资料…」 | Explain what is happening | WARNING |
| Primary CTA | Implicit progress via bootstrap → reLaunch hub/receipt | Auto-land correct destination | WARNING |
| Secondary / contact | `onContactBroker` → shared modal | Guidance, not disclaimer | WARNING |
| Loading | TaskShell loading clears after bootstrap | No endless spinner | WARNING |
| Retry | Retryable network; cooldown toast「请稍候再试」 | Bounded retry | WARNING |
| Resume | Marks restore hint; destination toast | Continuous restore feel | WARNING |
| Error | token_missing / expired → non-retryable + contact | No false Retry hope | WARNING |
| Completion | Lands Task Home or Receipt | Correct destination | WARNING |

### Task Home

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「事故资料」+ VM title | Know where you are | WARNING |
| Instruction | Status card + progress | Next step clear | WARNING |
| Primary CTA | Verb-led from VM | Singular next action | WARNING |
| Secondary | 「查看全部资料」modal | Safe overview | WARNING |
| Loading | 「正在加载我的资料…」 | Clears after load | WARNING |
| Retry | Bounded retryLoadTask | Recover then contact | WARNING |
| Resume toast | 「已恢复您上次填写的内容」 | Confirm restore | WARNING |
| Error | TaskError → retry + 联系陈总 | Customer-safe | WARNING |
| Contact on healthy UI | Only via error chrome | Want reachable help without failing first | TODO *(gap)* |
| Completion | CTA navigates to next section | Continuous task | WARNING |

### Story

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「事故经过」; card「请简单说一下发生了什么」 | Clear section | WARNING |
| Instruction | Example subtitle + placeholder | Know what to write | WARNING |
| Primary CTA | 「保存并返回我的资料」 | Verb + hub identity | WARNING |
| Secondary | 「稍后再填」 | Defer OK | WARNING |
| Loading | 「正在加载事故经过…」 | Explains itself | WARNING |
| Retry | onRetry → retryLoadTask | Recover | WARNING |
| Contact | **P3:** shared `contactBrokerModalCopy` (was `onLater`) | Contact ≠ postpone | FIXED → WARNING |
| Save success | Toast「已保存」+ back | Confirmed | WARNING |
| Save fail | Text kept; retryable error | Recoverable | WARNING |
| Completion | Return hub after read-back | Continuous | WARNING |

### Basics

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「基本资料」; card「补充基本资料」 | Clear | WARNING |
| Instruction | 「这些信息帮助陈总快速了解情况。」 | Purpose clear | WARNING |
| Primary CTA | 「保存并返回我的资料」 | Matches Story hub wording | WARNING |
| Secondary | 「稍后再填」 | Same defer verb as Story | WARNING |
| Loading | 「正在加载基本资料…」 | Clear | WARNING |
| Validation | Toasts for missing injury/police/time/vehicle | Friendly | WARNING |
| Contact | **P3:** shared modal (was `onLater`) | Contact ≠ postpone | FIXED → WARNING |
| Police mismatch | Customer message + 联系陈总 hint | No silent fail | WARNING |
| Success | 「已保存」after police read-back | Authoritative | WARNING |
| Completion | navigateBack hub | Continuous | WARNING |

### Photos

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「事故照片」; card「补充事故照片」 | Clear | WARNING |
| Instruction | Count + read-back note | Know required slots | WARNING |
| Primary CTA | 「上传下一张」 / 「完成并返回我的资料」 | Singular | WARNING |
| Secondary | 「返回我的资料」 | Hub wording identical | WARNING |
| Loading | 「正在加载照片资料…」 | Clear | WARNING |
| Upload progress | Slot percent | Visible | WARNING |
| Contact | **P3:** shared modal (was `onBackHome`) | Contact ≠ hub escape | FIXED → WARNING |
| Success | 「上传成功」only after read-back | No optimistic | WARNING |
| Retry | Slot retry without forced re-pick when local | Recover | WARNING |
| Completion | Done → back hub | Continuous | WARNING |

### Review

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「检查资料」;「请确认资料」 | Confirm step | WARNING |
| Instruction | ready / missing / overview | Ready vs not ready | WARNING |
| Primary CTA | 「提交给陈总审核」 | Verb-led | WARNING |
| Secondary | **P3:** 「返回我的资料」(was「…修改」) | Identical hub wording | FIXED → WARNING |
| Loading | 「正在加载提交前检查…」 | Clear | WARNING |
| Disabled reason | Under CTA when not ready | Explains why | WARNING |
| Duplicate submit | Busy guard | Blocked | WARNING |
| Success | **P3:** toast「提交成功」then Receipt | Feedback then next screen | FIXED → WARNING |
| Error | Customer mapErrorMessage + modal when missing | Friendly | WARNING |
| Contact | Shared modal | Consistent | WARNING |
| Completion | redirect Receipt after submitted read-back | Authoritative | WARNING |

### Receipt

| Check | Current | Expected | Mark |
|-------|---------|----------|------|
| Title | Nav「提交结果」;「资料已提交」 | Success obvious | WARNING |
| Instruction | message + next step | What happens next | WARNING |
| Primary CTA | 「返回我的资料」 | Identical hub wording | WARNING |
| Secondary | 「继续补充照片」when allowed | Recovery path | WARNING |
| Loading | 「正在加载提交结果…」 | Clears | WARNING |
| Resume toast | Same restore toast if resume → receipt | Consistent | WARNING |
| Contact | Shared modal | Consistent | WARNING |
| Broker note | Explicit 陈总会联系您 | Trust | WARNING |
| Materials note | 可能还需补充 | Expectation set | WARNING |
| Reload | Always re-fetch | No stale | WARNING |
| Completion | Submitted state felt final | Yes | WARNING |

### Cross-journey consistency

| Check | Mark |
|-------|------|
| 「联系陈总」→ same modal copy on Entry / Error / Task Home / Story / Basics / Photos / Review / Receipt | WARNING (code) |
| Hub return uses「我的资料」(not「任务首页」) | WARNING (code) |
| Resume toast identical | WARNING (code) |
| Loading indicators cleared by busy flags / TaskShell modes | WARNING (code) |
| Success feedback on save / upload / submit | WARNING (code) |
| Network/errors customer-safe Chinese (no IP / script / local API dump) | WARNING (code) |
| No intentional dead ends (retry or contact) | WARNING (code) |
| Full cold-open → submit → receipt in DevTools | **TODO** |

---

## 2. Remaining UX issues

| # | Page | Current | Expected | Severity | Suggested fix |
|---|------|---------|----------|----------|---------------|
| 1 | Full journey | DevTools cold path not run | Human verifies every row above | **Critical** | Run WeChat DevTools checklist on Windows host; mark PASS/FAIL with screenshots |
| 2 | HTTPS / domain | `apiBaseUrl` still `http://127.0.0.1:8001` | HTTPS + WeChat request合法域名 for real phone | **Critical** | Configure pilot HTTPS + mp domain whitelist (ops sprint; out of P3 code) |
| 3 | Task Home (healthy) | 「联系陈总」only on error chrome | Customer can ask for help without failing first | **High** | Add secondary/tertiary「联系陈总」on healthy hub (no new component — button bind existing handler) |
| 4 | Experience release | Prototype / local overrides | Packaged experience version for Chen Kui | **High** | Freeze config, strip prototype diagnostics, tag experience build |
| 5 | Photos defer | Secondary「返回我的资料」vs Story/Basics「稍后再填」 | Acceptable OR unify defer verb | **Low** | Keep as-is (hub escape vs section postpone) unless customers confuse |
| 6 | Review toast + redirect | Toast may be brief before redirect | Ensure toast readable on slow devices | **Low** | Optional short delay or rely on Receipt hero success |
| 7 | Entry / Task Home titles | Both「事故资料」 | Distinct open vs hub if needed | **Low** | Optional Entry「正在打开资料」nav title |
| 8 | Manual network fail | Not proven in DevTools | Offline / wrong base URL shows mapped Chinese only | **Medium** | Force unreachable in DevTools; confirm copy |
| 9 | Expired token path | Mapped in code | Live card expiry clears resume + contact | **Medium** | DevTools with expired token fixture |
| 10 | Real-device preview | 127.0.0.1 fails on phone | LAN / Cloud HTTPS URL | **High** | Document + set pilot `apiBaseUrl` |

---

## 3. Remaining pilot blockers

1. **Manual DevTools full journey not verified** (Critical).  
2. **HTTPS + WeChat合法域名** for real-device pilot (Critical).  
3. **Healthy Task Home lacks always-visible contact** (High — recovery story incomplete).  
4. **Experience / pilot config freeze** (High — no accidental local/dev token leaks).  
5. **Chen Kui dry-run script** (operator path + what to say when customer hits 「联系陈总」).

Non-blockers (acceptable for first pilot with caveats): Photos defer wording variance; Entry/Task Home shared nav title; brief submit toast.

---

## 4. Updated Pilot Readiness Score

### Dimension scores (0–100)

| Dimension | Score | Deduction notes |
|-----------|------:|-----------------|
| Architecture | 90 | Shared `taskPage` + TaskShell across journey; −10 no new hardening this sprint |
| Customer Journey | 86 | Continuous Entry→Receipt in code; −14 no DevTools end-to-end proof |
| UX Polish | 88 | P3 contact / hub wording / submit toast aligned; −12 healthy-hub contact gap + manual polish |
| Reliability | 82 | Read-back gates, busy guards, bounded retry; −18 not soak-tested / edge paths TODO |
| DevTools QA | 58 | **96** automated PASS; −42 because **full manual walkthrough TODO** |
| HTTPS readiness | 35 | Still HTTP localhost defaults; −65 for real-phone legal HTTPS/domain |
| Experience Version readiness | 70 | Product surface coherent; −30 prototype config / no freeze tag |
| Broker Pilot readiness | 68 | Contact messaging consistent; −32 ops runbook + real device + Chen Kui rehearsal |

### Overall Pilot Readiness Score

**83 / 100** (was **78** after P2)

**Why +5:** Secondary pages no longer mis-route「联系陈总」to postpone/hub escape; Review hub wording aligned; post-submit「提交成功」feedback added; automated coverage expanded (96 tests).

**Why not ≥90:** Manual DevTools checklist unproven; HTTPS/legal domain not ready for phone pilot; healthy Task Home contact still missing; experience freeze not done.

---

## 5. Top 10 items before Chen Kui Pilot

1. Run **full DevTools walkthrough** (Entry cold + resume + fail network + expire link + submit + receipt) and attach screenshots.  
2. Stand up **HTTPS pilot API** and whitelist WeChat request/upload domains.  
3. Set Mini Program **pilot `apiBaseUrl`** (never `127.0.0.1` on phone).  
4. Add **healthy Task Home「联系陈总」** secondary action.  
5. Freeze **experience build** (no prototype leaks; known token issuance path).  
6. Rehearse **Chen Kui reply script** when customer taps contact guidance.  
7. Verify **resume kill/reopen** toast on Task Home and Receipt in DevTools.  
8. Verify **expired / missing token** shows non-retryable contact path (no hopeful Retry).  
9. One **end-to-end photo upload** on real Wi-Fi (progress + read-back + success toast).  
10. Confirm **Receipt** shows next step + broker contact + 可能还需补充 before inviting first customer.

---

## UX consistency review (P3 code)

| Rule | Result |
|------|--------|
| 「联系陈总」behavior | Aligned on Story / Basics / Photos to shared modal (same as Entry / Error / Task Home / Review / Receipt) |
| 「返回我的资料」wording | Photos / Receipt / Review secondary + save CTAs use hub identity; Story/Basics primary「保存并返回我的资料」 |
| Resume toast | Single copy via `resumeHint` → Task Home / Receipt |
| Loading clear | Busy flags drive TaskShell; page tests assert clear after load/upload/submit |
| Success feedback | Story/Basics「已保存」; Photos「上传成功」; Review「提交成功」; Receipt success hero |
| Customer-safe errors | `mapErrorMessage` Chinese; no engineer dumps in mapped paths |
| Navigation dead ends | Error / Entry always retry or contact; section pages postpone/back to hub |

---

## Polish delivered this sprint

| Change | Files |
|--------|-------|
| Story contact → shared modal | `pages/story/story.{ts,wxml}` |
| Basics contact → shared modal | `pages/basics/basics.{ts,wxml}` |
| Photos contact → shared modal | `pages/photos/photos.{ts,wxml}` |
| Review secondary wording | `pages/review/review.wxml` →「返回我的资料」 |
| Review submit success toast | `pages/review/review.ts` |
| Regression tests | `tests/{story,basics,photos,review}Page.test.ts` |

---

## Automated Tests

### Mini Program

`cd miniapp && npm test`

- PASS: **96**
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

**Not run in this session** (WSL agent; WeChat DevTools available on Windows host but not executed here).  
All manual journey rows remain **TODO** / **WARNING**. Do not treat automated PASS as pilot green light.

## Files changed

- `miniapp/pages/story/story.ts`
- `miniapp/pages/story/story.wxml`
- `miniapp/pages/basics/basics.ts`
- `miniapp/pages/basics/basics.wxml`
- `miniapp/pages/photos/photos.ts`
- `miniapp/pages/photos/photos.wxml`
- `miniapp/pages/review/review.ts`
- `miniapp/pages/review/review.wxml`
- `miniapp/tests/storyPage.test.ts`
- `miniapp/tests/basicsPage.test.ts`
- `miniapp/tests/photosPage.test.ts`
- `miniapp/tests/reviewPage.test.ts`
- `docs/evidence/p20_product_polish_p3.md` *(this file)*

## Recommended next Sprint

**P4 — DevTools QA Gate + Pilot Ops Hardening**  
1) Execute and evidence the full manual checklist in WeChat DevTools.  
2) Healthy Task Home contact CTA.  
3) HTTPS / domain / experience freeze checklist (ops; still no feature expansion).  
4) Chen Kui pilot rehearsal script + one real-device photo upload proof.
