# Minimal Contact Field Spec

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** Define minimum useful contact fields, required vs optional, when to ask, when chat populates.

---

## 1. Minimum Useful Contact Fields

| Field | Required | When to ask | When chat populates | When can remain missing |
|-------|---------|-------------|---------------------|--------------------------|
| **Name** | Yes (for follow-up) | After quote-ready or when handoff | Customer says "我是张三" / "I'm John" / signs off with name | Until broker needs to call |
| **Phone** | Yes (for follow-up) | After quote-ready or when handoff | Customer says "我电话 626-123-4567" / "call me at..." | Until broker needs to call |
| **Email** | Optional / deferred | V2 or when broker prefers email | Customer provides email | V1: not required |

---

## 2. Required vs Optional

- **Name:** Minimum for "who is this lead." Broker can work with first name only.
- **Phone:** Minimum for "how to reach." Primary follow-up channel for Chen Kui (WeChat/call).
- **Email:** Optional for V1. Many brokers use WeChat/phone first; email can be V2.

---

## 3. When to Ask

- **Not before quote-ready:** Do not interrupt vehicle/zip/delivery flow to ask for name/phone.
- **At handoff or after:** When quote_ready_status is quote_ready or almost_ready, system can prompt: "方便留个姓名和电话，方便办公室联系您？" (or equivalent).
- **Lightweight:** One ask, not repeated. If customer doesn't provide, still_needed shows name, phone.

---

## 4. When Chat Populates

- **Explicit mention:** "我是李四" / "我电话 626-555-1234" / "call me 310-123-4567"
- **Sign-off:** "谢谢，张三" / "— John"
- **WeChat context:** If customer says "微信联系" and we have session, we may defer phone (V2).

---

## 5. When They Can Remain Missing

- **Quote-first flow:** Customer wants quote first, contact later. Case is still actionable; broker sees "Contact: name, phone needed."
- **Handoff without contact:** Broker can still run quote; follow-up requires broker to ask or customer to reply with contact.

---

## 6. Field Keys (collected_fields / still_needed_fields)

| Key | Label (EN) | Label (ZH) |
|-----|------------|------------|
| name | Name | 姓名 |
| phone | Phone | 电话 |
| email | Email | 邮箱 (optional) |

---

*See also: 03_QUOTE_READY_CONTACT_READINESS_SPEC.md, 04_BROKER_CONTACT_VISIBILITY_SPEC.md*
