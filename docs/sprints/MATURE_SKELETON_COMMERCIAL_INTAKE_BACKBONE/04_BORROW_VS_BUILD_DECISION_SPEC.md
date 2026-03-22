# Borrow-vs-Build Decision Spec

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Purpose:** Define what to borrow directly, adapt, build vertical-specific, and defer.

---

## 1. Borrow Directly (Use As-Is)

| Item | Source | Why |
|------|--------|-----|
| **Page hierarchy** (hero → primary → secondary → tertiary) | Stripe | Proven; reduces cognitive load |
| **Card containment** | Stripe | Clear boundaries; professional |
| **Service entry by need** | Amazon-style | Matches our 7 scenarios |
| **Ticket structure** (issue + context + status + next action) | Zendesk | Fits case card |
| **Priority/urgency** (critical, high, medium, low) | Zendesk | Fits broker triage |
| **Handoff context** (what customer said, what's needed) | Intercom | Fits broker_next_step, collected, still_needed |

---

## 2. Adapt (Modify for Our Context)

| Item | Source | Adaptation |
|------|--------|------------|
| **Trust/hero messaging** | Stripe | "Office will follow up" instead of "secure payment"; Chen Kui branding |
| **Primary actions** | Amazon | Our 7 scenarios as quick-start: 获取报价, 保单变更, 报事故, 上传材料, 联系人工 |
| **Flow shape** | Amazon + our skeleton | detect → ask → enough? → hand off (not Amazon's self-service resolution) |
| **Status workflow** | Zendesk | new, reviewing, waiting_client, done (simpler than Zendesk) |
| **Quick actions** | Intercom | client_reply_draft editable; no auto-send; paste-based, not real-time |
| **Collection logic** | Our skeleton | Per-category handoff thresholds; add-car 3 turns; others 2 |

---

## 3. Build Vertical-Specific (Must Be Ours)

| Item | Why |
|------|-----|
| **Add-car multi-turn** | Year, model, zip, delivery, driver; quote-ready; VIN path; coverage/garaging旁问 |
| **Quote-ready visibility** | quote_ready / almost_ready / need_more; insurance-specific |
| **Cancellation urgency** | Same-day action; payment failed; notice interpretation |
| **Missing document + already_sent** | "Verify receipt" when customer says sent; underwriting follow-up |
| **Chinese-speaking tone** | Chen Kui proxy style; conclusion first, next step second |
| **Handoff phrases** | "报价资料已收集..." vs "办公室会尽快处理..."; per-category |
| **follow_up_type** | new_info, correction, already_sent, clarification_question, urgency_question |
| **Human confirmation boundaries** | VIN, payment status, customer_says_sent — broker must verify |

---

## 4. Defer (Not Now)

| Item | Why |
|------|-----|
| **Real-time chat** | Paste-based for pilot; chat is later |
| **Multi-channel inbox** | Email/WeChat sync; not in scope |
| **Full ticketing** | SLA, macros, triggers; too heavy |
| **Team assignment** | Single broker office; no multi-agent |
| **Carrier API** | Quote engine, policy changes; out of scope |
| **OCR / AI extraction** | Attachment visible; no AI parse yet |
| **Stripe billing** | Manual payment for v1 |
| **Multi-tenant auth** | Single broker pilot |

---

## 5. Decision Summary Table

| Category | Count | Examples |
|----------|-------|----------|
| **Borrow directly** | 6 | Page hierarchy, card containment, service entry, ticket structure, urgency, handoff context |
| **Adapt** | 6 | Trust messaging, primary actions, flow shape, status, quick actions, collection logic |
| **Build vertical-specific** | 8 | Add-car, quote-ready, cancellation, missing doc, tone, phrases, follow_up_type, human confirmation |
| **Defer** | 8 | Real-time chat, multi-channel, full ticketing, team assignment, carrier API, OCR, Stripe, multi-tenant |

---

*End of Borrow-vs-Build Decision Spec*
