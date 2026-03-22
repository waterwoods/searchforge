# Baseline Audit — Unified Intake Customer Entry Page

**Sprint**: Unified Intake UI Professionalization  
**Date**: 2026-03-20

---

## What Already Works

- **Strong**: Tab structure (客户入口 vs 办公室工作台) — role clarity
- **Strong**: Quick-start buttons exist (6 actions)
- **Strong**: Client config (ui_copy) for Chen Kui
- **Acceptable**: Welcome copy (welcomeHighlight, welcomeHint)
- **Acceptable**: Conversation flow after submit

---

## What Still Feels Like Demo

- **Biggest**: "模拟演示" button prominent next to title — internal demo signal
- **Biggest**: Big textarea (8 rows when empty) dominates first screen
- **Biggest**: "快速选择" feels like optional chips, not primary path
- Cards use `rgba(255,255,255,0.03)` — dark-theme styling on light background
- `color: 'rgba(255,255,255,0.9)'` on light bg = unreadable (theme mismatch)

---

## What Still Feels Like Internal Workbench

- **Biggest**: URL `/workbench/unified-intake` — "workbench" in path
- **Biggest**: "返回工作台" link in header — internal navigation
- Title "客户入口" is functional, not trust-building
- No explicit "formal insurance service" framing

---

## Biggest Trust Gap

- Trust messaging buried in paragraph; not hero-level
- No explicit "办公室会在1–3个工作日内跟进"
- Page does not say "您的信息会妥善处理" above the fold

---

## Biggest Visual-Structure Gap

- No clear 3-layer structure (Trust → Actions → Free input)
- Textarea and buttons compete; hierarchy unclear
- Dark-theme rgba values on light background — inconsistent
- Card boundaries weak; spacing uneven

---

## Classification Summary

| Area | Rating | Notes |
|------|--------|-------|
| Role clarity | Strong | Tabs work |
| Trust messaging | Weak | Thin, not hero |
| Primary path | Weak | Textarea dominates |
| Visual hierarchy | Weak | No 3-layer structure |
| Professional look | Weak | Theme mismatch, scattered |
| Action prominence | Acceptable | Buttons exist but feel secondary |

---

## High-Value to Improve Now

1. Fix dark-theme color remnants (critical)
2. Create 3-layer structure (Trust → Actions → Free input)
3. Make actions primary, textarea secondary
4. De-emphasize "模拟演示"
5. Add explicit trust in hero
6. White cards, clear boundaries

---

*End of audit*
