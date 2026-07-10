# P19H-3h — Product Architecture: WeCom + H5 Task Page + Broker Workbench

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Status:** Design complete — **GO** for Claim H5 Task Page MVP implementation  
**Scope:** Product architecture — documentation only  
**Audience:** Andy, Chen Kui pilot team, P19H+ implementation agents  
**Prerequisite:** P19H-3h Recon ✅ · P19H-3f-4 (Status Card) ✅ · P19H-3f-5 (Single Active Task) ✅ · P19H-3g (Pilot readiness) ✅

---

## 1. Product thesis

**WeChat-native Broker Intake Copilot** evolves from conversational Q&A into a **task-driven intake system**:

> **WeCom opens the task. H5 completes the task. The state machine controls the task. The broker closes the task.**

Customers experience something closer to **Walmart Spark Driver**: one screen, one primary action, visible progress, clear completion — not a chatbot interrogation. Brokers receive **structured, auditable evidence** instead of scrolling WeChat threads.

This is **record collection and broker handoff memory** — not carrier filing, CRM, liability engine, or coverage automation. Every surface reinforces: *这不代表已经向保险公司正式报案*.

### Core principle — Structured Task First, AI Assist Second

**结构化任务优先，AI 理解辅助。**

The customer-facing main path must **not** depend on AI interpreting free text. Customers complete work through **explicit buttons, fields, uploads, and submit**. The **state machine** advances the workflow. AI handles backend understanding, organization, summary, missing-item hints, risk flags, and **broker draft** — nothing more.

| Layer | Role in this principle |
|-------|------------------------|
| **State machine** | **Main controller** — phase, missing_info, single-active-task routing |
| **H5 Task Page** | **Structured task execution UI** — wizard steps, PATCH/submit, loading UX |
| **WeCom** | **Entry · notify · light confirm · exceptions** — not complex intake main UI |
| **AI brain** | **Assist only** — extract, normalize, summarize, flag; never owns flow |
| **Broker Workbench** | Shows structured facts + AI draft; **broker confirms** final handoff |

**Customer input priority:**

```text
1. Explicit H5 buttons / fields / upload / submit     ← authoritative
2. H5 confirmed facts (persisted PATCH + timeline)
3. WeCom free text / photos                           ← supplemental / provisional
4. AI extraction                                      ← draft only
```

**Why:** Like Walmart Spark Driver, smoothness comes from a clear task state machine — not free chat. Users speak less, guess less, wait less. The system misjudges less, forks less, repeats less. Brokers trust structured data.

**Claim H5 MVP implementation must enforce this.** No chat-driven step collection, no LLM-controlled phase transitions, no treating WeCom narrative as primary intake.

---

## 2. Why WeCom chat alone is not enough

WeCom is excellent for **trust, entry, and notification**. It is structurally weak as the **primary formal intake surface** for accident records.

| Symptom | Root cause in pure chat | H5 + state machine fix |
|---------|-------------------------|-------------------------|
| 回复慢 | Sync callback + LLM/rules per message (2–5s) | Local form; one API round-trip per step |
| 重复点击 | msgmenu buttons cannot disable | Web button `disabled` + loading |
| 信息来回提交不丝滑 | Free-text extraction loop; bulk narrative re-parse | Step wizard with explicit fields |
| 无视觉进度 | Status Card is pull-based (`进度`) | Push progress on each step complete |
| 客户信任感不足 | Feels like bot Q&A | Feels like「填任务」— Spark-like task page |
| 异常污染主流程 | Collision / multi-open edge cases mixed into chat flow | Exceptions routed to Confirm Cards; H5 stays linear |

**Prior recon score (P19D-16, updated P19H-3h):**

| Surface | Spark-like (Claim overall) |
|---------|---------------------------|
| Pure WeCom chat | ~50–60% |
| WeCom + H5 Task Page | ~85–88% |

**What WeCom must keep owning:**

- Start Card ceremony (`我要理赔`)
- Status Card (`进度` / `状态`)
- End Card (`broker_done`)
- Collision Resolver / lane-switch Confirm Cards
- Urgent injury alert copy
- Optional chat supplements (photos, free text as safety net)

**What WeCom must stop owning (Claim MVP):**

- Primary collection of accident basics (time, location, story, other party)
- Step-by-step field prompts in chat

---

## 3. Target architecture

