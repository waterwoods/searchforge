# ADD-CAR-FIRST WORKBENCH ECHO + BROKER DRY RUN — Blueprint

## Sprint goal

Align the office-side Unified Intake workbench with the **Add-Car-first** story already told on customer entry, so brokers perceive **one pilot product** (same service record, same flagship path) from portal to desk.

## Why now

Customer entry is explicitly Add-Car-first (portal taglines, structured add-car path, pilot intro). The broker tab still read as a **generic** “paste → case → draft” tool: weak echo of flagship path, weak “same case as customer” language, and tab chrome that did not mirror the customer tab’s “suffix” pattern.

## Scope

- Office workbench **language and hierarchy** (headings, tab label, queue/paste chrome, browser title).
- **Terminology** continuity: 服务记录 / 加车报价旗舰路径 / 与客户报送同源.
- **Lightweight** `ui_copy` keys + frontend wiring.
- Sprint docs: blueprint, spec, final report.
- Validation: `npm run build`, mental dry-run walkthrough.

## Non-scope

- Triage engine, case store, API contracts beyond **pass-through `ui_copy` keys** already used elsewhere.
- CRM expansion, auth, billing, broad non–Add-Car hardening.
- Production deploy commands.

## Current entry vs workbench mismatch (summary)

| Area | Customer entry | Workbench (before) |
|------|----------------|-------------------|
| Positioning | Add-Car-first, pilot intro, portal tagline | Generic “整理 case” |
| Tab chrome | Suffix: 报送入口（加车优先） | Suffix: 办公室 only |
| Case identity | 服务记录编号, 加车 framing | “最近 case”, English “case” heavy |
| Continuity | Explicit handoff to office | Little “同源 / 同一服务记录” language |

## Target outcome

Brokers scanning the workbench tab see **the same product thesis** as on customer entry, understand **what came in** as the same **服务记录** world, and dry-run trust improves without new backend intelligence.
