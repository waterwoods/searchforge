# P0 Architecture Freeze — Customer Waiting State

**Status:** Architecture approved — **Commit 1 implemented** (Case Status + routing). Voluntary Supplement / soft-freeze edits are **not** in Commit 1.  
**Date:** 2026-07-22  
**Scope:** Customer experience after required intake is complete and no open Request More exists  
**Does not supersede:** One Active Case (D-001), Append-first (D-002), Today First (D-003), Why/After (D-004/D-005), One Truth (D-006), Service Home (D-008), Golden one-scan  
**Related runtime today:** Constitution `waiting_broker` / `_TODAY_WAIT = "先不用操作"`; Task Home waiting block; Receipt supplement path

---

## P20 header

**ONE OBJECTIVE**  
When the customer owes nothing, they still understand where their case is, what happens next, and what they can still do — without a dead-end「先不用操作」screen.

**OUT OF SCOPE (this freeze)**  
Claim Vehicle T6, new claim types, multi-case picker, push/WebSocket, estimated SLA clocks that we cannot honor, download/PDF, customer chat product, redesign of Request More broker UI.

**STOP RULE**  
Approve this freeze before any implementation commits. Split later work into small commits.

---

## 0. Problem statement (Founder PAT)

```text
Finish required intake (e.g. Insurance Card)
  → Home → Continue → Task Home
  → 「先不用操作」
  → Dead end
```

Customer cannot meaningfully: understand next step, voluntarily add material, or generate clear broker-visible activity — while also correctly blocked from a second Active Case.

**Classification:** Missing **Customer Waiting State** product design — not a UI copy bug alone.

Constitution already computes `waiting_broker` and has better Why/After strings (`资料已齐，陈总正在审核。`) but **Today collapses to「先不用操作」**, which erases meaning and freezes the shell into an inert task page.

---

## 1. Answers (deliberate)

### Q1 — Should “Waiting Broker” be a dedicated product state?

**Yes.**

Treat **Waiting Broker** as a first-class customer lifecycle state (already partially modeled as Constitution `waiting_broker` / stage), not as “Task Home with an empty CTA.”

| Customer owes work | State name | Surface mode |
|--------------------|------------|--------------|
| Yes (default intake or open Request More) | **Action Needed** | Task Home (Today First) |
| No | **Waiting Broker** | **Case Status** (same route family, different mode) |
| Case closed / broker done (later) | **Closed** (out of V1 detail) | Status read-only |

### Q2 — Should Task Home become read-only?

**Not “Task Home frozen.”** Switch mode:

- **Action Needed** → Task Home remains the work surface (editable for the open task).
- **Waiting Broker** → same entry path opens **Case Status** (read-mostly): status, last submitted, what happens next, secondary actions.

Do **not** keep a primary disabled CTA that says nothing useful.

### Q3 — Edit photos / story / insurance while waiting?

**Soft-freeze completed required slots. Allow voluntary append.**

| Material | While Waiting Broker | Rationale |
|----------|----------------------|-----------|
| Completed required tasks (story, insurance, required photos) | **No free re-edit as primary** | Avoid silent overwrite while broker reviews |
| Voluntary add (extra photo, short note, extra document) | **Yes — append** | D-002 Append-first; real “I forgot one more photo” |
| Correction of a completed slot | Broker **Request More** or Contact broker | Broker owns reopen; No Unsupported Choices |

**Voluntary path:** secondary action「补充资料」→ narrow append sheet (photo and/or short note) bound to **same** `case_id` / resume token — never a second case.

### Q4 — Home vs Continue landing

| Surface | Role |
|---------|------|
| **Service Home** | Remains **product entrance** (D-008). Always. |
| **Continue Current Claim** | Opens the **current case surface**: Action Needed → Task Home; Waiting Broker → **Case Status**. |
| Dedicated Status-only route | Optional later; V1 may mode-switch Task Home / Receipt into Case Status to avoid page sprawl. |

Home is **not** replaced by Status. Continue must not dump the user into「先不用操作」as if it were a task.

### Q5 — Replace「先不用操作」?

**Yes — retire it as primary Today copy.**

Suggested Waiting Broker headline (Chinese, human):

