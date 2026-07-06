# P19 UX Recon — Spark Driver-style Mobile Task Workflow for Insurance Case Builder IQ

**Date:** 2026-07-05  
**Type:** Product research / design recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, implementation agents  
**Prerequisite:** Loop 0–3B stable; `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` is the technical spec authority for P19.

**Purpose:** Extract the **workflow pattern** behind gig-economy mobile task apps (Walmart Spark Driver as reference) and map it to P19 WeCom Photo Intake / Mobile Case Builder — without copying UI chrome.

**This loop:** No code. No deploy. No schema changes.

---

## 1. Spark Driver-style Workflow — Core Patterns

We borrow **behavioral structure**, not visual design. Spark Driver succeeds because every trip is a **finite mobile task** with proof, status taps, and backend dispatch — not because of Walmart branding.

**Key insight (Andy):** Spark Driver is **not just photo upload**. It is a **guided, location/task-aware workflow** — a repeating loop of micro-steps, verification, and exception branches until the task is complete and ops has done final review. The best pattern to borrow is **guided micro-steps + verification + exception handling + final review** — not the visual UI.

### 1.0 Guided micro-step loop (Spark → Insurance)

#### Spark Driver — item-by-item guided flow

| Step | Driver action | System behavior |
|------|---------------|-----------------|
| 1 | **Confirm arrival** | Validates driver is at the right store/aisle context |
| 2 | **Start task** | Opens active pick/delivery task card |
| 3 | **Guide to next item** | Shows what to find next — one item at a time |
| 4 | **Scan / verify item** | Barcode or visual check against expected SKU |
| 5a | **If correct** | Add to cart / basket; mark item done |
| 5b | **If wrong** | Continue searching; system keeps context |
| 5c | **If unavailable** | Report exception; ops sees substitute / skip path |
| 6 | **Repeat** | Loop back to step 3 for next item |
| 7 | **Final review** | Review basket before completion tap; dispatch confirms |

This is a **state machine with a human in the loop** — not a single upload form.

#### Insurance Case Builder IQ — parallel guided flow

| Step | Customer / system action | Broker / backend behavior |
|------|--------------------------|---------------------------|
| 1 | **Confirm active case** | Start Card or lane intent → one active Draft case (B0 Rule 8) |
| 2 | **Ask for next needed document** | System prompts **one** gap: next doc or field from checklist |
| 3 | **Customer uploads photo** | WeCom image/file → download → store |
| 4 | **Verify receipt + doc type confidence** | Ack received; classify by lane context / prompt / filename (no OCR required in P19A) |
| 5a | **If clear** | Attach to case; update checklist → `received` |
| 5b | **If unclear / wrong document** | Ask for clearer or correct document; broker may request re-shoot (P19B+) |
| 5c | **If missing / unavailable** | Mark exception or `manual_handle`; broker follows up offline |
| 6 | **Repeat** | Prompt next needed item until checklist materially complete |
| 7 | **Final broker review** | Broker confirms fields + attachments → close case; customer DONE card |

```text
Spark:     arrive → start → [next item → scan → correct? → cart | retry | exception]* → final review → complete
Insurance: start  → case → [next doc → upload → clear?   → attach | re-ask | manual]*  → broker review → close
```

**What we copy:** the **loop shape** — one guided step at a time, verify each proof, branch on failure, human final gate.  
**What we do not copy:** Walmart colors, aisle maps, cart iconography, or driver earnings UI.

### 1.1 Task card

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **One active task surface** | Driver sees one offer / one delivery at a time | Reduces cognitive load; mobile screen is not a dashboard |
| **Context in the card** | Pickup, drop-off, pay estimate, time window — essentials only | User decides in seconds whether to accept or act |
| **Stateful card** | Card updates as task progresses (accepted → en route → delivered) | User always knows "where am I in this job?" |

**Insurance mapping:** One **active business flow** per customer (B0 Rule 8). Start Card opens a lane-specific task; subsequent messages and photos attach to that case — not a free-form chat thread.

### 1.2 Step-by-step checklist

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **Ordered micro-steps** | "Arrive → scan → photo → confirm" — not one long form | Each step is completable in one thumb action |
| **Visible progress** | Checked items vs remaining | Motivation + clarity on what's left |
| **System prompts next gap** | App asks only for the **next missing** item | No re-typing what user already provided |

**Insurance mapping:** Per-lane document checklist (VIN photo, renewal notice, accident photos, DMV notice). System surfaces **still_needed_fields** and **needed documents** — customer fills gaps, not a full application.

