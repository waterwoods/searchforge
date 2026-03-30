# Long-Tail Reply Audit Spec

## Audit Surface
- `services/fiqa_api/inbox_triage/triage.py` (customer reply generation path).
- `services/fiqa_api/inbox_triage/config_loader.py` (template/stitched/handoff loading behavior).
- `configs/industries/insurance/reply_templates.json` (industry base).
- `configs/clients/chen_kui/reply_overrides.json` and `configs/clients/socal_precision/reply_overrides.json` (client override layer).
- Prior sprint runners and scenario batteries for A/B verification pattern.

## Residual Customer-Visible Long-Tail Lines Found In Code
- `missing_signature` zh/en direct literals.
- `underwriting_followup` zh/en direct literals.
- `renewal_reminder` zh/en direct literals.
- `informational` zh/en direct literals.
- Also observed but not selected this sprint: some fallback lines for `unclear`, generic catch-all fallback, and special one-off add-car or handoff edge tails.

## Noticeability / Value
- These four categories appear less often than add-car/missing-document/payment high-frequency paths.
- They are still customer-visible and influence perceived office realism.
- They are ideal for incremental productization and same-industry portability claims.

## Safety Assessment
- Safe now: selected four categories are pure wording outputs after category selection.
- Keep in code for now:
  - Branch-selection and category detection logic.
  - Dynamic retrieval-augmented snippets and slot-collection logic.
  - Ultra-generic final fallbacks where over-externalization may reduce safety/clarity.
