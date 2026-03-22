# Container Alignment Blueprint — Unified Intake

## Purpose

Define how the **gray shell**, **top chrome** (title strip, pilot alert, tabs), and **tab surfaces** share one alignment system so the page reads as a single product, not stacked blocks.

## Layer model (outside → in)

| Layer | Role | Width rule |
|-------|------|------------|
| App route wrapper (`App.tsx`) | Light theme + gray wash | `minHeight: 100%`, background `#e8eaed` |
| Page root (`UnifiedIntakePage`) | Borders + full-bleed gray | Full width of `Content` |
| **Shell column** | Max readable width on large screens | `maxWidth: UNIFIED_INTAKE_SHELL_MAX` (1280), `margin: 0 auto`, horizontal padding `18px` |
| **Chrome** | Title card, `Alert`, `Tabs` | Same width as shell inner content (no nested max-width that differs) |
| **Tab panel** | Customer or broker body | **Full width of shell inner content** — no secondary centered column that disagrees with chrome |

## Alignment invariant (post-sprint)

> The **left outer edge** of the main white customer-entry shell aligns with the **left outer edge** of the white “统一服务入口” strip and with the tab bar content region (modulo Ant Design tab item internal padding).

## What we deliberately did *not* do

- No new grid system or layout component extraction.
- No change to broker tab column ratios or demo queue behavior.
- No change to shell `1280` cap or outer `18px` gutter.