### 1.3 Scan / photo proof

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **Camera as input** | Barcode scan or photo replaces manual entry | Faster, fewer typos, matches what user already has |
| **Proof artifact** | Image is evidence tied to the task | Dispatch / support can verify without re-asking |
| **Immediate ack** | "Photo saved" before backend fully processes | User trusts the action landed |

**Insurance mapping:** Customer sends insurance card, renewal notice, accident photos, DMV letter via WeCom. System stores attachment, binds to case, broker reviews — **photo is proof, not a decision**.

### 1.4 Tap-to-confirm status

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **Large tap targets** | Accept, Start, Delivered, Problem — not free text | One action = one state transition |
| **Explicit consent** | Driver taps to confirm each milestone | Audit trail; no ambiguous "I thought I was done" |
| **Native buttons where possible** | WeCom `msgmenu` / template buttons | Same thumb-first discipline on WeChat |

**Insurance mapping:** Start Card ("开始加车"), lane disambiguation ("这是加车资料 / 保费资料 / …"), upload-intent buttons (P19D). Status moves forward on **tap or short reply**, not long forms.

### 1.5 Exception handling

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **Named exception paths** | Can't scan? Bad address? Customer not home? | User is never stuck in a dead end |
| **Escalation without blame** | "Report issue" → support queue | Driver keeps moving; ops sees the exception |
| **Retry with guidance** | "Take clearer photo of barcode" | Actionable fix, not generic error |

**Insurance mapping:** Ambiguous case binding → ask customer which lane. Download/storage failure → customer ack + broker sees error. Blurry photo → broker requests clearer image. Coverage / claim questions → **manual handle**, never auto-resolve.

### 1.6 Backend review / dispatch visibility

| Pattern | What it means | Why it works |
|---------|---------------|--------------|
| **Ops sees task + proof** | Dispatch dashboard: task state, photos, exceptions | Human can intervene before customer is left hanging |
| **Assignment / ownership** | Task belongs to a queue or agent | Accountability |
| **Customer gets status, not internals** | "Your delivery is on the way" — not warehouse SKU logic | Trust without exposing ops complexity |

**Insurance mapping:** Broker Workbench shows case, attachments, checklist gaps, OCR draft (later), binding confidence. Customer gets safe canned acks ("陈总会人工确认") — **never** coverage decisions or quote promises in chat.

### Pattern summary (reference only — not UI copy)

```text
[Task Card] → [Guided loop per item] → [Verify + branch] → [Final review]
      ↓              ↓                      ↓                    ↓
  Active case    next doc/field      attach | re-ask |      broker Confirm
  one lane       photo proof         exception/manual       → close case
```

Core borrow: **guided micro-steps + verification + exception handling + final review** — not Spark's visual UI.

---

## 2. Mapping to Insurance Case Builder Lanes

Four live lanes from Loop 3B. Each lane is a **mobile task type** with its own checklist and proof types.

### 2.1 Add Vehicle

| Spark pattern | Insurance task |
|---------------|----------------|
| Task card | Start Card → Draft case (`add_car`) |
| Checklist | VIN, delivery date, garaging ZIP, primary driver, phone; docs: registration, VIN photo, insurance card (opt), DL (opt) |
| Photo proof | Temp tag, VIN sticker, insurance card, registration photo |
| Tap confirm | Start → optional "我上传保险卡" / "我上传行驶证" (P19D) |
| Exception | Missing VIN → ask text or clearer VIN photo; second topic mid-flow → flag for broker (Rule 8) |
| Backend | Workbench: Draft fields, attachments, broker Confirm → Active |

**Customer phrase:** "明天提新车，帮我加保险" → photo-heavy, few typed fields.

### 2.2 Premium Review

| Spark pattern | Insurance task |
|---------------|----------------|
| Task card | `policy_review` case from "保险又涨了" / renewal concern |
| Checklist | Current policy or renewal notice; optional: vehicles, usage, claim history fragments |
| Photo proof | Renewal notice, dec page, premium letter (image or PDF) |
| Tap confirm | Lane start implicit or explicit; upload renewal doc |
| Exception | No document yet → ask for photo; **never** auto-quote in reply |
| Backend | Workbench: attachment + OCR draft (P19C) + missing fields; broker: review / compare / call |

**Customer phrase:** "保险又涨了" → document-first, broker explains — system organizes materials only.

### 2.3 Claim Lite

| Spark pattern | Insurance task |
|---------------|----------------|
| Task card | `claim_lite` case from accident report |
| Checklist | Safety first → time/place → photos → other party info (if available) |
| Photo proof | Accident scene, damage, plates, police report photo |
| Tap confirm | Safety confirmation; send photos when safe |
| Exception | Injury implied → urgent / manual handle; missing photos → broker requests |
| Backend | Workbench: photos, received time, urgent flags; **no liability or file-claim decision** |

