# P16-Z3 Gap Analysis

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Current level:** Engine L4.5 · Deployed L3.5 · Chen Kui effective L2.5  
**Next target:** Deployed L4.5 (single-turn excellence + L5 UX bridge)

---

## Gap framing

Every gap is scored against the North Star:

> **Does fixing this help transform messy customer communication into an office-executable case faster, more accurately, and more completely?**

Gaps are organized by **what prevents reaching the next maturity level**, not by engineering convenience.

---

## L3.5 → L4.5: Immediate pilot gaps (next 7 days)

These block **Deployed L4** — paste → case ready → next action in Chinese.

### Technical gaps

| Gap | Level | Severity | Root cause | Fix type |
|-----|-------|----------|------------|----------|
| Append summary merge incomplete | L3/L5 | **P0** | Prior bubbles not injected into summary | Engine tune (1–2 days) |
| Generic broker_next_step fallbacks | L4 | **P0** | Template gaps + no blocklist enforcement | Config + rules (1 day) |
| EN/ZH mix in glance | L4 | **P1** | Partial i18n pass | Copy fix (0.5 day) |
| Y44 correction keywords | L5 | **P1** | Correction patterns not in rules | Engine tune (0.5 day) |
| deadline_mentioned → still_needed | L2 | **P1** | Cancel/UW deadline not in gap list | Engine tune (0.5 day) |

### UX gaps

| Gap | Level | Severity | Root cause | Fix type |
|-----|-------|----------|------------|----------|
| **No post-copy append CTA** | L5 | **P0** | Never designed | UX copy (0.5 day) |
| Append box only on reopen | L5 | **P0** | Buried in queue flow | UX promote (0.5 day) |
| client_prep hidden | L4 | **P1** | product_only gate | Ungate (0.5 day) |
| Duplicate-case confusion | L5 | **P1** | UX creates new case accidentally | UX fix (0.5 day) |

### Workflow gaps

| Gap | Level | Severity | Root cause | Fix type |
|-----|-------|----------|------------|----------|
| No "mark sent / waiting on customer" | L8 | **P1** | Missing post-copy workflow step | UX + status (0.5 day) |
| Observation log empty | L9 | **P0** | Process not started | Founder (1 hour) |
| No supervised Day 0 protocol | L9 | **P0** | Not scheduled | Founder (2 hours) |

### Commercial gaps

| Gap | Level | Severity | Root cause | Fix type |
|-----|-------|----------|------------|----------|
| **FP-004 Preview SSO blocks URL** | L0 | **P0** | Founder config | 5-minute toggle |
| Invoice payment IDs empty | L9 | **P0** | Founder admin | 30 minutes |
| No time-saved evidence | L9 | **P1** | No tracking | Process in observation log |

---

## L4.5 → L5.5: Retention gaps (days 8–21)

These block **multi-turn maturity** — broker returns after client reply.

### Technical gaps

| Gap | Level | Severity | Fix |
|-----|-------|----------|-----|
| Premium thread merge (Y45) | L2/L5 | P1 | `bill_sent_claimed` when 发你账单了 |
| Named insured extraction | L2 | P2 | Weak extractor for anonymous paste |
| Carrier name from prose | L2 | P2 | "保险公司说…" disambiguation |
| LLM path unverified | L1/L2 | P2 | Defer — rules at 88.6 |

### UX gaps

| Gap | Level | Severity | Fix |
|-----|-------|----------|-----|
| Continuity score 41/100 | L5 | **P0** | Post-copy CTA + append promote |
| No waiting_on pill after copy | L8 | P1 | Glance pill |
| Follow-up editor hidden | L8 | P2 | Ungate for power users week 2+ |
| Urgent-today queue sort | L1/L8 | P1 | Sort/filter by urgency |

### Workflow gaps

| Gap | Level | Severity | Fix |
|-----|-------|----------|-----|
| Broker doesn't know append exists | L5 | **P0** | Training + CTA on Day 0 |
| No append success metric | L9 | P1 | Log append usage in observation log |
| Chen Kui ui_copy deploy parity | L4 | P1 | Config deploy check |

### Commercial gaps

| Gap | Level | Severity | Fix |
|-----|-------|----------|-----|
| No payment received | L9 | **P0** | Invoice + follow-up |
| No testimonial | L9 | P1 | Day 7 ask |
| No P16-Y CI gate | L7 | P1 | ≥88 pre-deploy |

---

## L5.5 → L6.5: Document intelligence gaps (week 2–3)

