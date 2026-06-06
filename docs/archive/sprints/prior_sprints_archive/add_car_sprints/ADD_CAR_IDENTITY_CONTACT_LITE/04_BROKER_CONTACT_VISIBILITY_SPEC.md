# Broker Contact Visibility Spec

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** Define what broker sees in workbench for contact info; how still-needed appears.

---

## 1. What Broker Sees in Workbench

| Element | When present | When missing |
|---------|--------------|--------------|
| **Name** | Display customer_name | "Name needed" or in still_needed_fields |
| **Phone** | Display customer_phone | "Phone needed" or in still_needed_fields |
| **Contact block** | Card or section with name, phone | Same card with "Contact needed" + still_needed tags |

---

## 2. How Collected Contact Info Appears

- **Location:** In case detail, above or beside Collected/Still needed (vehicle fields)
- **Format:** "Name: 张三" / "Phone: 626-555-1234"
- **Editable:** Broker can edit via PATCH /customer (existing API); UI can add inline edit or modal

---

## 3. How Still-Needed Contact Fields Appear

- **In still_needed_fields:** name, phone as orange tags when missing
- **In broker_next_step:** "Confirm name/phone for follow-up" when quote-ready but contact missing
- **In contact block:** "Name needed", "Phone needed" as placeholders

---

## 4. broker_next_step When Contact Missing

When quote_ready_status is quote_ready or almost_ready and (name or phone) missing:

- Append or include: "Confirm name and phone for follow-up." (or zh: "确认姓名和电话以便跟进")
- Do not block handoff; contact is "nice to have before first call"

---

## 5. Contact Block Placement

- In Broker Workbench case detail, add a "Contact" section:
  - If customer_name: show "Name: {value}"
  - If customer_phone: show "Phone: {value}"
  - If missing: show "Name needed", "Phone needed" (or still_needed tags)
- Place after Quote status, before or with Collected/Still needed

---

*See also: 05_EXECUTION_OUTLINE.md*
