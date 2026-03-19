# Insurance Industry Pack

Insurance-specific intent markers, reply templates, and document labels.

**Purpose:** Tunable without code change. Swappable when adding another industry.

**Load order:** Loaded after common base; overridden by client pack when client overrides exist.

**Files:**
- `markers.json` — Intent detection markers (add_vehicle, payment, cancellation, dmv_help, etc.) and document_items
- `reply_templates.json` — First-turn reply templates (add_car, payment_lapse_expiration, missing_document, etc.)
- `category_templates.json` — Per-category broker_next_step and client_prep (cancellation_warning, payment_lapse_expiration, etc.)
- `add_car_rules.json` — Add-Car Quote next-step prompts (ask_vehicle, ask_zip, ask_delivery_driver)
