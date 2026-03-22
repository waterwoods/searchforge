# Acceptance / Attachment-Ready Criteria

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Practical criteria for reduced fake/demo feel, visible document readiness, broker confidence.

---

## 1. Reduced Fake/Demo Feel

- [ ] Add-car flow can accept uploaded files (image, PDF)
- [ ] Upload is optional; flow works without attachment
- [ ] Customer can complete add-car chat-only and hand off

---

## 2. Visible Document Readiness

- [ ] Broker sees attachment count on case card (e.g. "📎 1")
- [ ] Broker sees attachment list (filename, type) in case detail
- [ ] Broker can distinguish "materials received" vs "no materials"

---

## 3. Stronger Broker Confidence

- [ ] broker_next_step mentions "Materials received" when attachment present
- [ ] still_needed says "Registration/dec page optional" when no attachment
- [ ] Quote-ready logic unchanged; attachment does not replace it

---

## 4. Acceptable Simplicity for V1

- [ ] No OCR or extraction
- [ ] No mandatory upload
- [ ] Metadata only: filename, type, size, created_at
- [ ] Broker views files manually (download/open)

---

## 5. Founder Demo Value

- [ ] Founder can create add-car case, upload registration/VIN photo, see it in workbench
- [ ] Founder can show Chen Kui: "Materials received" vs "optional"
- [ ] 4–6 exact test cases documented in Founder Inspection Notes

---

*See also: 07_FOUNDER_INSPECTION_NOTES.md*
