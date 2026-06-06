# Hybrid Unified Entry — Routing / State Logic Spec

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. How Button Context Is Stored

| Layer | Storage | Lifetime |
|-------|---------|----------|
| **Frontend** | `selectedButtonIntent: string | null` (e.g., "add_car", "claim_intake") | Until user deselects, reroutes, or starts new conversation |
| **API request** | Optional `soft_route?: string` in triage request body | Per request only |
| **Backend** | Receives `soft_route`; uses as hint; does not persist | Stateless |

**Mapping**: Button ID → intent string

| Button | soft_route value |
|--------|------------------|
| Get a Quote | add_car |
| Policy Change | remove_car |
| File a Claim | claim_intake |
| Payment / Billing | cancellation_warning |
| Upload Documents / Talk to Agent | missing_document |

---

## 2. How Free Text Can Override Current Button Context

| Condition | Action |
|-----------|--------|
| Triage returns `issue_category` that maps to different flow than `soft_route` | Override: use text intent; set `reroute_acknowledged = true` |
| Text is clearly add-car but soft_route was payment | Reroute to add_car; acknowledge |
| Text is clearly payment but soft_route was add_car | Reroute to payment; acknowledge |
| Text is ambiguous | Use soft_route as tiebreaker; no reroute |
| Text reinforces soft_route | No reroute; proceed normally |

**Override rule**: `intent_from_text` != `intent_from_soft_route` AND confidence in text intent is high → override.

---

## 3. When the System Should Switch Intent

| Trigger | Switch? |
|---------|---------|
| Latest message clearly indicates different category | Yes |
| Latest message is follow-up in same flow | No |
| Latest message is ambiguous | No (stay with soft_route if present) |
| User explicitly says "不是这个，是..." | Yes |

---

## 4. When It Should Stay in the Current Flow

| Trigger | Stay? |
|---------|------|
| Latest message adds info (year, zip, "发了") | Yes |
| Latest message asks clarification ("什么意思") | Yes (answer first, then hand off) |
| Latest message is vague ("有个问题") | Yes (ask one focused question) |
| Soft_route matches inferred intent | Yes |

---

## 5. How FAST / LLM / Human Confirmation Fit

| Component | Role |
|-----------|------|
| **FAST (rule-based)** | Quick intent signals (keywords, patterns) |
| **LLM (triage)** | Full classification, summary, draft; can use soft_route as hint |
| **Human confirmation** | For VIN, payment status, customer_says_sent; broker must verify |

Rerouting decision can use:
- Rule-based: e.g., "加" + vehicle → add_car; "cancel" + payment → cancellation
- LLM: when ambiguous, LLM output is truth; soft_route can bias but not override clear LLM result

---

## 6. Soft Route vs Hard Route

| Type | Meaning | Overridable? |
|------|---------|--------------|
| **Soft route** | Button-selected hint; advisory | Yes, by free text |
| **Hard route** | Not used in this sprint | N/A |

We do not implement hard routing. Buttons are always soft.

---

## 7. Reroute Acknowledgment Payload

When backend detects reroute, it can return:

```json
{
  "reroute_occurred": true,
  "previous_soft_route": "add_car",
  "new_intent": "cancellation_warning",
  "reroute_message": "看起来这是付款/取消相关的问题，我先帮您处理这个。"
}
```

Frontend uses `reroute_message` to display acknowledgment and clears `selectedButtonIntent`.

---

## 8. Implementation Notes

- **Triage API**: Add optional `soft_route?: string` to request
- **Triage logic**: Compare `issue_category` to `soft_route`; if conflict, set `reroute_occurred` and `reroute_message`
- **Frontend**: Send `soft_route` when button selected; handle `reroute_occurred` in response

---

*See also: UX/Interaction Design Spec, Case Creation Policy Spec*
