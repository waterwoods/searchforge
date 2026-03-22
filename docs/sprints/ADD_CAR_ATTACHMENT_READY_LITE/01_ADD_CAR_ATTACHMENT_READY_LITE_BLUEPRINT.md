# Add-Car Attachment-Ready Lite Blueprint

**Sprint:** Add-Car Attachment-Ready Lite  
**Created:** 2026-03-19  
**Purpose:** Extend add-car Real Intake with lightweight attachment support so the flow feels more like real insurance intake.

---

## 1. Why Add-Car Still Feels Lighter Than Real Insurance Intake

| Weakness | What it means |
|----------|---------------|
| **Chat-only materials** | User provides vehicle/zip/delivery via text; no way to upload registration, VIN photo, dec page, or screenshots. |
| **No document visibility** | Broker cannot see whether supporting materials were received. |
| **Demo-like feel** | Real office intake expects registration, VIN photo, dec page; add-car today has none of that. |
| **Broker rework risk** | Broker must re-ask for materials after handoff; no visibility into what was already sent. |

---

## 2. Why Attachment Readiness Matters Now

- **Broker trust:** Chen Kui needs to see that add-car can receive and show supporting materials — not just chat.
- **Trial credibility:** "Real intake" includes document readiness; without it, the flow feels lighter than real office.
- **Commercial value:** Add-car is highest-frequency; attachment support multiplies product realism and trust.

---

## 3. What This Sprint Will Strengthen

| Area | Target |
|------|--------|
| Attachment intake | Add-car cases can accept uploaded materials (registration, VIN photo, dec page, screenshot) |
| Attachment visibility | Broker sees attachment presence, type, filename in workbench |
| Quote-ready + attachment | Clear distinction: Quote-ready vs Quote-ready + attachment received |
| Still-needed clarity | When no attachment: "registration/dec page optional" — not blocking |
| Simulation coverage | Add-car scenarios with attachment-ready behavior |

---

## 4. What This Sprint Intentionally Will NOT Do

- **No OCR** — no document extraction, no auto-fill from images/PDFs
- **No mandatory uploads** — uploads are accelerators, not gates
- **No document intelligence** — no parsing, classification, or auto-decision from documents
- **No complex file pipelines** — lightweight storage and display only

---

## 5. Success Criteria

Add-car feels "attachment-ready for trial" when:

1. Add-car cases can accept and store uploaded materials
2. Broker sees attachment presence, type, filename in workbench
3. Quote-ready logic stays clear; attachment does not replace it
4. Uploads are optional; flow works without them
5. Founder can demo add-car + attachment on Vercel with confidence

---

*See also: 02_ATTACHMENT_INTAKE_SPEC.md, 03_ATTACHMENT_VISIBILITY_SPEC.md, 04_QUOTE_READY_ATTACHMENT_STATE_SPEC.md*
