# P16-Z2 Phase 4 — Document Intelligence Research

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Question:** How do best-in-class systems convert Image/PDF/Screenshot → Structured facts → Case?

---

## Insurance document landscape (Chen Kui office)

| Document | Frequency | Typical source | Fields needed |
|----------|-----------|----------------|---------------|
| **Cancellation / UW notice** | Daily (trial wedge) | Carrier email, WeChat screenshot | Carrier, deadline, policy #, reason |
| **Payment / bill notice** | Daily | SMS screenshot, email | Amount, due date, pay link |
| **Claims letter (FNOL)** | Weekly | Mail, email PDF | Date of loss, claim #, adjuster |
| **DMV notice** | Weekly | Mail scan | SR-22, suspension, registration expiry |
| **Driver license** | Per add-driver | WeChat photo | Name, DOB, license #, address, class |
| **Vehicle registration** | Per add-car | Photo/PDF | VIN, plate, owner, expiry |
| **Dec page / ID card** | Per quote | Photo/PDF | Named insured, vehicles, limits, dates |
| **ACORD forms** | Occasional | Email PDF | Full application fields |

**Pilot reality:** 90%+ arrive as **WeChat text** or **screenshot described in text**. Actual image bytes are minority today but **high value when present**.

---

## Industry pipeline (IDP — Intelligent Document Processing)

Best-in-class (Lido, InsurGrid, Datagrid, Scry AI, Roots.ai) use **hybrid OCR + LLM**, not OCR alone:

```
┌──────────┐   ┌────────────┐   ┌─────────────┐   ┌──────────┐   ┌──────────┐
│ Capture  │ → │ Classify   │ → │ Extract     │ → │ Validate │ → │ Route to │
│ (any src)│   │ doc type   │   │ fields+conf │   │ rules    │   │ case/AMS │
└──────────┘   └────────────┘   └─────────────┘   └──────────┘   └──────────┘
```

### Stage details

| Stage | What happens | Insurance-specific |
|-------|--------------|-------------------|
| **Capture** | Email, portal upload, WeChat forward, SFTP | Broker paste + optional attachment |
| **Classify** | "This is a cancel notice" vs "DL front" | Carrier-agnostic; context not coordinates |
| **Extract** | Named insured, dates, amounts, VIN, policy # | Schema per doc type |
| **Validate** | VIN=17 chars; date parseable; amount numeric | CDI/DMV rule checks optional |
| **Route** | Push to case fields or AMS | `collected_fields` merge |

**Key insight (Roots.ai, 2025):** OCR extracts characters; LLM extracts **meaning**. Template-based OCR fails on carrier-specific layouts. Contextual extraction handles "Named Insured" anywhere on page.

---

## Company patterns applicable to us

### Stripe Smart Disputes → Insurance evidence packet

| Stripe concept | Insurance analog |
|----------------|------------------|
| `reason` code | `issue_category` (cancel, payment, claim) |
| `recommended_evidence[]` | `still_needed_fields` |
| `smart_disputes.status: requires_evidence` | Notice mentioned but no image |
| Merge manual + auto evidence | OCR fields + broker paste text |
| `due_by` deadline | `deadline_mentioned` → urgency |
| Auto-submit before timeout | Office alert: "deadline in 3 days" |

### Salesforce Content + Case → Document on record

Files attach to Case; Einstein reads content for classification. We already have `add_attachment_to_case()` + OCR sidecar.

### Zendesk attachment AI → Screenshot triage

Attachments trigger optional AI summary on ticket. Our `v6_ocr_signals` + `ocr_case_fusion.py` are the equivalent — **built, not wired to product UI**.

---

## Document type → field schemas (minimum viable)

### Cancel / UW notice

```yaml
required: [carrier, deadline_or_effective_date]
high_value: [policy_number, named_insured, cancellation_reason]
optional: [premium_amount, payment_link]
urgency_rule: deadline <= 7 days → urgent
```

### Payment notice

```yaml
required: [amount_or_balance, due_date]
high_value: [carrier, policy_number, pay_method]
```

