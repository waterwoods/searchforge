# Coverage Gap / Weak Spot Spec

This document ties **observed battery failures** to **likely system causes**. It is based on the run recorded in `battery_run_results.json` (rule path).

## 1. Prospective send vs. already sent (materials / screenshots)

**Symptom (WIRC-004):** Customer asks whether they **can** send a VIN screenshot; system can treat this as **materials already sent**, and the client draft thanks them for having sent documents.

**Gap:** Distinguish **“我可以发…吗？”** (permission / process question) from **“已经发你了”** (completed send).

**Impact:** **Trust-breaking** risk on the customer side.

---

## 2. ZIP / price / channel questions without vehicle yet

**Symptom (WIRC-010 turn 1):** ZIP “贵不贵” + WeChat screenshot habit → **`issue_category: unclear`** with a **notice/clarification** style reply, not add-car oriented.

**Gap:** Short **general questions** that are clearly insurance-shopping but **lack vehicle** may not attach to add-car flow until a later turn.

**Impact:** **Weak** first reply; broker must recover manually. Turn 2 can repair the thread.

---

## 3. Handoff gating vs. “quote_ready” when driver missing

**Symptom (WIRC-006 turn 1):** `handoff_ready: true` and `quote_ready_status: quote_ready` while **`primary_driver` still in `still_needed_fields`**.

**Gap:** Inconsistent **handoff** semantics vs. **slot checklist** for driver.

**Impact:** **Weak** for workbench UX (looks “done” when a key field is explicitly still needed). Broker `broker_next_step` partially mitigates.

---

## 4. Make/model extraction holes (English model names)

**Symptom (WIRC-008):** Clear **“2021 Nissan Altima”** in one message, but structured output behaves as if **make/model** were missing and repeats asks for ZIP/model.

**Gap:** Vehicle **lexicon / pattern coverage** (model token not recognized → `make_model` false).

**Impact:** **Weak**; feels broken to a broker reading the customer message.

---

## 5. Broker summary truncation (make/model)

**Symptom (WIRC-001, WIRC-007 turn 1):** Broker line uses broad **“2024 本田”** instead of **Accord / RAV4**.

**Gap:** Summarization / concrete vehicle string prefers **short** or **brand-level** labels.

**Impact:** **Acceptable** for demo if broker reads customer text, but weak for **at-a-glance** desk work.

---

## 6. Insurance status side effects

**Symptom (WIRC-004):** Flags such as **`insurance_status_new_customer`** appear alongside an **add-to-policy** story (“加进保单”).

**Gap:** Status extraction may **over-trigger** on phrases like **刚买车** without enough disambiguation from **existing policy** context.

**Impact:** **Human confirmation** recommended on broker side before CRM notes.
