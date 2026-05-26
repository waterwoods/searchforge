# Current Transaction Title Spec (Add-Car)

## Goal

The customer should feel: **“I am currently handling Add-Car Quote / 加车报价.”**

## Signals (stacked)

1. **Persistent ribbon** (when Add-Car context is active and conversation has started)  
   - **Title:** e.g. `当前办理：加车报价`  
   - **Subtitle:** one line explaining this is a formal request flow, not casual chat.

2. **Progress card** (while `handoff_ready` is false)  
   - Card title switches from generic `整理中` to **`加车报价 · 进度`** when Add-Car is detected.

3. **Composer hint**  
   - When Add-Car: label **`当前办理`** + tag **加车报价** (replacing generic “当前主题” for this flow).

## Detection rules (client)

Treat as Add-Car active when any of:

- Soft route `add_car` is selected, or  
- Last triage has `quote_ready_status`, or  
- Structured fields include add-car slots (`year`, `make_model`, `zip`, `delivery_date`, `primary_driver`, `vin`), or  
- Inferred focus from category/fields/text is **Add car quote**.

## Config keys (`ui_copy.json`)

| Key | Purpose |
|-----|---------|
| `add_car_transaction_title` | Ribbon title |
| `add_car_transaction_subtitle` | Ribbon subtitle |
| `add_car_progress_card_title` | Progress card title when collecting |

## Out of scope

Renaming unrelated intents; changing broker-only taxonomy.
