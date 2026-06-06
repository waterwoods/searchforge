# Lightweight Ticket / Follow-up UX Sprint Report

**Sprint:** Lightweight Ticket / Follow-up UX Sprint  
**Date:** 2026-03-11  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — day-to-day broker follow-up continuity

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| **Stage 1 — Define lightweight ticket model** | ✅ Completed | §0b added to BROKER_HANDOFF_CLARITY_GUIDE.md |
| **Stage 2 — Broad follow-up / reopen scouting** | ✅ Completed | Inspected case_store, triage, routes, UnifiedIntakePage, queue/case card |
| **Stage 3 — Classify continuity gaps** | ✅ Completed | 10 categories; prioritized 4 high-value fixes |
| **Stage 4 — Prioritize highest-value fixes** | ✅ Completed | Resume here, due-state, last meaningful update, queue last-update |
| **Stage 5 — Improvement Loop 1** | ✅ Completed | Resume here card, due-state labels, last meaningful update |
| **Stage 6 — Improvement Loop 2** | ✅ Completed | Queue "Last update" when note exists; smoke check steps 17–18 |
| **Stage 7 — Optional Improvement Loop 3** | Skipped | Two passes sufficient |
| **Stage 8 — Lightweight ticket product proof** | ✅ Completed | 5 walkthroughs below |
| **Stage 9 — Regression + safety protection** | ✅ Completed | Smoke check steps; runbook note |
| **Stage 10 — Audit + practical judgment** | ✅ Completed | Verdict: Accept |

---

## 2. Lightweight ticket target

**What a good lightweight ticket/follow-up experience means:**

| Concept | Target |
|---------|--------|
| **Status** | new, reviewing, waiting_client, done — broker can mark progress |
| **Due-state** | Overdue / Due today / Due tomorrow / No due date — broker knows when to act |
| **Last meaningful update** | Latest broker note or activity — broker sees what changed since last open |
| **Reopen context** | "Resume here" — waiting on + next contact + latest note — broker picks up where they left off |
| **Waiting on** | client, broker, carrier, underwriting — broker knows who owns the next move |
| **Next step** | broker_next_step — operational, actionable |

**Why it matters:** Chen Kui and office staff need to continue yesterday's work today. The system should remember the case in a practical way: what is active, what is waiting, what needs follow-up, what to reopen, what to do next — without becoming a heavy CRM.

---

## 3. Product / data / UX changes made

| File | Change | Purpose |
|------|--------|---------|
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Added §0b Lightweight Ticket / Follow-up Model | Define status, due-state, last update, reopen context |
| `ui/src/pages/UnifiedIntakePage.tsx` | `getFollowUpDueTag()` extended | Overdue, Due today, **Due tomorrow** |
| `ui/src/pages/UnifiedIntakePage.tsx` | `getDueStateLabel()` | Due-state label for "Where this case stands" |
| `ui/src/pages/UnifiedIntakePage.tsx` | "Resume here" card | When reopening, shows waiting on + next contact + latest note |
| `ui/src/pages/UnifiedIntakePage.tsx` | "Last meaningful update" label | Replaces "Latest context" in Where this case stands |
| `ui/src/pages/UnifiedIntakePage.tsx` | Due-state tag in case card | "No due date" / "Due: X" when no overdue/due today |
| `ui/src/pages/UnifiedIntakePage.tsx` | Queue card "Last update" | When note exists, shows "Last update: {note preview}" |
| `scripts/unified_intake_smoke_check.sh` | Steps 17–18 | Follow-up continuity, due-state, last meaningful update |

**Backend:** No changes. All improvements are UI-side from existing persisted fields.

---

## 4. Simulation and improvement loops

**What was simulated (Ticket-Flow Simulator):**

- Customer sent missing item yesterday, now sends another update → broker adds note "Client resent dec page"; reopen shows "Resume here" with note
- Renewal case needs follow-up today → due-state "Due today" tag; broker sees "Your move"
- Claim case continued after first intake → broker sets waiting_on=client, next_contact_by; reopen shows "Resume here"
- Missing-document "already sent again" → broker adds note; queue shows "Last update: Client said they resent..."
- Add-car quote-ready except one detail → broker sets waiting_on=broker; reopen shows "Resume here"

