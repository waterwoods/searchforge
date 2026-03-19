# Included Scenario Matrix Spec

**Purpose:** For each included scenario, define business goal, routing, multi-turn collection, handoff timing, case summary value, office usefulness, commercial importance.

---

## 1. Scenario Matrix

| Scenario | Business goal | Common customer asks | Routing | Multi-turn collection | Handoff timing | Expected case summary | Office usefulness | Commercial importance |
|----------|---------------|----------------------|---------|------------------------|---------------|----------------------|-------------------|------------------------|
| **Quote / Add-car** | New vehicle quote; add car to policy | "我买了台宝马X5，想问下保费多少钱" | LLM → FAST | year, model, zip, delivery, driver | Turn 2–3 when year+model+zip | "报价资料已收集，办公室会尽快出价" | Collected chips; Ready to quote | **High** — revenue |
| **Policy change (remove)** | Remove vehicle from policy | "卖车了，想把2014 Honda Accord从保单拿掉" | LLM | vehicle, sale date, transfer | Turn 2 | "办公室会尽快处理" | Vehicle identified | **Medium** — routine |
| **Material collection / already sent** | Missing document; client says already sent | "UW follow up - need dec page. 上周发过了" | LLM → FAST | item, sent status | Turn 2 | Verify receipt; request still-missing | Verify receipt badge | **High** — common pain |
| **Renewal / premium review** | Premium too high; renewal notice | "保费太高了，能不能便宜一点" | LLM | policy, bill, remove intent | Turn 2 | Review renewal; confirm remove option | Retention follow-up | **High** — retention |
| **Billing / cancellation** | Payment failed; cancellation risk | "这个英文 notice 说 payment failed，我现在怎么办？" | LLM | notice, payment proof | Turn 2 | Same-day action; confirm balance | Urgency badge | **High** — same-day |
| **Claim first notice** | Accident; hit-and-run | "刚出事故了，要收集什么？" | LLM | accident details, photos, other driver | Turn 2 | First-response guidance | Claim intake | **Medium** — time-sensitive |
| **Talk to Agent** | Customer wants human | "我想跟经纪人直接说" | FAST | — | Immediate | Hand off to broker | Broker action | **Medium** — trust |

---

## 2. Routing Model Summary

| Route | When | Examples |
|-------|------|----------|
| **FAST** | Turn 2+ simple patterns; already_sent, what_to_send, add_car_field | FAQ-W1, SIM8, SIM10 |
| **LLM** | Turn 1; mixed intent; unclear | Turn 1; mixed-language; cancellation |
| **Human** | VIN, payment status, customer_says_sent | Add-car VIN; payment proof |

---

## 3. Multi-Turn Expectations

| Scenario | Turn 1 | Turn 2 | Turn 3 | Handoff |
|----------|--------|--------|--------|---------|
| Add-car | Ask year/model/zip | Ask zip if missing | Ask driver if needed | year+model+zip |
| Missing doc | Ask item + sent status | Clarify sent | — | item + sent status |
| Renewal | Ask policy/bill | — | — | policy or bill |
| Cancellation | Ask notice/proof | — | — | notice or proof |
| Claim | First-step guidance | — | — | accident + details |

---

## 4. Case Summary Expectations

| Scenario | conversation_summary | broker_next_step |
|----------|----------------------|------------------|
| Add-car | Intent + Collected (year, model, zip) | Confirm missing driver/ZIP if needed, then quote |
| Missing doc | Item + sent status | Verify receipt; request still-missing |
| Renewal | Premium concern + policy | Review renewal; confirm remove option |
| Cancellation | Same-day action | Confirm balance due |

---

*End of Included Scenario Matrix Spec*
