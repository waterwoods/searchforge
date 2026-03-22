# Visual Readability / Contrast Fix Spec

**Sprint:** Workbench Demo UX + Visual Bug Fix Sprint

---

## 1. What Areas Are Unreadable Now

- **Lower cards** — "最近 case" section: case cards, tags, preview text, "最近" line
- **Summary stat cards** — 需立即处理, 等客户回复, 队列 case 数, 高风险 case: labels and numbers
- **Demo queue card** — 演示路径 text; Tag "X/13 个 case 已就绪"
- **Paste area** — Secondary text; example cards

---

## 2. Why Current Contrast Is Broken

- **Dark theme inheritance** — Unified Intake is inside App with `theme.darkAlgorithm`
- **Text type="secondary"** — In dark theme, secondary ≈ rgba(255,255,255,0.45); low contrast on dark gray
- **Tag color="default"** — Gray on dark; blends
- **Card backgrounds** — Some use light tints (#f6ffed) on dark; inconsistent
- **fontSize: 11, 12** — Small + secondary = very low contrast

---

## 3. Visual Standards to Restore

| Element | Standard |
|---------|----------|
| Primary text | Dark on light; ≥ 4.5:1 contrast |
| Secondary text | Dark gray on light; ≥ 4:1 |
| Tags | Sufficient contrast; avoid default gray on dark |
| Card backgrounds | Light, consistent; selected state obvious |
| Section headings | Bold, readable |

---

## 4. What Tags/Cards/Text/Buttons Need Improved Contrast

| Component | Fix |
|-----------|-----|
| 最近 case cards | Light theme for workbench content; or explicit light card bg |
| Summary stat cards (需立即处理, etc.) | Light bg; dark text |
| renderRecentCaseCard | Ensure Text not type="secondary" for key info; or use explicit color |
| Tag color="default" | Prefer explicit color (blue, green) where meaningful |
| Demo queue card | Readable labels; Tag contrast |

---

## 5. Root-Cause Targets (Not Cosmetic)

- Bad token/color choice → Use light theme for workbench
- Wrong theme inheritance → Wrap UnifiedIntakePage in ConfigProvider defaultAlgorithm
- Disabled-state styling → Verify button states
- Selected/highlight-only readability → Ensure selected card stands out
- Card background mismatch → Light cards on light page bg
- Text color mismatch → Light theme gives dark text on light
- Tag/badge contrast → Avoid default; use semantic colors