| Slot | Copy |
|------|------|
| **Status (primary)** | 陈总正在审核您的资料 |
| **Why** | 您这边暂时没有需要完成的事项 |
| **After** | 如需补充，陈总会再联系您 |
| **Last submitted** | 最近提交：{item} · {relative or local time} |
| **Reassurance** | 有进展时我们会联系您（勿重复提交同一份资料） |

Do **not** invent false ETA (“预计 2 小时”) unless operations can keep it true.

### Q6 — What can the customer still do with no actionable task?

**Choose deliberately — V1 allow list:**

| Action | V1 |
|--------|----|
| View case status / next step | **Required** |
| View submitted materials (read) | **Required** |
| Contact broker | **Required** |
| Voluntary supplement (append) | **Required** |
| View simple timeline / progress list | **Nice → include if cheap** |
| Leave unstructured long message | Defer (contact broker covers) |
| Download / PDF copy | **Out** |
| Nothing | **Reject** — that is today’s dead end |
| Start new claim | Policy only (One Active Case) — not a waiting escape hatch |

### Q7 — Voluntary supplemental information?

**Yes (V1).**

- Secondary, never competing with an open Today task (D-003).
- Append-only to Active Case (D-002).
- Does **not** clear Waiting Broker unless Constitution says customer work is owed again (usually stays Waiting; broker sees new material).
- Does **not** require Request More to unlock.

### Q8 — Request More transition — sufficient?

**Yes for V1**, if Status ↔ Action Needed is explicit:

```text
Waiting Broker
  → Broker Request More (supported type)
  → Action Needed (Today = that item)
  → Customer completes
  → Waiting Broker
```

Sufficient when:

1. Same resume token / one-scan (Phase 2 freeze).  
2. Continue / foreground rehydrates Constitution.  
3. Case Status never claims “nothing to do” while an open request exists (One Truth).

Queued multi-item Request More stays Today First (one active item).

### Q9 — Workbench event on voluntary supplement?

**Yes.**

Append creates a timeline / workbench-visible event on the **same case**, e.g. conceptual:

- `customer_voluntary_supplement_submitted` (or reuse existing supplement/upload events if already equivalent)

Broker must see that new material arrived **without** a Request More row — so office is not blind.

### Q10 — Extends to Vehicle / Driver / Police / Witness / Medical?

**Yes — without redesign.**

Those are **item types** that flip Action Needed via Request More (and later optional defaults). Waiting Broker / Action Needed / voluntary append are **case-level modes**, not per-document products.

---

## 2. State diagram (customer lifecycle)

```text
                    ┌─────────────────┐
                    │  Service Home   │  product entrance
                    └────────┬────────┘
                             │ Continue (active case)
                             ▼
              ┌──────────────────────────────┐
              │     Resolve Constitution     │
              └──────────────┬───────────────┘
           owed work?        │         no owed work?
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
┌───────────────────┐                   ┌─────────────────────┐
│  ACTION NEEDED    │                   │  WAITING BROKER     │
│  (Task Home)      │                   │  (Case Status)      │
│  Today = 1 task   │                   │  Status + After     │
│  Primary = do it  │                   │  Secondary actions  │
└─────────┬─────────┘                   └──────────┬──────────┘
          │ complete                               │
          └────────────────┬───────────────────────┘
                           ▼
                 ┌───────────────────┐
                 │  WAITING BROKER   │◄──── Broker idle / review
                 └─────────┬─────────┘
                           │ Request More
                           ▼
                 ┌───────────────────┐
                 │  ACTION NEEDED    │
                 └───────────────────┘

Voluntary supplement (only meaningful in WAITING or as secondary
when not conflicting with Today):
  WAITING ──append──► WAITING (+ workbench event)
  ACTION NEEDED: prefer finish Today first; append not primary
```

Golden path unchanged:

```text
Scan once → Entry → (Action Needed | Waiting) → Home → Service Home
  → Continue → same token → same case → Request More without rescan
```

---

## 3. Permissions by state

| Capability | Action Needed | Waiting Broker | Notes |
|------------|---------------|----------------|-------|
| Open / continue case | Yes | Yes | Resume token |
| Complete Today task | Yes | No | |
| Edit open request item | Yes | No | |
| Free-edit completed slots | Limited | **No (soft-freeze)** | |
| Voluntary append | Secondary / defer | **Yes** | |
| View submitted materials | Yes | Yes | Read |
| Contact broker | Yes | Yes | |
| Start new claim | Policy | Policy | D-001 / P30 |
| Clear resume token | Never casually | Never | Breaks one-scan |