```text
                         ┌─────────────────────────────────────┐
                         │           Customer                  │
                         └──────────────┬──────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────────┐       ┌──────────────────┐
│  WeCom           │         │  H5 Task Page        │       │  (Future)        │
│  entry · notify  │ signed  │  structured intake   │       │  mini program    │
│  simple confirm  │ link    │  photos · submit     │       │  independent app │
└────────┬─────────┘         └──────────┬───────────┘       └──────────────────┘
         │                              │
         │         ┌────────────────────┼────────────────────┐
         │         │                    │                    │
         ▼         ▼                    ▼                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  AI brain (extraction · summary · missing info)                              │
│  • Chat append safety net                                                    │
│  • Field normalization (date, phone)                                         │
│  • Does NOT own flow control                                                 │
└────────────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  State machine (claim_state.py · derive_claim_phase · single active task)  │
│  • Phase transitions                                                         │
│  • missing_info derivation                                                   │
│  • Stronger than AI for「what step are we on」                               │
└────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Postgres (source of truth — no schema migration)                          │
│  known_facts · claim_phase · claim_timeline · attachments                  │
└────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Broker Workbench                                                          │
│  Case Summary · Received · Missing · Risk flags · Photos · Timeline · Done │
└────────────────────────────────────────────────────────────────────────────┘
```

### Channel responsibilities

| Layer | Owns | Does NOT own |
|-------|------|--------------|
| **WeCom** | Start / Status / End / Confirm Cards; trust copy; urgent alerts; optional supplement | Primary structured field collection |
| **H5 Task Page** | Step form, photos, submit, resume, loading UX, idempotent handoff | Login, carrier filing, OCR/ASR |
| **AI brain** | Extract from chat supplements; normalize; summarize; missing hints; risk flags; **broker draft** | Flow control; phase transitions; auto-confirming customer facts |
| **State machine** | **Main controller** — phase, missing_info, single-active-task routing | Customer-facing copy (delegates to cards/H5) |
| **Workbench** | Review structured facts + AI draft; broker confirms; broker_done; risk visibility | Customer-facing intake; treating AI draft as final without broker review |

### Data flow (steady state)

```text
WeCom Start Card → mint h5t1 token → H5 deep link
H5 step PATCH → patch_case_known_facts → append claim_timeline (source: h5_task)
H5 photo POST → GCS + attachment metadata (existing claim_evidence_pack)
H5 submit POST → intake_ready_for_broker / broker_review phase
Workbench GET → build_claim_case_brief()
Broker Done POST → End Card + terminal phase
```

**Do NOT rewrite the AI brain.** Wire H5 submits into existing `patch_case_known_facts` + `derive_claim_phase`.

---

## 4. Why H5 before mini program

| Factor | H5 WebView | WeChat Mini Program |
|--------|------------|---------------------|
| Time to ship Claim form MVP | **5–7 days** | 2–4× engineering; audit weeks |
| WeCom deep link | ✅ `H5_TASK_FRONTEND_BASE_URL` shipped | Requires open-data / binding |
| Token auth (no login) | ✅ `h5t1.*` shipped | Identity binding complexity |
| Photo upload | ✅ GCS path exists | Native picker better; not blocking |
| Pilot iteration | Fast Vercel deploy | Slow review cycle |
| Spark-like target | **~85–88%** | ~92–95% |

**Verdict:** H5 is sufficient for Chen pilot. Mini program is a **Phase 4+** investment after the task model is validated.

**P19E-3 evolution:** H5 scope moves from「photo shell only」→「**Claim primary intake form + photos**」.

---

## 5. Why not independent app now

| Factor | H5 from WeCom | Independent app |
|--------|---------------|-----------------|
| Customer friction | Zero install; tap link in trusted WeChat thread | App store, login, push permissions |
| Chen pilot audience | WeChat-native brokers and customers | Wrong distribution for pilot |
| Engineering | Reuse token + upload infra | Auth, push, app lifecycle, store review |
| Trust |「陈总办公室发的链接」| Unknown app brand |

An independent app makes sense only when:
- Multi-broker SaaS with own brand
- Offline-heavy workflows
- Push notifications beyond WeCom

None apply to Chen pilot.

---

## 6. Long-term platform direction

**AI Task Intake Platform** — same core pattern across verticals:

```text
Channel entry (WeCom / SMS / email / web)
    → H5 Task Page state machine
    → AI extraction + evidence chain
    → Operator Workbench review
```

