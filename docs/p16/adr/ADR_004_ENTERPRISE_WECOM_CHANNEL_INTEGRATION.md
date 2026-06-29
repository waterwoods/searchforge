# ADR-004: Enterprise WeCom Channel Integration

**Date:** 2026-06-26  
**Sprint:** P16 Channel Evolution  
**Status:** Proposed — Architecturally Approved (pending pilot gate)  
**Authority:** Supersedes Decision Freeze §4 “WeChat native integration” **for Enterprise WeCom only**  
**Does not supersede:** ADR-001, ADR-002, ADR-003  
**Related:** `docs/p16/P16_DECISION_FREEZE_V1.md` · `docs/p16/P16_REQUEST_FRAMEWORK.md` · `docs/p16/P16_FUTURE_VISION.md`

---

## Decision

**Insurance Case IQ is channel-agnostic.** Any future communication platform integrates through the same **Channel Adapter contract** — not by forking the AI Engine.

**Enterprise WeCom is Channel Adapter #1** — the first official customer channel after Web Intake. It is transport and identity only. The product remains **Insurance Case IQ** (Unified Intake + Readiness + Trusted Packet + Broker Inbox).

Personal WeChat automation remains **permanently rejected**.

Web Intake remains the canonical reference implementation. WeCom and all future channels are equal downstream consumers of the same extract → readiness → packet path.

---

## Problem

Chinese insurance brokerages operate inside WeChat. Customers send unstructured, multi-modal evidence across days:

- text, photos, voice, insurance cards, police reports, PDFs, videos, random follow-ups

Brokers spend most of their time reading, finding, re-asking, organizing, copying, and remembering — before they can create a case or quote. P16’s web intake solves this for customers who use a link, but **does not meet customers where they already are**.

Decision Freeze and Request Framework explicitly exclude “WeChat Bot” and “WeChat native integration” for V1 pilot scope — paste/link only.

---

## Current Limitation

| Limitation | Impact |
|------------|--------|
| Web-only primary intake | Broker must push a link; friction in WeCom-native workflows |
| Manual WeChat thread reading | ~10 min/case hunting evidence (Decision Freeze §1) |
| Paste/link only | No automatic capture of inbound WeCom messages |
| Personal WeChat excluded | Correct — but Enterprise WeCom was lumped into the same exclusion |
| No channel abstraction | Risk of building one-off integration per platform |

The intelligence layer (extract, readiness, packet) is proven on web. The **channel gap** is the missing piece, not the engine.

---

## Business Motivation

- Brokers already live in WeChat/WeCom; the pain is **information chaos**, not quoting
- Enterprise WeCom is a **legitimate enterprise channel** for Chinese brokerages — but not the product
- Same AI engine serves Web, WeCom, and future channels — no second product
- Wedge remains: **Trusted Packet saves broker time** (Decision Freeze north star)
- Revenue path unchanged: Chen Kui pilot → 10 cases → $49 invoice

---

## Architecture

### Layer model

```
┌─────────────────────────────────────────────────────────────┐
│  CHANNELS (transport only — swappable adapters)             │
│  Web Intake · Enterprise WeCom (#1) · Email · SMS · …       │
└───────────────────────────┬─────────────────────────────────┘
                            │  Channel Adapter Contract
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  INSURANCE CASE IQ (product — channel-agnostic)             │
│  Ingest · GCS · Extract · Readiness · Case Builder · Packet │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  BROKER SURFACES (unchanged)                                │
│  Broker Inbox · Trusted Packet · Suggested Reply · Copy All │
└─────────────────────────────────────────────────────────────┘
```

### Channel-agnostic principle

> **Insurance Case IQ is channel-agnostic. Any future communication platform should integrate through the same Channel Adapter contract.**

Insurance Case IQ 不绑定企业微信。企业微信只是第一个正式 Channel。未来 Email、SMS、WhatsApp、LINE、网页、电话转写，都应该通过同一个 Channel Adapter 合约接入，而不是为每个渠道重写一套 AI Engine。

### Enterprise WeCom as Channel Adapter #1