**Customer phrase:** "我撞车了" → intake + evidence capture, broker handles FNOL guidance offline.

### 2.4 Coverage Risk

| Spark pattern | Insurance task |
|---------------|----------------|
| Task card | `coverage_risk` case from DMV / cancellation / lapse concern |
| Checklist | Notice document, policy number if known, notice date |
| Photo proof | DMV notice, cancellation letter, SR-22-related mail |
| Tap confirm | Send notice photo; system stores — does not interpret coverage |
| Exception | High anxiety messages → calm ack + manual review queue |
| Backend | Workbench: high-risk lane, attachment, OCR draft fields; broker only decides next step |

**Customer phrase:** "DMV 说我没保险" → **highest red-line lane**; system never says "you're covered" or "you can drive."

### Lane × proof matrix

| Lane | Primary proof types | Broker risk |
|------|---------------------|-------------|
| Add Vehicle | registration, VIN photo, insurance card | Medium — data accuracy |
| Premium Review | renewal notice, dec page | Medium — no auto-quote |
| Claim Lite | accident photos | High — timing + emotion |
| Coverage Risk | DMV / cancellation notice | **Highest** — legal/coverage sensitivity |

---

## 3. Customer Mobile — Minimal Actions

Design principle: **thumb-first, chat-native, no forms.** Customer should never feel like they opened a insurance portal.

| Action | Examples | System response |
|--------|----------|-----------------|
| **Send text** | "明天提车" · "保险涨了" · "撞车了" · VIN in message | Intent → lane → Start Card or case create |
| **Tap button** | Start · lane disambiguation · upload intent (P19D) | State transition; high-confidence binding |
| **Photo / upload** | Insurance card, renewal PDF, accident photos, DMV notice | Store → bind case → safe ack (§12 in P19 spec) |
| **Fill few fields** | VIN · delivery date · phone · policy # · garaging ZIP | Merge into `collected_fields`; only ask if not in photo/OCR draft |

### What customer does NOT do

- No multi-page forms
- No account login
- No document type taxonomy selection (unless disambiguation required)
- No waiting on OCR in chat
- No reading Workbench or binding confidence

### Ack timing (non-blocking)

Customer gets **immediate** safe acknowledgement when media is received — even if download/GCS/OCR is still async. Failed storage still gets "message received" tone; broker sees error (P19 spec §12).

---

## 4. Broker Workbench — Corresponding Actions

Workbench is the **dispatch console** — Spark's ops view, not the driver's app.

| Workbench action | When | Outcome |
|------------------|------|---------|
| **See attachment** | Any WeCom image/file on case or unassigned queue | Preview via signed URL / auth proxy |
| **See missing checklist** | Case detail: `still_needed_fields` + document checklist states | Broker knows what to ask customer |
| **Confirm OCR draft** | P19C+: extracted fields with confidence | Selected fields → official `known_facts` / `collected_fields` |
| **Ask for clearer photo** | Blurry, cropped, or wrong doc type | Outbound message or manual WeCom reply |
| **Mark manual handle** | Claim Lite urgent, Coverage Risk, emotional/complex thread | Case flagged; phone-first workflow |
| **Close case** | Work complete or customer resolved offline | Case archived; customer DONE card if applicable |

### Additional broker affordances (P19B+)

- Reassign attachment to different case
- Set / correct document type manually
- Resolve unassigned attachment queue
- Override binding when system confidence was low

**Invariant:** Broker is the **only** path from draft/evidence → official case truth (B0 broker Confirm gate; Constitution Rule 7).

---

## 5. Why P19A First — Attachment Foundation, Not OCR

### 5.1 Dependency chain

```text
WeCom callback detects media
  → download (media_id expires in days)
  → durable storage (GCS)
  → attachment metadata + case binding
  → Workbench visibility
  → [later] OCR draft
  → [later] broker field confirmation
```

OCR without steps 1–5 is **orphan extraction** — no audit trail, no broker preview, no reassign, no retry on failed download.

### 5.2 OCR is P19C draft, not official facts

| Layer | Role | Customer sees | Broker sees |
|-------|------|---------------|-------------|
| **Raw attachment (P19A)** | Source of truth artifact | "收到图片" | Thumbnail + metadata |
| **OCR draft (P19C)** | Suggested fields | Nothing (async, non-blocking) | Draft + confidence |
| **Confirmed facts (P19D/broker)** | Official case data | DONE / progress msgs only | Confirmed fields on case |

OCR **must not** auto-update case facts or trigger customer-facing coverage/quote/claim language.

### 5.3 Broker confirmation required

Aligns with:

- `TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` — Draft until broker Confirm
- ADR-003 — no carrier/policy automation
- P19 spec §13 — safety rules

