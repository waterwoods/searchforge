# P16 OCR Kill Test — Certification

**Sprint:** P16 Add-Car Packet Builder Kill Test  
**Question:** Should we build Upload-first Add-Car Packet Builder, or rethink product direction?  
**Certification status:** PENDING FIRST RUN

---

## Purpose of this document

This certification answers the kill-test question:

> Is upload-first extraction from real insurance/car purchase documents strong enough to justify building the Add-Car Packet Builder?

It is updated after each test run. The final entry is the binding decision.

---

## Decision Framework

### GO

**Criteria:**
- ≥7/10 test cases generate usable packet drafts
- VIN extraction accuracy ≥90% on documents containing a VIN
- No invented (hallucinated) critical fields detected
- Wu Xiaojie could likely determine quote readiness without WeChat follow-up

**Recommended action if GO:**
Proceed to sprint planning. Build Add-Car Packet Builder as Upload-first flow.
Estimated build scope: 2–3 weeks for MVP (upload endpoint, extraction worker, packet preview UI, office workbench card).

---

### CONDITIONAL GO

**Criteria:**
- 5–6/10 cases usable
- VIN extraction works but needs customer confirmation on some cases
- Customer confirmation step can fix most gaps

**Recommended action if CONDITIONAL GO:**
Build with explicit customer confirmation loop as a first-class step.
Add confirmation UI before packet is sent to office.
Track confirmation-to-resolution rate in production.

---

### NO GO

**Criteria:**
- <5/10 cases generate usable packet drafts
- Frequent hallucinated VIN/year/model
- Cannot reliably detect missing or conflicting fields

**Recommended action if NO GO:**
Do not build upload-first flow. Consider alternatives:
1. **Structured form** — Customer fills guided form; upload as optional supplement
2. **Guided photo capture** — Specific photo prompts (VIN label, reg card, etc.)
3. **Manual triage** — Wu Xiaojie manually enters from uploads (no AI extraction)
4. **Hybrid** — Extraction as suggestion only; manual confirmation for every field

---

## Certification Log

### Run 1 — PENDING

| Field | Value |
|-------|-------|
| Date | Not yet run |
| Provider | — |
| Cases tested | 0 |
| Packet-ready rate | — |
| VIN extraction rate | — |
| Verdict | **AWAITING FIRST RUN** |
| Signed by | — |

**To generate this certification:** Run the kill test and interpret results.

```bash
python scripts/run_p16_ocr_kill_test.py \
  --input-dir test_assets/p16_ocr_kill_test \
  --provider auto
```

Then update this file with:
1. The date and provider
2. The automated verdict from `P16_OCR_KILL_TEST_REPORT.md`
3. Andy's manual override note (if the automated verdict doesn't capture qualitative observations)
4. Final recommended action

---

## How to update this certification

After running the test:

1. Read `docs/trial/P16_OCR_KILL_TEST_REPORT.md` — automated verdict
2. Read `artifacts/p16_ocr_kill_test/results.json` — per-case details
3. Fill in the certification log above
4. Add a qualitative note (did Wu Xiaojie's judgment align with the automation?)
5. Sign off with date

---

## Key questions the test answers

| Question | Tested by |
|----------|-----------|
| Can AI extract VIN from dealer paperwork? | VIN field extraction rate |
| Can AI detect when a document is unrelated? | `unrelated_documents` count |
| Can AI detect conflicting vehicle info? | `conflicts` across cases |
| Are missing fields surfaced clearly? | `missing_fields` list |
| Is the packet draft useful for Wu Xiaojie? | Manual review of `quote_ready_packet_draft` |
| Does the 5–10 min time save hold? | Packet-ready rate × baseline time estimate |

---

## Out of scope for this test

- Customer UI / upload interface
- Production deployment
- CRM integration
- WeChat integration
- Authentication / session management
- Second carrier submission

These are only built if this test returns GO or CONDITIONAL GO.

---

## Commercial context

**Chen Kui and Wu Xiaojie's workflow (current state):**
1. Customer sends documents via WeChat
2. Wu Xiaojie manually extracts VIN, year, make, name, phone from photos
3. Wu Xiaojie drafts add-car packet
4. ~5–10 minutes per request

**Target state (if GO):**
1. Customer uploads documents
2. AI extracts 8 fields automatically
3. Wu Xiaojie reviews conflicts / missing fields
4. Packet is ready in <1 minute

**ROI threshold:** If ≥50% of add-car requests result in a usable packet draft, time savings justify the build.

---

*Kill test certification — not a production deployment record.*  
*See `docs/trial/INDEX.md` for active pilot certifications.*
