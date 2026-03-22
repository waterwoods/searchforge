# Root-Cause Diagnostic Spec

## Biggest root cause (ranked)

1. **`_derive_follow_up_type` used imprecise `sent_markers`**  
   Including standalone **`截图` / `screenshot`** and substring **`发你` / `发我`** meant that *any* mention of a screenshot or “send you” fired **`already_sent`**, even when the sentence was a **question** (e.g. 我可以先发你截图吗).

2. **Short `unclear` category path** (`_build_client_reply_draft`, zh)  
   For `len(text) <= 20`, the code treated substring **`发你`** as evidence of “already sent” and replied **“您是说发过了吗？”** — which matched **要不要先发你** because **发你** appears inside **先发你**.

3. **Broker conversation summary `context_hint`**  
   Scanning the full customer transcript for bare **`发你` / `我发你`** produced **“Client says already sent”** for permission-style lines containing **先发你**.

4. **Payment / cancellation structured hints**  
   `screenshot_sent` and payment “sent notice/screenshot” hints used the same loose OR of 截图 + 发你 without distinguishing prospective permission.

## What this was *not* (primarily)

- **Not mainly a product-design flaw** — the intended playbook (answer permission, then collect slots) was already partially implemented via `_get_prospective_send_materials_lead`, but **ordering and marker breadth** undermined it.
- **Not mainly lexicon** for the trust break — the failure reproduced on generic words (截图, 发你).
- **Partly first-turn tolerance** — very short or doc-only lines without 加车 could still land in `unclear` until 行驶证/registration + prospective routing was added.

## Exact code areas

| Area | File | Functions / region |
|------|------|---------------------|
| Follow-up typing | `triage.py` | `_derive_follow_up_type`, `_is_prospective_send_offer_message`, `_message_claims_completed_material_send` |
| Customer draft | `triage.py` | `_build_client_reply_draft` (`unclear` short branch) |
| Broker summary | `triage.py` | `_build_conversation_summary` |
| Payment hints | `triage.py` | `_build_conversation_summary` payment branch; `_extract_cancellation_fields` |
| Add-car asks / handoff | `triage.py` | `_get_next_ask_for_add_car`, `triage_conversation` handoff / `add_car_materials_sent` / broker_next_step |
| Add-car routing | `triage.py` | `_is_add_vehicle_request`; slot extraction `_extract_add_car_fields`, `_add_car_vehicle_concrete_from_scope` |
| Markers | `configs/industries/insurance/markers.json` | `vehicle_context` |

## Safest high-value fix

Replace **broad substring “sent” detection** with **(A) prospective-send guard first** and **(B) completed-send phrases only** — especially remove **bare 截图/screenshot** and **bare 发你** from automatic “already sent.”
