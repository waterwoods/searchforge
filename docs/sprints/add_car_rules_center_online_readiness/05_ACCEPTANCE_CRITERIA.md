# Add-Car Rules Center Online Readiness — Acceptance / SLA Criteria

**Sprint:** Add-Car Rules Center Online Readiness  
**Purpose:** Practical criteria for "good enough online."

---

## 1. Business-User Clarity

- [ ] Page title and subtitle explain what the page does
- [ ] Editable fields have business-friendly labels (no engineering terms)
- [ ] Flow structure (收集顺序, 转办公室条件) is visible and read-only
- [ ] Sample preview buttons exist and work

---

## 2. Online Safety

- [ ] Publish is disabled when backend reports `publishable: false`
- [ ] When disabled, explanatory text is visible ("此环境为预览模式")
- [ ] No misleading "发布后生效" when publish will fail

---

## 3. Preview Usefulness

- [ ] User can type or click sample input
- [ ] Preview returns client_reply_draft, collected_fields, still_needed_fields
- [ ] Preview uses draft when user has edited

---

## 4. Non-Confusing Publish Behavior

- [ ] Publish enabled only when backend can persist
- [ ] Restore always available
- [ ] Draft vs published state is understandable

---

## 5. Founder Can Confidently Inspect/Demo

- [ ] Page is reachable on Vercel (Workbench → 加车报价规则)
- [ ] Founder can show: edit → preview → (publish or "预览模式" explanation)
- [ ] No unexpected 503 or confusing error when clicking publish in production

---

## 6. Definition of "Good Enough Online"

Minimum bar: Andy can open the page on Vercel, show Chen Kui or an assistant the flow, edit a rule, run a preview, and explain honestly that "publish works locally; online we're in preview mode for now" — without confusion or embarrassment.

---

*See also: 06_FOUNDER_DEMO_INSPECTION_NOTES.md*
