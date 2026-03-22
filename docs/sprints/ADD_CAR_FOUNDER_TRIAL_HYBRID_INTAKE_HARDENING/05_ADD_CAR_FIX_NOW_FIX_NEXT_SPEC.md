# Add-Car Fix-Now / Fix-Next Spec

## Fix-now (this sprint)

| ID | Item | Rationale |
|----|------|------------|
| FN-1 | **Hybrid structured add-car card** on Customer Entry empty state | Highest ROI: reduces demo-like “pure chat” feel without new backend |
| FN-2 | **Document set + explicit intake decision** | Founder confidence and repeatable trial |

## Fix-next

| ID | Item | Rationale |
|----|------|------------|
| NX-1 | Show hybrid card when `selectedButtonIntent === add_car` mid-flow (optional second path) | Users who tap button first might still want fields |
| NX-2 | Localize composed message / field placeholders for EN-primary trials | Commercial breadth |
| NX-3 | Workbench one-line “Add-car intake path: quick form vs chat” in case metadata | Auditability for broker staff |

## Acceptable-for-trial

- Quote-ready without contact (with human-confirmation hint).
- Attachment optional; no OCR.
- Mixed intent sometimes only in `secondary_issue_note` — acceptable if broker_next_step mentions both.

## Defer

- Carrier APIs, real premium, VIN OCR, CRM, multi-tenant auth, enterprise workflow.
