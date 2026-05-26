# Founder Inspection Notes

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** What founder should inspect after this sprint; exact Vercel tests; "good enough to show Chen Kui."

---

## 1. What to Inspect After This Sprint

- [ ] Add-car case accepts file upload
- [ ] Attachment appears in case detail (workbench)
- [ ] Case card shows attachment badge when present
- [ ] Quote-ready + attachment display correctly
- [ ] still_needed / broker_next_step reflect attachment presence

---

## 2. Exact Vercel Test Cases

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 1 | Add-car + upload registration | Create add-car case (BMW X5, 90210, next week). Upload PDF/image. Open case. | Attachment list shows filename; badge "📎 1" on card |
| 2 | Add-car chat-only, no upload | Create add-car case. Do not upload. Hand off. | Quote-ready; still_needed says "Registration/dec page optional" |
| 3 | Quote-ready + attachment | Create add-car case, complete fields, upload VIN photo. | "Quote-ready · Materials received" |
| 4 | Append message + upload | Create case, hand off. Append follow-up. Upload dec page. | Attachment appears; case updated |
| 5 | Multiple attachments | Upload registration + VIN photo. | Both appear in list; badge "📎 2" |
| 6 | Non-add-car case | Create missing_document case. Try upload. | Upload works (or gracefully disabled for non-add-car) |

---

## 3. What "Good Enough to Show Chen Kui" Looks Like

- Broker sees: "This add-car case has 1 attachment (registration.pdf)"
- Broker sees: "Quote-ready · Materials received" when both apply
- Broker sees: "Registration/dec page optional" when no attachment
- No broken UI; no mandatory upload blocking flow

---

## 4. What to Watch For

- File size limits (10 MB default)
- Supported types (image/*, application/pdf)
- Storage path (local vs prod)
- Attachment persistence across case append

---

*See also: ADD_CAR_ATTACHMENT_READY_LITE_REPORT.md (final report)*
