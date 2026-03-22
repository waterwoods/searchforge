# Attachment Visibility / Broker UX Spec

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Define what broker sees in workbench for attachment presence and still-needed material cues.

---

## 1. What Broker Sees in Workbench

| Element | Content |
|---------|---------|
| **Attachment presence** | "1 attachment" / "2 attachments" / "No attachments" |
| **Attachment list** | Filename, type (registration, vin_photo, dec_page, screenshot), size, date |
| **Still-needed (when no attachment)** | "Registration / dec page optional — can speed up quote" |
| **Still-needed (when attachment present)** | "Materials received — ready for quote" or similar |

---

## 2. Layout and Display

- **Case card (queue):** Small badge: "📎 1" or "📎 2" when attachments exist
- **Case detail (workbench):** Section "Supporting materials" with list of attachments
- **Add-car block:** Quote-ready badge + attachment badge side-by-side when both apply

---

## 3. How This Improves Trust and Reduces Rework

1. **Broker knows what was received** — no need to re-ask "did you send registration?"
2. **Broker sees filename/type** — can prioritize which to review first
3. **Clear still-needed** — when no attachment, broker knows it's optional
4. **Reduced back-and-forth** — customer can upload once; broker sees it

---

## 4. What Still-Needed Says When No Attachment Exists

- **Add-car, quote-ready, no attachment:** "Registration / dec page optional — can speed up quote"
- **Add-car, almost-ready, no attachment:** Same; attachment does not change quote-ready
- **Add-car, need-more, no attachment:** Focus on missing fields first; attachment remains optional

---

## 5. What Still-Needed Says When Attachment Exists

- **Add-car, quote-ready + attachment:** "Materials received — ready for quote"
- **Add-car, almost-ready + attachment:** "Materials received — ask for delivery/driver if needed"

---

*See also: 04_QUOTE_READY_ATTACHMENT_STATE_SPEC.md*