**Problems found:**

1. Reopen: no compact "where I left off" — broker had to scan full card
2. Due-state: only overdue/due today; no "due tomorrow" or "no due date"
3. Last meaningful update: labeled "Latest context" — less clear for daily use
4. Queue: tracking summary was generic; when note exists, "Last update" is more useful

**Fixes made:**

1. "Resume here" card when reopening with follow-up or note
2. Due-state: Overdue, Due today, Due tomorrow, No due date
3. "Last meaningful update" label
4. Queue: "Last update: {note preview}" when note exists

**After rerun:** Reopened cases with notes now show "Resume here" and "Last update" in queue. Due-state is clearer.

---

## 5. Product proof strength

| Question | Answer |
|----------|--------|
| Can broker more easily continue work from yesterday? | Yes. "Resume here" and "Last meaningful update" reduce re-reading. |
| Is reopen clearer? | Yes. Compact "Resume here" card with waiting on + next contact + latest note. |
| Is due-state useful enough? | Yes. Overdue, Due today, Due tomorrow, No due date. |
| Is last meaningful update visible enough? | Yes. Case card and queue show it. |
| Does this feel more daily-usable? | Yes. Less demo-only; more practical follow-up. |
| Is anything getting too heavy? | No. No new backend; no CRM complexity. |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | 49/49 scenarios, multi-turn, adversarial, complex |
| `cd ui && npm run build` | PASS | UI compiles |
| `scripts/unified_intake_smoke_check.sh` | PASS | Steps 17–18 for follow-up continuity |

---

## 7. Business / platform value

| Area | Improvement |
|------|-------------|
| **Daily-use continuity** | Broker can resume work faster; "Resume here" and "Last update" reduce mental reconstruction |
| **Due-state clarity** | Overdue / Due today / Due tomorrow help broker prioritize |
| **Reopen experience** | Compact "Resume here" card shows where broker left off |
| **Queue follow-up** | "Last update" when note exists helps broker scan without opening |

---

## 8. Remaining blocker(s)

1. **No append-to-existing-case flow:** When customer sends new message, broker pastes → new triage → new case. Broker must add note manually for continuity.
2. **Field values in queue:** Queue shows field names (Year, Make/Model) not extracted values (2025, Honda CR-V).
3. **API test:** missing_document collected_fields may fail if server not restarted (pre-existing).

---

## 9. Recommended next step

Consider a lightweight "Paste new message into this case" flow: when broker has a case open, allow pasting a follow-up message that updates source_text and re-triages, merging into the existing case. Low-risk, high-value for continuity. Do not build inbox sync or full CRM.

---

## 10. 中文或中英混合宏观总结

**轻量 ticket / follow-up 这次变好了什么：**
- Reopen 时多了「Resume here」卡片，一眼看到 waiting on、next contact by、latest note。
- Due-state 更清楚：Overdue、Due today、Due tomorrow、No due date。
- 「Last meaningful update」取代「Latest context」，更贴近日常办公用语。
- 队列卡片有 note 时显示「Last update: {note 预览}」，不用点开就知道最近更新。

**reopen、due-state、last update 哪些更清楚了：**
- Reopen：Resume here 卡片。
- Due-state：四档标签（overdue / due today / due tomorrow / no due date）。
- Last update：case card 和 queue 都显示。

**哪些地方更像日常办公而不是 demo：**
- 昨天设了 waiting on client、next contact by 明天，今天 reopen 能立刻看到 Resume here。
- 加了 broker note「客户说明天重发」，queue 显示 Last update，不用点开。

**还缺什么：**
- 客户发新消息时，不能直接 append 到现有 case，需要 broker 手动加 note。
- Queue 仍显示字段名而非值（如 2025, Honda CR-V）。