---

## 4. Actions available per state

### Action Needed

1. **Primary:** Do Today’s task  
2. Contact broker  
3. View progress / materials (secondary)  
4. Home → Service Home  

### Waiting Broker

1. **Primary:** Understand status (no fake work CTA)  
2. View submitted materials  
3. **补充资料** (voluntary append)  
4. Contact broker  
5. Home → Service Home  

---

## 5. Minimal UX (V1)

**One composition for Waiting Broker (Case Status):**

1. Status headline — 陈总正在审核您的资料  
2. Why / After — one line each (existing Constitution fields preferred)  
3. Last submitted — one line  
4. Completed list — compact, read-only  
5. Footer: **补充资料** (secondary) · **联系保险顾问** · (optional) 查看资料  

**No** primary button that is disabled with「先不用操作」.  
**No** second blue CTA competing with Status.

Service Home Continue label can stay「继续处理当前报案」even when waiting — it means “open my case,” not “you still owe work.” Optional later:「查看案件状态」when Waiting (polish only).

---

## 6. Suggested wording (replace「先不用操作」)

| Role | Do not use | Use |
|------|------------|-----|
| Today / status title | 先不用操作 | 陈总正在审核您的资料 |
| Why | 目前没有需要您操作的事项 (alone) | 您这边暂时没有需要完成的事项 |
| After | 请等待确认 (vague) | 如需补充，陈总会再联系您 |
| Voluntary CTA | 开始新报案 (wrong job) | 补充资料 |
| Soft-freeze toast | — | 审核中暂不修改已交资料；如需更正请联系陈总或等待补件请求 |

Keep engineering terms out of UI (token, projection, waiting_broker).

---

## 7. Architectural vs UI polish

### Architectural (needs freeze + careful commits)

1. Elevate **Waiting Broker** as customer-visible mode (Constitution stage → Case Status UX contract).  
2. Soft-freeze vs **voluntary append** permission model.  
3. Workbench / timeline **event** for voluntary supplement.  
4. Continue routing: Action Needed vs Waiting → correct surface (One Truth).  
5. Retire「先不用操作」as primary Today when `_is_waiting_broker`.  

### UI polish (after architecture)

1. Copy, spacing, last-submitted formatting.  
2. Continue label variant「查看案件状态」.  
3. Compact completed-task list styling.  
4. Reuse Receipt vs Task Home shell — implementation choice, not product law.

---

## 8. Migration plan (no breakages)

### Invariants to preserve

| Invariant | Rule during migration |
|-----------|------------------------|
| One Active Case | Voluntary append ≠ new case; Start New still policy |
| Golden one-scan | Never clear `mp_prototype_resume_token` on Waiting UX |
| Resume token | Continue / Status / append use same token |
| Request More | Waiting → Action Needed on same session / foreground refresh |

### Suggested commit split (after approval only)

1. **Copy + Case Status mode** — replace「先不用操作」primary; Waiting shows Status layout; no new APIs.  
2. **Voluntary append (minimal)** — photo and/or note → existing upload/fact path + timeline event; soft-freeze completed slots.  
3. **Founder PAT** — Golden: finish insurance → Waiting Status meaningful → Home → Continue → Status → Broker Request More → Action Needed → complete → Waiting again.

### Non-goals in migration

- ETA clocks, PDF download, chat, multi-case, changing Golden Entry deep-link, Claim Vehicle T6.

---

## 9. Decision summary (proposed D-014 — pending Founder ack)

| Field | Content |
|-------|---------|
| **Decision** | When the customer owes no work, the product enters **Waiting Broker** (Case Status): meaningful status copy, soft-frozen completed slots, voluntary append allowed, Contact broker required;「先不用操作」is retired as primary Today. Request More flips to Action Needed on the same case/token. |
| **Why** | Removes Founder/customer dead end without violating One Active Case or inventing a second case workflow. |
| **Status** | **Proposed — await Founder approval before implementation** |

---

## 10. Approval checklist

- [ ] Founder accepts Waiting Broker as dedicated state  
- [ ] Founder accepts soft-freeze + voluntary append  
- [ ] Founder accepts wording direction (no false ETA)  
- [ ] Founder accepts workbench visibility for voluntary supplement  
- [ ] Implementation authorized as separate task (max small commits above)

**Until checked:** no code changes for this freeze.