| Vertical | Example task trip |
|----------|-------------------|
| Insurance | Claim intake, Add Car, policy change |
| Ecommerce | Return/refund evidence, delivery dispute |
| Service / repair | Work order photos, scope confirmation |
| Medical admin | Prior auth documents, intake forms |
| Loan / tax | Document collection, income verification |

**Reusable primitives (already in codebase):**

- `h5t1` signed tokens
- Lane (`claim`, `add_car`) + flow constants
- `known_facts` JSON persistence
- `claim_timeline` / activity timeline pattern
- Workbench brief + broker_done ceremony
- Single Active Task per lane
- Idempotency + reply dedup

**What varies per vertical:** step definitions, field contracts, broker review panels — not the platform skeleton.

---

## 7. Chen pilot objective

| Pain today | Target with WeCom + H5 + Workbench |
|------------|-------------------------------------|
| Chen repeats「还要什么」on WeChat | Status Card + H5 progress show missing inline |
| Customers send incomplete narratives | H5 wizard enforces one field per step |
| Materials lost in chat scroll | Timeline + attachments bound to active case |
| Broker scrolls 50 messages to understand case | Claim Case Brief in ~10 seconds |
| Duplicate taps / uncertain if message sent | H5 disabled submit + idempotency keys |
| Two accidents mixed together | Collision Resolver + single active task policy |

**Pilot success criteria (customer-facing):**

1. Customer says `我要理赔` → receives Start Card with **H5 link as primary CTA**
2. Customer completes H5 trip → broker sees structured brief without re-asking basics
3. Customer asks `进度` → Status Card matches H5 state (已收到 / 还缺 / 下一步)
4. Chen clicks Broker Done → customer receives End Card (when send env enabled)

**Pilot success criteria (broker-facing):**

1. Open Workbench row → see key facts, photos, missing, risk flags in one drawer
2. No raw inbound noise in default queue
3. Multi-open Claims flagged (`possible_multi_claim_context`) without customer picker

---

## 8. Two business lanes (pilot scope)

| Lane | Customer entry | H5 task trip | Workbench |
|------|----------------|--------------|-----------|
| **Claim** | `我要理赔` → Start Card | Claim Intake Trip (9 steps) — **MVP first** | Claim Case Brief |
| **Add Car** | Add car intent → Start Card | Add Car Intake Trip (9 steps) — **Phase 3 reuse** | Add Car brief (existing) |

Lane switch (Add Car → Claim) uses existing Confirm Card. Collision uses existing Resolver. H5 does not replace these exception paths.

---

## 9. Existing asset inventory (reuse map)

| Asset | Status | Reuse for H5 |
|-------|--------|--------------|
| `h5_task_token.py` | ✅ | Extend `FLOW_CLAIM_INTAKE_FORM` |
| `h5_task_link.py` | ✅ | `mint_h5_claim_intake_form_link()` |
| `h5_task_upload.py` + routes | ✅ | Photo step |
| `claim_state.py` | ✅ | Phase derivation unchanged |
| `claim_workbench_display.py` | ✅ | Brief auto-enriches from `known_facts` |
| `reply_dedup.py` | ✅ | Card dedup |
| Single Active Task (P19H-3f-5) | ✅ | Append to newest open case |
| H5 Claim intake form page | ❌ | **To build** |
| H5 intake APIs (`/intake`, `/fields`, `/submit`) | ❌ | **To build** |

---

## 10. GO / HOLD

| Decision | Verdict |
|----------|---------|
| WeCom + H5 + Workbench architecture | **GO** |
| Claim H5 Task Page MVP | **GO** (5–7 days) |
| Mini program | **HOLD** |
| Independent app | **HOLD** |
| Schema migration | **NO** |
| Rewrite claim AI | **NO** |

---

## Related documents

| Doc | Purpose |
|-----|---------|
| `p19h3h_claim_h5_task_state_machine_2026_07_10.md` | Claim step design |
| `p19h3h_add_car_h5_task_state_machine_2026_07_10.md` | Add Car step design |
| `p19h3h_smooth_ux_idempotency_async_design_2026_07_10.md` | Idempotency + async |
| `p19h3h_evidence_chain_broker_review_design_2026_07_10.md` | Timeline + Workbench |
| `p19h3h_master_design_summary_2026_07_10.md` | Implementation handoff |

*Recon source: `docs/policy/p19h3h_h5_task_page_primary_intake_recon_2026_07_10.md`*
