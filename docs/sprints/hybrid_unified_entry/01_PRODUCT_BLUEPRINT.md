# Hybrid Unified Entry System — Product Blueprint

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15  
**Scope**: Chen Kui Insurance Unified Entry — Customer Entry + Broker Workbench

---

## 1. Why This Sprint Matters Now

The current Unified Intake page works but feels like a **lab tool** rather than a **product**:

- Customer Entry is a single text area with "需要示例？" — no guided start
- No visible welcome that sets expectations
- No quick paths for common intents (quote, claim, payment, etc.)
- Free text is the only entry; users who don't know what to type may bounce
- Button vs free-text priority is undefined — no rerouting model
- Case creation timing is implicit, not customer-visible

The founder agrees: the product should feel **welcoming**, **easy to start**, **not intimidating**, and **able to guide without forcing**. This sprint upgrades the entry model to achieve that.

---

## 2. How the Current Entry Model Works

| Aspect | Current behavior |
|--------|------------------|
| **First screen** | Title "客户入口" + subtitle + Simulation Assistant link |
| **Entry** | Single TextArea: "请在此输入或粘贴您的问题..." |
| **Guided start** | "需要示例？" reveals link-style example buttons (5 CUSTOMER_ENTRY_EXAMPLES) |
| **Routing** | Backend triage classifies intent; no soft routing from button context |
| **Rerouting** | Not implemented — no button context, no override logic |
| **Case creation** | Implicit when triage returns handoff_ready; no explicit confirmation |
| **Customer vs office** | Tabs: 客户入口 vs Broker Workbench — clear but not emphasized |

**Strengths**: Multi-turn works; triage is solid; handoff flow exists.  
**Weaknesses**: No welcome, no quick paths, no rerouting, no explicit case-creation moment.

---

## 3. What the New Hybrid Unified Entry Should Do Better

| Improvement | Target |
|-------------|--------|
| **Welcome** | Friendly first-line: "How can I help today?" or equivalent |
| **Quick start** | 5 visible buttons for common intents; one click sets soft context |
| **Free text** | Always visible and prominent; user can type at any time |
| **Button + text coexistence** | Buttons are starters; free text can override when intent changes |
| **Rerouting** | When user types something that belongs to another flow, system adapts and acknowledges |
| **Case creation** | Explicit moment: "Would you like me to organize this into a case so our office can follow up?" |
| **Customer vs office** | Clear separation: customer-facing intake vs office-side workbench |

---

## 4. Why This Improves Realism, Conversion, and Product Quality

| Dimension | Impact |
|-----------|--------|
| **Realism** | Feels like a real SaaS intake surface, not a paste-only lab |
| **Conversion** | Lower friction: buttons reduce "what do I type?" anxiety |
| **Product quality** | Guided + free-text hybrid matches how real users behave |
| **Trust** | Explicit case creation and office handoff build confidence |
| **Flexibility** | Free text remains highest-priority truth — no lock-in from buttons |

---

## 5. Design Principle (Non-Negotiable)

**Buttons are only a starter, not a lock. Free text is always the highest-priority truth.**

- Buttons help the user start
- If the user later types something that belongs to another flow, the system adapts
- The system does not keep forcing the original button path if the user clearly changed topic
- The latest real user message overrides the earlier soft routing context when appropriate

---

## 6. Out of Scope for This Sprint

- Full CRM or case history
- Email/SMS/WeChat integration
- Auto-send
- Auth / multi-tenant
- Other verticals

---

*See also: UX/Interaction Design Spec, Routing/State Logic Spec, Case Creation Policy Spec*