**P19A acceptance:** WeCom image appears in Workbench on correct case (or unassigned queue); text lanes regress-free; zero OCR.

### 5.4 Preflight readiness

`docs/evidence/p19a_gcs_bucket_preflight_2026_07_05.md` — GCS bucket + IAM **PASS**. Infrastructure gate for P19A Loop 1 is green; implementation still awaits explicit loop kickoff per P19 spec §17.

---

## 6. Big-Tech Best Practice Principles (Applied)

Patterns seen in Uber, DoorDash, Instacart, Spark-class apps — adapted for regulated insurance intake:

| Principle | Meaning for P19 |
|-----------|-----------------|
| **Mobile-first** | WeCom is the UI; Workbench is ops-only |
| **Event never lost** | Raw media event persisted even if download fails; dedup by `msg_id` |
| **Async processing** | GCS upload, OCR, classification off critical reply path |
| **Non-blocking upload acknowledgement** | Customer reply before OCR completes |
| **Human confirmation for high-risk decisions** | Coverage, claims, quotes, policy changes — broker only |
| **Clear exception path** | Unassigned queue, binding disambiguation, storage error visible to broker |
| **Idempotent ingress** | Same WeCom message must not create duplicate attachments |
| **Private artifacts** | No public URLs; auth-gated preview |
| **Observability for ops** | Binding confidence, document type confidence, OCR status on Workbench |

---

## 7. Design Red Lines — Non-Negotiable

These apply to **all** P19 loops (A through E) and customer-facing copy:

| Red line | Rationale |
|----------|-----------|
| **No coverage decision** | Cannot tell customer they are/aren't insured from OCR or chat |
| **No claim/liability decision** | Cannot say "you should/shouldn't file" or infer fault from photos |
| **No quote promise** | Premium Review is review-only; no premium numbers from AI in WeCom |
| **No public image exposure** | GCS private; signed URL or proxy only |
| **No full `external_userid` display** | Mask in Workbench (Loop 3D pattern) |
| **No OCR auto-confirm** | Extracted fields stay draft until broker action |

### Additional guardrails (from P19 spec §13)

- Never tell customer they can or cannot drive (Coverage Risk)
- Never file claim or change policy automatically
- Preserve raw uploaded file for audit
- Show OCR confidence when draft exists — never hide uncertainty

---

## 8. Recommended Next Step

**P19A Loop 1 — WeCom Media Intake Foundation**

| Item | Scope |
|------|-------|
| **In** | Media detection → WeCom download → GCS → metadata → case bind or unassigned → Workbench placeholder → safe customer ack |
| **Out** | OCR, schema migration, full Workbench attachment UI (P19B), guided upload buttons (P19D) |
| **Stop gate** | P19 spec §16 acceptance criteria + `check_chen_kui_demo_environment.sh --cloud-api` + Andy sign-off before P19B |

### Entry checklist (before coding)

1. Read this recon + `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` + B0 contract
2. Confirm GCS bucket preflight evidence (PASS 2026-07-05)
3. Verify WeCom media API from Cloud Run egress
4. Branch from `sprint/p16-trust-layer` at latest stable checkpoint
5. Implement **P19A only** — STOP at acceptance gate

### Phased roadmap (reference)

```text
P19A  Attachment foundation     ← NEXT
P19B  Workbench attachment UI
P19C  OCR draft (optional)
P19D  Customer checklist + upload buttons
P19E  Demo rehearsal (Chen Kui)
```

---

## 9. Recon Verdict

| Question | Answer |
|----------|--------|
| **Is Spark-style workflow applicable?** | **Yes** — task card + checklist + photo proof + tap confirm maps cleanly to four lanes |
| **Is OCR blocking MVP value?** | **No** — attachment + broker visibility delivers demo value first |
| **Safe to proceed to P19A?** | **Yes** — spec complete, Loop 3B stable, GCS preflight PASS, red lines documented |
| **Code changed this loop?** | **No** |
| **Deploy this loop?** | **No** |

---

## Related Documents

| Doc | Role |
|-----|------|
| `docs/p19_wecom_photo_intake_mobile_case_builder_spec.md` | P19 technical + product spec (authority) |
| `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` | One flow at a time; broker Confirm gate |
| `docs/evidence/p19a_gcs_bucket_preflight_2026_07_05.md` | P19A infrastructure preflight |
| `docs/evidence/loop_3b_stable_checkpoint_2026_07_05.md` | Pre-P19 stable baseline |
| `docs/p18_3_vip_driver_business_value_analysis.md` | VIP customer lane business context |

---

*P19 UX Recon loop complete — documentation only. STOP.*