### Driver license (photo)

```yaml
required: [full_name, license_number, expiration_date]
high_value: [address, date_of_birth, class]
validate: license_number format CA
```

### Vehicle registration

```yaml
required: [vin, plate_number]
high_value: [registered_owner, expiration_date, make_model_year]
validate: vin length == 17
```

---

## SearchForge current state (from P16-Z0 Image Archaeology)

| Capability | Status |
|------------|--------|
| Google Vision OCR pipeline | ✅ `image_input_pipeline.py` |
| OCR text → fields | ✅ `parse_ocr_text_to_fields.py` |
| Merge into triage | ✅ `ocr_case_fusion.py` |
| Inline image on triage API | ✅ no product UI caller |
| Broker attachment upload | ✅ workbench; needs Vision keys |
| PDF text extraction | ❌ `pdf_skipped` stub |
| Text-only "发截图了" detection | ✅ `notice_image` in still_needed |
| Primary upload-first intake | ❌ frozen (P16-L) |

**Verdict:** Engine can process images when bytes provided. Trial wedge correctly remains **text paste**. Document intelligence is **Week 2–3 enhancement**, not Week 1 blocker.

---

## Confidence and human-in-the-loop (HITL)

Production IDP systems never auto-write low-confidence fields:

| Confidence | Action |
|------------|--------|
| **≥ 0.85** | Auto-fill `collected_fields`; show in glance |
| **0.60–0.84** | Suggest with "请核实" flag |
| **< 0.60** | Put in summary only; add to `still_needed` |

**Chen Kui trust model:** Broker always sees OCR output before sending to customer. Never silent auto-write to client-facing copy.

**Minimum implementation:** Show extracted fields in broker glance with source tag `[OCR]`. Broker edits or ignores.

---

## PDF strategy (defer vs build)

| Option | Effort | Value for pilot |
|--------|--------|-----------------|
| **Defer** — ask broker to screenshot PDF | Zero | Acceptable for 2–3 weeks |
| **pdftotext** shell conversion | S | Unlocks email PDF forwards |
| **Full PDF IDP** | L | Overkill for 1 office |

**Recommendation:** Defer PDF. Screenshot-of-PDF via phone is how Chen Kui works today.

---

## Document intelligence priority matrix

| Priority | Scenario | Implementation |
|----------|----------|----------------|
| **P0** | Text describes notice content | Already works (triage.py) |
| **P0** | Text says "发截图了" but no image | `notice_image` in still_needed ✅ |
| **P1** | Broker uploads cancel notice screenshot | Wire existing attachment OCR |
| **P1** | OCR merges into collected_fields | Exists; test on pilot keys |
| **P2** | Driver license photo on add-car | Schema + OCR field map |
| **P2** | Customer-facing upload | CustomerEntryTab — hidden |
| **P3** | PDF email attachment | pdftotext or defer |
| **Never** | Full AMS integration | Out of pilot scope |

---

## Anti-patterns from enterprise IDP

| Anti-pattern | Why skip |
|--------------|----------|
| Template per carrier (50+ templates) | Maintenance nightmare for 1 developer |
| Auto-push to AMS without review | Chen Kui won't trust |
| OCR-first intake (upload before message) | Constitution frozen; wrong wedge |
| 99% accuracy marketing requirement | 80% useful + verify beats 0% waiting |
| Multi-language doc support | Chinese + English sufficient |

---

## 2-week document intelligence scope

**Week 1:** Text-only excellence (cancel notice, payment — no OCR changes)

**Week 2:**
1. Enable Vision API keys on pilot deploy
2. Broker attachment upload → OCR → glance fields (existing code path)
3. Show `[OCR]` tagged fields in collected_fields rail
4. P16-Y Y38 battery PASS for notice_image gap

**Week 3 (if trial live):**
1. Customer photo upload on add-car path (CustomerEntryTab)
2. DL/reg field schemas

**Success metric:** Broker uploads cancel notice screenshot → deadline + carrier in glance without manual typing.

---

*End of P16-Z2 Phase 4 — Document Intelligence Research*
