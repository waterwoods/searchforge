# Candidate Directions Inventory Spec

**Sprint:** Product Value Review Sprint  
**Created:** 2026-03-19

---

## 1. Candidate List

| # | Direction | Problem it solves | Who it helps most | Why it might matter now | Likely effort/risk |
|---|-----------|-------------------|-------------------|-------------------------|--------------------|
| 1 | **Add-Car Quick Intake Card** | Add-car is high-frequency; broker wants faster entry for common pattern (year+model+zip) | Broker | Add-car is star scenario; quick-fill reduces paste friction | Low–medium; UI + optional backend |
| 2 | **Attachment upload (visible in case)** | Broker receives screenshots/PDFs; today only paste works | Broker, customer | Real office uses attachments; "paste only" feels MVP | Medium; storage, UI, case linkage |
| 3 | **OCR / AI-assisted extraction** | Broker pastes screenshot text manually; OCR would auto-extract | Broker | Reduces manual OCR step; feels "smart" | High; vision API, accuracy, edge cases |
| 4 | **Workbench handoff strengthening** | Broker may not see correction/already_sent; field values not in chips | Broker | Fix-next from pre-trial; reduces rework | Low; UI polish; some backend |
| 5 | **Mixed-intent broker action clarity** | "Also asked" and secondary_issue_note exist; broker visibility may need polish | Broker | 14/14 mixed-intent pass; last-mile visibility | Low; UI/UX polish |
| 6 | **Configuration/template expansion** | Handoff thresholds in triage.py; client variation needs config | Future clients | Enables client B/C without code change | Medium; extraction, testing |
| 7 | **Further add-car refinement** | HT12 correction shows "Bmw" not "BMW X3"; coverage phrasing gap | Broker | Add-car excellence V2; minor polish | Low; extraction logic |
| 8 | **Trial execution improvements** | Founder may stumble; broker may hit trust-breaking moments | Founder, broker | Pre-trial identified fix-next; observation capture | Low–medium; runbooks, small UX |
| 9 | **Billing clarification route fix** | Billing must NOT route to payment_lapse; fix_next in scenario_logic_center | Broker | Trust-breaking if wrong; pre-trial excluded from first 3 | Low; triage logic |
| 10 | **Scenario hardening (remove-car, bundling)** | Remove-car medium maturity; bundling weak | Broker | Extends scenario coverage | Medium; scenario logic |

---

## 2. Per-Direction Detail

### 2.1 Add-Car Quick Intake Card

- **What:** Quick-fill or card for common add-car pattern (year, model, zip, delivery).
- **Problem:** Broker pastes full message; could use structured quick-entry for frequent case type.
- **Who:** Broker doing many add-car quotes.
- **Why now:** Add-car is star scenario; trial will show if quick-entry is requested.
- **Effort:** Low–medium. UI component; optional backend prefill.
- **Risk:** Low. Additive; does not break existing flow.

### 2.2 Attachment upload (visible in case)

- **What:** Upload file (image/PDF); store with case; visible in case card. No OCR in v1.
- **Problem:** Real office receives screenshots; today broker must OCR externally and paste.
- **Who:** Broker, customer (indirect).
- **Why now:** "Paste only" is acceptable for trial; post-trial feedback may prioritize.
- **Effort:** Medium. Storage (S3/GCS or local), UI upload, case linkage, display.
- **Risk:** Medium. New surface; storage cost; no OCR yet so value is "visible in case" only.

### 2.3 OCR / AI-assisted extraction

- **What:** Upload image → OCR → extract text → feed to triage. Or AI-assisted field extraction.
- **Problem:** Broker manually OCRs screenshots; AI could auto-extract.
- **Who:** Broker.
- **Why now:** Deferred in STANDARD_SCENARIO_PACKAGE; CHEN_KUI_TRIAL_PACK says "not yet."
- **Effort:** High. Vision API, accuracy tuning, edge cases, cost.
- **Risk:** High. Accuracy failures = trust-breaking; expensive to do well.

### 2.4 Workbench handoff strengthening

- **What:** Field values in chips (e.g. 2025, Honda CR-V); correction/already_sent visibility polish; queue card enhancements.
- **Problem:** Broker sees summary but not field values in chips; correction badge exists but may need prominence.
- **Who:** Broker.
- **Why now:** Pre-trial fix-next; Workbench Handoff Readiness report identified remaining gaps.
- **Effort:** Low. UI polish; some backend if field values need extraction.
- **Risk:** Low. Incremental; no flow change.

### 2.5 Mixed-intent broker action clarity

- **What:** Ensure "Also asked" and secondary_issue_note are visible and actionable in broker view.
- **Problem:** Mixed-intent handling exists (14/14 pass); broker visibility may need polish.
- **Who:** Broker.
- **Why now:** Sprint just completed; last-mile visibility.
- **Effort:** Low. UI/UX polish.
- **Risk:** Low.

### 2.6 Configuration/template expansion

- **What:** Extract handoff thresholds, category templates to config; enable client B/C variation without code.
- **Problem:** Handoff thresholds in triage.py; client variation requires code change.
- **Who:** Future clients (B, C).
- **Why now:** Pre-trial defer; valuable for scaling but not for first paid pilot.
- **Effort:** Medium. Extraction, testing, documentation.
- **Risk:** Medium. Config drift; regression risk.

### 2.7 Further add-car refinement

- **What:** HT12 correction preference (X3 over X5); coverage phrasing polish.
- **Problem:** Minor add-car edge cases; broker_next_step shows "Bmw" not "BMW X3."
- **Who:** Broker.
- **Why now:** Add-Car Excellence sprint deferred to V2.
- **Effort:** Low. Extraction logic.
- **Risk:** Low.

### 2.8 Trial execution improvements

- **What:** Founder pre-trial checklist polish; observation capture; fix-now queue process; small friction reduction.
- **Problem:** Founder may stumble; broker may hit trust-breaking moments; observations may not convert to fixes.
- **Who:** Founder, broker.
- **Why now:** Trial package exists; execution readiness is next logical step.
- **Effort:** Low–medium. Runbooks, templates, small UX.
- **Risk:** Low.

### 2.9 Billing clarification route fix

- **What:** Ensure billing clarification does NOT route to payment_lapse.
- **Problem:** fix_next in scenario_logic_center; trust-breaking if wrong.
- **Who:** Broker.
- **Why now:** Pre-trial fix-next; excluded from first 3 flows but should be fixed.
- **Effort:** Low. Triage logic.
- **Risk:** Low.

### 2.10 Scenario hardening (remove-car, bundling)

- **What:** Deepen remove-car; improve bundling scenario.
- **Problem:** Remove-car medium maturity; bundling weak; pre-trial excluded bundling.
- **Who:** Broker.
- **Why now:** Extends coverage; lower priority than trial execution.
- **Effort:** Medium. Scenario logic, simulations.
- **Risk:** Medium. Scope creep.

---

## 3. Intentionally Excluded from This Inventory

| Item | Why excluded |
|------|--------------|
| Inbox sync, email/WeChat integration | Out of scope; large integration |
| Carrier API | Out of scope |
| Multi-tenant, auth, Stripe | Out of scope |
| Full CRM | Out of scope |
| Broad refactor | Not a direction; anti-pattern |

---

*End of Inventory Spec*