| Gap type | Detail | Severity |
|----------|--------|----------|
| **Technical** | Vision API keys not on pilot | P1 |
| **Technical** | OCR fields not in glance with [OCR] tag | P1 |
| **UX** | Attachment upload collapsed by default | P1 |
| **UX** | No inline image paste | P2 — defer |
| **Workflow** | Broker habit is text paste, not upload | P2 — training |
| **Commercial** | OCR not in Day 0 wedge (cancel text works) | P2 — week 2 |

---

## L6.5 → L7.5: Confidence gaps (month 2)

| Gap type | Detail | Severity |
|----------|--------|----------|
| **Technical** | v4/v5 computed but not rendered | P2 |
| **UX** | No「需核实」badge | P2 |
| **UX** | assist_layer env-gated | P3 |
| **Workflow** | Broker doesn't know when to double-check | P2 |
| **Commercial** | No ROI story for risk surfacing | P3 |

---

## L7.5 → L8.5: Lifecycle gaps (month 2–3)

| Gap type | Detail | Severity |
|----------|--------|----------|
| **Technical** | Activity timeline backend-only | P2 |
| **UX** | Customer tab hidden | P2 (week 3) |
| **UX** | 我的办理 status hidden | P2 |
| **Workflow** | No formal outcome enum | P2 |
| **Commercial** | Single office — no queue management need yet | P3 |

---

## L8.5 → L9: Outcome gaps (month 3+)

| Gap type | Detail | Severity |
|----------|--------|----------|
| **Technical** | learning_signals no product loop | P3 |
| **Technical** | audit_export stub | Ignore |
| **UX** | No resolution capture UI | P2 |
| **Workflow** | Observation log → engine feedback manual | P2 |
| **Commercial** | No outcome-based pricing data | P2 |
| **Commercial** | No verified resolution (Zendesk pattern) | P3 |

---

## Gap summary by category

### Technical gaps (engine)

| Priority | Gap | Blocks level |
|----------|-----|--------------|
| P0 | Append summary merge | L5 |
| P0 | Chinese template + blocklist | L4 |
| P1 | Correction keywords (Y44) | L5 |
| P1 | Deadline → still_needed | L2 |
| P1 | Premium thread merge (Y45) | L5 |
| P2 | OCR glance tags | L6 |
| P2 | Risk badge | L7 |

**Key insight:** All P0/P1 technical gaps are **tune existing engine** — not new services.

### UX gaps (deployed surface)

| Priority | Gap | Blocks level |
|----------|-----|--------------|
| P0 | Post-copy append CTA | L5 |
| P0 | Append discoverability | L5 |
| P0 | FP-004 SSO (access) | L0 |
| P1 | client_prep visibility | L4 |
| P1 | waiting_on pill | L8 |
| P1 | EN/ZH fix | L4 |

### Workflow gaps (office process)

| Priority | Gap | Blocks level |
|----------|-----|--------------|
| P0 | Supervised Day 0 | L9 |
| P0 | Observation log discipline | L9 |
| P1 | Mark sent / waiting on customer | L8 |
| P1 | Append training on Day 0 | L5 |

### Commercial gaps (payment)

| Priority | Gap | Blocks level |
|----------|-----|--------------|
| P0 | SSO blocks trial | L0 |
| P0 | Invoice empty | L9 |
| P0 | No payment | L9 |
| P1 | No time-saved evidence | L9 |
| P1 | No testimonial | L9 |

---

## What does NOT block next level (false gaps)

These feel like gaps but are **intentionally deferred**:

| Perceived gap | Why it's not blocking L4.5 |
|---------------|---------------------------|
| Customer tab on Day 0 | Broker paste is wedge; Cap 4 is week 3 |
| Full CRM | Offices have AMS |
| Stripe billing | Manual invoice until 3+ offices |
| LLM generation path | Rules at 88.6 |
| PDF extraction | Text paste handles cancel wedge |
| Mobile optimization | Desktop between WeChat pings |
| P17 platform | Constitution blocked |
| New microservices | Duplicates existing engine |
| Voice/IVR | Out of scope |
| Multi-tenant auth | Single pilot office |

---

## Gap closure sequence

```
Day 1:   FP-004 (L0) → access
Day 2-3: Chinese templates + EN/ZH (L4)
Day 3-4: Post-copy CTA + append promote (L5 UX)
Day 4-6: Summary merge + correction rules (L5 engine)
Day 7:   Day 0 supervised + observation log row 1 (L9 process)
Week 2:  OCR wire + waiting_on + CI gate (L6/L8)
Week 3:  Payment + testimonial (L9)
```

**No step requires new architecture.**

---

*End of P16-Z3 Gap Analysis*
