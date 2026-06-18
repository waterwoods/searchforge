# P16 Real Case Workflow

**Sprint:** P16-CK-REAL-PILOT-SPRINT · Phase 1  
**Case type:** Add-Car only  
**Broker:** Chen Kui (陈魁)

---

## End-to-end flow

```
Customer Message (WeChat)
        ↓
   P16 Intake (paste → workbench)
        ↓
   Broker Review (Collected / Still needed / Next step / Draft)
        ↓
   Office Action (quote packet / follow-up)
        ↓
   Follow-up (customer returns → append)
        ↓
   Completion (draft sent · office has what it needs)
```

---

## Stage 1 — Customer Message

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Customer sends fragmented WeChat bubbles (year, VIN, ZIP, driver, delivery, name/phone in separate messages). Broker receives notification; may delay opening thread. | None |
| **P16** | Same — customer still uses WeChat only | None until broker pastes |

**Time (traditional):** 0 min (passive wait)  
**Time (P16):** 0 min  
**Expected savings:** 0 (no change at this stage)

---

## Stage 2 — P16 Intake

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Broker opens WeChat; scrolls full thread; mentally notes what's said vs missing | None |
| **P16** | Broker copies customer message(s) → pastes into **办公室工作台** | Intake API triages: urgency, route (add-car), extracts fields, generates Collected / Still needed / Next step / Draft |

**Time (traditional):** ~1.5–2.0 min (read + scroll)  
**Time (P16):** ~0.3 min (paste) + ~0.5 min (scan structured output)  
**Expected savings:** ~1.0–1.5 min

---

## Stage 3 — Broker Review

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Broker re-reads bubbles to verify VIN, ZIP, driver; composes WeChat reply from scratch; decides what to tell office | None |
| **P16** | Broker scans Collected / Still needed; light-edits draft; copies to WeChat; sends himself (never auto-send) | Draft reply pre-written; broker_next_step guides action |

**Time (traditional):** ~3.0–4.0 min (extract + draft + office note)  
**Time (P16):** ~1.0–1.5 min (review + edit + copy)  
**Expected savings:** ~2.0–2.5 min

**Pilot evidence:** "Would broker reread WeChat?" → target **NO** on majority

---

## Stage 4 — Office Action

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Office (Wu Miss) re-reads broker's WeChat summary or asks broker to clarify missing fields; builds quote packet | None |
| **P16** | Office reads same structured case (or broker forwards screen summary); acts on Collected / Still needed | Same case view broker saw — no re-extraction |

**Time (traditional):** ~1.5–2.0 min (clarify + organize)  
**Time (P16):** ~0.5 min (read screen / broker handoff)  
**Expected savings:** ~1.0–1.5 min (office-side)

**Pilot evidence:** Office feedback — "Could office act without rereading?"

---

## Stage 5 — Follow-up (append path)

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Customer returns with name/phone or missing VIN; broker re-scrolls entire WeChat thread; re-extracts; may lose earlier fields | None |
| **P16** | Broker appends new customer message to **same case** | Append merges new fields; preserves VIN, ZIP, delivery, driver (integrity-certified P16 Append Sprint) |

**Time (traditional):** ~1.5–2.0 min (re-read + re-organize)  
**Time (P16):** ~0.5 min (paste append + verify Collected updated)  
**Expected savings:** ~1.0–1.5 min (higher on append cases)

**Pilot evidence:** Append used? Y/N · field regression? Y/N

---

## Stage 6 — Completion

| | Human steps | System steps |
|---|-------------|--------------|
| **Today** | Broker confirms office has quote inputs; case closed in broker's head or notes | None |
| **P16** | Broker marks case done (mental or log); office proceeds with quote | Case remains in workbench for reference |

**Time (traditional):** ~0.5 min  
**Time (P16):** ~0.2 min  
**Expected savings:** marginal

---

## Total expected time savings

| Workflow | Typical minutes | Source |
|----------|-----------------|--------|
| **Traditional (incomplete thread)** | ~10.0 min | [`P16_TIME_SAVINGS_MODEL.md`](./P16_TIME_SAVINGS_MODEL.md) |
| **Traditional (complete, no append)** | ~6.5 min | Same |
| **P16 (typical)** | ~3.0 min | Same |
| **Simulation avg saved** | **6.2 min/case** | P16-Z24 battery |
| **Pilot success floor** | **≥ 4 min/case** | Broker-logged per case |

---

## Measurement method

After each real case, Chen Kui estimates:

```
Minutes Saved = (time without tool) − (actual workbench time)
```

Calibrate once at Day 0: _"这条如果不用工具，你要花多少分钟？"_

Log in [`P16_CASE_EVIDENCE_LOG.md`](./P16_CASE_EVIDENCE_LOG.md) and roll up in [`P16_TIME_SAVINGS_TRACKER.md`](./P16_TIME_SAVINGS_TRACKER.md).

---

## Out of scope (this sprint)

- Cancellation cases
- Missing-doc cases
- Auto-send to WeChat
- CRM integration

---

*Phase 1 complete — real case workflow documented.*