**这次对陈奎和以后别的小客户有什么帮助：**
- 陈奎办公室可以更快继续昨天的 case，减少重复阅读。
- 以后别的 broker 客户也能用同一套轻量 ticket 逻辑，更贴近真实办公室 follow-up 工作方式。

---

## 11. Practical lightweight ticket cheat sheet

| What exists | How it appears |
|-------------|----------------|
| **Status** | new, reviewing, waiting_client, done |
| **Due-state** | Overdue (red), Due today (orange), Due tomorrow (gold), No due date |
| **Last meaningful update** | Latest broker note or activity; "Last update" in queue when note exists |
| **Reopen support** | "Resume here" card: waiting on + next contact + latest note |
| **Waiting on** | none, client, broker, carrier, underwriting |
| **Next step** | broker_next_step from triage |

**What still remains manual:** Appending new customer messages to existing case (add broker note for continuity).

---

## 12. Continuity problem summary

| Category | Strength | Notes |
|----------|----------|-------|
| **Reopen with note** | Strong | Resume here + Last meaningful update |
| **Due-state** | Strong | Overdue, Due today, Due tomorrow, No due date |
| **Queue last update** | Strong | "Last update" when note exists |
| **Reopen without note** | Acceptable | Resume here shows follow-up only; broker may need to re-read source |
| **New customer message** | Weak | Creates new case; broker adds note to old case for continuity |

**Repeated continuity weaknesses addressed:**
- Reopen loses context → Resume here card
- Due-state vague → Four-tier labels
- Last update not useful → "Last meaningful update" + queue "Last update"

---

## 13. Follow-up proof walkthroughs

### 1. Add-car resumed case

**What happened:** Broker triaged add-car quote, set waiting_on=broker, next_contact_by=today, note="Same-day quote if VIN comes back."

**What broker sees now:** Reopen → "Resume here" shows "Waiting on broker · Next contact by 2026-03-11 · Latest note: Same-day quote if VIN comes back." Due-state: "Due today."

**What improved:** Resume here card; due-state tag.

**Result:** Strong.

---

### 2. Renewal follow-up

**What happened:** Broker triaged premium review, set waiting_on=client, next_contact_by=tomorrow, note="Waiting on latest bill."

**What broker sees now:** Reopen → "Resume here" shows "Waiting on client · Next contact by 2026-03-12 · Latest note: Waiting on latest bill." Due-state: "Due tomorrow."

**What improved:** Due tomorrow tag; Resume here.

**Result:** Strong.

---

### 3. Claim continued case

**What happened:** Broker triaged claim intake, set waiting_on=client, note="Client will send photos tomorrow."

**What broker sees now:** Reopen → "Resume here" shows "Waiting on client · Latest note: Client will send photos tomorrow." Due-state: "No due date" (if next_contact_by empty).

**What improved:** Resume here; Last meaningful update.

**Result:** Strong.

---

### 4. Missing-document "already sent again" case

**What happened:** Broker triaged missing doc, set waiting_on=client, note="Client said they resent dec page yesterday."

**What broker sees now:** Queue shows "Last update: Client said they resent dec page yesterday." Reopen → "Resume here" with that note.

**What improved:** Queue "Last update"; Resume here.

**Result:** Strong.

---

### 5. Queue-level triage / follow-up example

**What happened:** Founder demo queue loaded; mixed cases with notes and follow-up.

**What broker sees now:** Work now vs Waiting or parked; "Last update" on cases with notes; Overdue / Due today / Due tomorrow tags.

**What improved:** Queue-level last update; due-state visibility.

**Result:** Strong.

---

### One case that remains only acceptable

**Reopen without note:** When broker reopens a case with no note and no follow-up target, "Resume here" does not appear. Broker sees full case card. Acceptable — broker can add note on next touch.

---

### One limitation intentionally not addressed

**Append new message to existing case:** Building inbox sync or "paste into this case" would add complexity. Broker adds note manually for now. Keeps product lightweight.

---

*End of report*