```
Enterprise WeCom
       ↓
WeCom Channel Adapter (implements Channel Adapter Contract)
       ↓
Insurance Case IQ (Intelligence Layer — unchanged)
  ├── Ingest normalized events
  ├── Store media in GCS
  ├── Run extraction (Gemini Flash 2.5)
  ├── Compute readiness (ADR-001)
  ├── Assemble Trusted Packet
  └── Persist case (Postgres / service_records)
       ↓
Broker Inbox + Trusted Packet + Suggested Reply
       ↓
Broker Action (manual — ADR-003)
```

**Stack (frozen):** Cloud Run · FastAPI · Postgres · GCS · React broker UI on Vercel

### Channel Adapter Contract (all channels)

Every adapter — Web reference, WeCom (#1), and future channels — implements the same boundary:

| Responsibility | Owner |
|----------------|-------|
| Receive platform webhooks / events | Channel Adapter |
| Download and store media to GCS | Channel Adapter |
| Map platform identity → P16 case identity | Channel Adapter |
| Emit normalized intake events | Channel Adapter → Insurance Case IQ |
| Send broker-approved replies | Channel Adapter (outbound) |
| Extraction, readiness, packet assembly | **Insurance Case IQ only** |
| Broker Inbox, Trusted Packet, Copy All | **Insurance Case IQ only** |

**Normalized event types (conceptual):** `message.received` · `media.received` · `identity.bound` · `reply.send`

**Adapter must NOT:**

- Run extraction or readiness rules
- Assemble packets
- Call carrier or AMS systems
- Store business logic divergent from other channels

---

## Design Principles

1. **Insurance Case IQ is the product; channels are adapters.** WeCom is Channel Adapter #1, not a product name or fork.

2. **Insurance Case IQ is channel-agnostic. Any future communication platform should integrate through the same Channel Adapter contract.**

   Insurance Case IQ 不绑定企业微信。企业微信只是第一个正式 Channel。未来 Email、SMS、WhatsApp、LINE、网页、电话转写，都应该通过同一个 Channel Adapter 合约接入，而不是为每个渠道重写一套 AI Engine。

3. **Reuse existing AI Engine, Case Builder, Trusted Packet, Broker Inbox.** No per-channel intelligence fork.

4. **One readiness model (ADR-001) across all channels.**

5. **One packet format across all channels.**

6. **Source attribution applies to all channel media** (e.g. `from: wecom_message_id / filename`).

7. **Never depend on personal WeChat automation** — no RPA, no unofficial hooks.

8. **Evolution, not replacement** — Web Intake remains first-class; new channels are additive.

9. **Channel metadata is additive** — no fork of case schema for channel-specific logic.

10. **Suggested Reply is assistive** — broker reviews; ADR-003 language rules apply.

11. **Fail closed on identity ambiguity** — do not silently merge unrelated threads into one case.

---

## Non-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Personal WeChat bot / automation | Unofficial, unstable, out of scope |
| “WeCom AI” or “Enterprise WeChat product” as branding | Product is Insurance Case IQ |
| Per-channel AI Engine or Case Builder | Violates channel-agnostic principle |
| Carrier API / quote automation | ADR-003 |
| Timeline UI | ADR-002 |
| Any channel as CRM or policy system | Decision Freeze §4 |
| Customer login / accounts | Phone + link + channel identity only |
| Autonomous follow-up without broker gate | Future Vision Business Loop — not V1 channel work |
| Multi-tenant platform | Single pilot broker first |

---

## Future Evolution

### Channel roadmap (same contract, different adapters)

| Channel | Adapter status | Notes |
|---------|----------------|-------|
| **Web Intake** | Reference implementation | Canonical `/add-car` path today |
| **Enterprise WeCom** | **Channel Adapter #1** | First post-pilot official channel |
| Email | Future adapter | Same contract |
| SMS | Future adapter | Same contract |
| WhatsApp | Future adapter | Same contract |
| LINE | Future adapter | Same contract |
| Phone / call transcription | Future adapter | Same contract |

**Rule:** New channel = new adapter implementing the Channel Adapter Contract. **Never** new AI Engine.

### Phased delivery (WeCom as Adapter #1)

| Phase | Scope |
|-------|-------|
| **Now** | Web intake + pilot (frozen) |
| **ADR-004 Phase 1** | WeCom Adapter: inbound text + image → existing add-car path |
| **Phase 2** | WeCom Adapter: PDF, voice (transcribed), multi-message thread binding |
| **Phase 3** | Suggested Reply outbound via WeCom Adapter; bilingual templates from `document_guidance` |
| **ADR-005** | Active Case + evidence append — `docs/p16/adr/ADR_005_ACTIVE_CASE_CONSOLIDATION.md` (implementation gated) |
| **Post-gate** | Business Loop auto follow-up (Future Vision §2) |
| **Future channels** | Email / SMS / WhatsApp / LINE / phone — new adapters only |

---

## Risks

| Risk | Mitigation |
|------|------------|
| WeCom corp onboarding friction | Pilot with one broker corp; document setup runbook |
| Identity mismatch (WeCom user ≠ phone) | Explicit binding step; BROKER_REVIEW on ambiguity |
| Multi-message → multi-case rows | Document as known gap; ADR-005 Active Case addresses |
| Voice/video processing cost/latency | Phase 2; async transcription; do not block packet for media |
| Scope creep (“build WeCom CRM”) | Adapter boundary enforced in code review |
| Per-channel fork temptation | Channel Adapter Contract + channel-agnostic principle in ADR |
| Regulatory / data residency | GCS + Cloud Run US-West; disclose in broker agreement |
| Suggested Reply over-promises | ADR-003 language templates; broker approval required |
| Pilot distraction | Gate: 10 cases + paid invoice before Phase 1 build |

---

## Migration Strategy

1. **No breaking changes** to web intake or existing API contracts.
2. **Add** `channel` field on cases (`web` | `wecom` | `mixed` | future values).
3. **WeCom Channel Adapter** deployed as separate Cloud Run service or route module — isolated credentials.
4. **Broker Inbox** shows channel badge; packet view unchanged.
5. **Parallel operation:** broker sends web link OR customer uses WeCom — same office outcome.
6. **Rollback:** disable WeCom webhook; web path unaffected.
7. **Future channels:** register new adapter; no engine changes.

---

## Development Phases

### Prerequisite gate (mandatory before Phase 1 code)

- CK-001 … CK-010 completed
- Average ≥4 min saved documented
- First $49 invoice paid
- Chen Kui or Wu Xiaojie explicit request for WeCom

### Phase 1 — WeCom Adapter MVP (inbound capture)

- WeCom corp app + webhook endpoint
- Text + image → GCS + append to case
- Route to existing intake/extract path
- Broker Inbox shows WeCom-sourced cases

### Phase 2 — Thread continuity

- Multi-message session binding
- PDF + file types aligned with web MIME allowlist
- Voice → transcription → text evidence

### Phase 3 — Outbound assist

- Suggested Reply from readiness gaps
- Broker approves before send
- Bilingual templates (existing `document_guidance` pattern)

### Phase 4 — Multi-channel case merge (depends on ADR-005)

- Same customer on web + WeCom → one Active Case
- Packet merge rules; VIN conflict → BROKER_REVIEW

---

## Reconsideration Trigger

This decision is revisited if:

1. Pilot gate is not met — defer all channel adapter work
2. Broker explicitly rejects Enterprise WeCom — evaluate next channel (Email/SMS) via same contract
3. Tencent API changes materially — adapter update only; engine unchanged

---

## Consequences

- **Product identity preserved.** Insurance Case IQ remains the product name and intelligence owner.
- **WeCom is not a wedge rebrand.** Channel Adapter #1 only.
- **Future channels are cheap architecturally.** Adapter work only; no engine rewrite.
- **Decision Freeze §4 amended** (when accepted): Personal WeChat automation rejected; Enterprise WeCom per this ADR post-pilot gate.
- **Active Case consolidation** — see ADR-005 (`ADR_005_ACTIVE_CASE_CONSOLIDATION.md`); WeCom Phase 2+ blocked until resolver deployed.

---

*Related: `ADR_001_REQUEST_READINESS.md` · `ADR_002_NO_TIMELINE_V1.md` · `ADR_003_NO_CARRIER_API_V1.md` · `ADR_005_ACTIVE_CASE_CONSOLIDATION.md` · `docs/p16/P16_DECISION_FREEZE_V1.md`*
