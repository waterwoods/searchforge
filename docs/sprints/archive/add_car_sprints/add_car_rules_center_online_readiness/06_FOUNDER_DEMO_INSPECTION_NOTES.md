# Add-Car Rules Center — Founder Demo / Inspection Notes

**Sprint:** Add-Car Rules Center Online Readiness  
**Purpose:** What founder should inspect on Vercel and how to explain it.

---

## 1. Where to Inspect

- **URL:** `https://ui-smoky-beta.vercel.app/workbench/add-car-rules` (or production alias)
- **Navigation:** Workbench → 加车报价规则 (or AI Workbench sidebar)

---

## 2. What to Click

1. **Open Rules Center** — Workbench → Add-Car Rules
2. **Edit a field** — e.g. 缺年份车型时问什么（中文）→ change text
3. **Sample preview** — Click "我想加一台X5" or "多轮：2024 90210" → 预览
4. **Check publish** — If "预览模式" badge: publish is disabled (expected online). If no badge: publish enabled (local).

---

## 3. Expected Behavior

| Action | Expected |
|--------|----------|
| Page loads | Rules displayed; no error |
| Edit field | Draft updated; preview uses draft |
| Preview | System reply, collected/still_needed shown |
| Publish (online) | Button disabled; "此环境为预览模式" visible |
| Publish (local) | Button enabled; click → success |
| Restore | Reloads published rules; clears draft |

---

## 4. What to Explain as "Preview-Ready" vs "Fully Publish-Ready"

- **Preview-ready:** Edit + preview work online. Business users can experiment with wording and see results.
- **Fully publish-ready:** Only in local dev. Online (Cloud Run), config is read-only; publish is disabled. To persist changes in production, would need writable volume or manual config update.

---

## 5. One-Liner for Chen Kui

"这是加车报价的规则编辑页面。可以改文案、预览效果。在线环境目前是预览模式，改完不能直接保存；本地可以发布。你可以先试试预览，确认效果后再决定是否在本地发布。"

---

*See also: 05_ACCEPTANCE_CRITERIA.md*
