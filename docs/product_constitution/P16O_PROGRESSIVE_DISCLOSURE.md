# P16-O Phase 4 — Progressive Disclosure

**Date:** 2026-06-01  
**Principle:** Hide complexity until needed

---

## Before First Submit

| Hidden | Rationale |
|--------|-----------|
| IntakeFlowStepTrack | Progress before commitment confuses |
| Transaction banner | Duplicate of progress card |
| Progress card | No conversation yet |
| Structured form fields | Behind 「逐项填写加车信息」 link |
| Category buttons | Message-first infers intent |
| Thread / bubbles | No turns yet |

**Visible:** Headline · subline · textarea · send · trust · footer links · resume hints

---

## After First Message

| Revealed | Default state |
|----------|---------------|
| Flow step track (3 dots) | Visible |
| Progress card | Shows next_best_question prominently |
| AddCarRecordSummaryRail | Collapsed — 「已记录 N 项 · 还缺 M 项」 |
| Thread | Collapsed for add-car pre-handoff |
| Bubble tags / role labels | Hidden |

---

## After Formal Submit

| Revealed | Default state |
|----------|---------------|
| Green confirmation card | Visible — headline + processing line |
| Case reference ID | Visible, copyable |
| Structured snapshot | Collapsed — 「查看整理详情」 |
| Thread history | Collapsed |
| Append panel | Collapsed link label |

---

## My Requests

| Hidden by default | Revealed on select |
|-------------------|-------------------|
| List row updated timestamp | Detail panel only |
| Collected field chips | Collapse — count in label |
| Refresh button | Auto-refresh on window focus |

---

*End of P16-O Phase 4 — Progressive Disclosure*
