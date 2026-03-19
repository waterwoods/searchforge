# Unified Intake Focus Mode + Customer-First Layout Report

**Sprint**: Unified Intake Focus Mode + Customer-First Layout  
**Date**: 2026-03-15  
**Status**: Complete  
**Production URL**: https://ui-smoky-beta.vercel.app/workbench/unified-intake

---

## 1. Sprint theme

- **Theme**: Layout focus and customer-first product presentation
- **Why now**: Product logic is strong; page still felt like a lab/workbench. Chen Kui trial needs a sellable, focused surface. Commercial risk: prospect sees "one tool among many" instead of "this is the product."

---

## 2. Control docs created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/UNIFIED_INTAKE_FOCUS_MODE_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/UNIFIED_INTAKE_FOCUS_MODE_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/UNIFIED_INTAKE_FOCUS_MODE_ACCEPTANCE_CRITERIA.md` |

---

## 3. Baseline audit

| Dimension | Before | Classification |
|-----------|--------|----------------|
| **Left nav** | 200px Sider with Showtime, Experiment Lab, RAG Lab, AI Workbench (10+ items). Unified Intake buried under AI Workbench. | **Distracting** |
| **Header** | KpiBar (P95, Recall, QPS) — lab metrics, not broker-facing | **Distracting** |
| **Central input prominence** | maxWidth 720, padding 24, 6 rows TextArea | **Acceptable** |
| **Customer vs broker role clarity** | Tab labels: "客户入口" / "Broker Workbench" — no explicit role hint | **Weak** |
| **Simulation Assistant** | Button "Simulation Assistant" (English), same visual weight as title | **Weak** |
| **Overall product feel** | Lab tool inside broader platform; one of many routes | **Weak** |

---

## 4. Iteration loop 1

### What changed

- **AppLayout**: On `/workbench/unified-intake` only: hide left Sider; replace KpiBar with product title "保险经纪人智能助手 · Unified Intake"
- **Customer Entry**: maxWidth 720→800, padding 24→32; Title level 3→2; subtitle fontSize 15; TextArea rows 6→8; Simulation Assistant → text button "模拟演示" (de-emphasized)
- **Tabs**: size="large"; tab labels add role hints: "— 客户" / "— 办公室"
- **Page wrapper**: paddingTop 16→12, paddingBottom 24; pilot intro maxWidth 720→800

### What got more focused

- Left nav gone → no competing navigation
- Header simplified → product title instead of lab metrics
- Full-width content area → page feels like a product surface

### What got more customer-first

- Customer Entry area larger and more prominent
- Input box 8 rows (was 6) when empty
- Title level 2, stronger hierarchy
- Simulation Assistant de-emphasized (text button, Chinese label)

### What did not improve

- Pilot intro still above the fold (closable)
- Broker Workbench tab content unchanged in Loop 1

### Whether it was worth it

**Yes.** Left nav removal and header simplification alone make the page feel like a focused product. Customer Entry prominence improved.

---

## 5. Iteration loop 2

### What changed

- **Broker Workbench tab**: Subtitle 办公室工作台：粘贴客户消息，整理 case，查看下一步动作、已收集/还缺什么、草稿回复。确认后再发. Tags: "粘贴 → 整理", "不自动发送". Padding 24→28.
- **Header**: Added "返回应用" link to /workbench for users who land on Unified Intake directly
- **Bug fix**: Added missing `Space` import in AppLayout (runtime error on first deploy)

### What improved vs loop 1

- Broker Workbench feels more office-facing (Chinese copy, trust tags)
- Role separation clearer: Customer Entry = 客户; Broker Workbench = 办公室
- Navigation: users can return to main app

### What still remained weak

- Pilot intro can feel heavy on first load (closable)
- Simulation Assistant panel unchanged (still a modal)

### Whether it was worth it

**Yes.** Broker Workbench copy and role clarity improved. "返回应用" is low-risk UX.

---

## 6. Optional loop 3

**Not used.** Loop 2 delivered sufficient polish. Further changes (e.g. pilot intro default-collapsed, Simulation Assistant panel redesign) would be scope creep. Stopping is correct.

---

## 7. Frontend redeploy result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Production URL** | https://ui-smoky-beta.vercel.app |
| **Unified Intake URL** | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| **Deployment URL** | https://ui-4u8a5d2ax-andys-projects-1f411b73.vercel.app |
| **Alias updated** | Yes — ui-smoky-beta.vercel.app |
| **Warnings** | Chunk size >500kB (pre-existing) |

---

## 8. Post-deploy inspection

### Directly observed

- Page loads without error
- Left nav hidden on Unified Intake
- Header shows "保险经纪人智能助手 · Unified Intake" + "返回应用"
- Tabs: 客户入口 — 客户 | Broker Workbench — 办公室
- Customer Entry: title "客户入口", subtitle, "模拟演示" button, large input, 提交
- Pilot intro visible (closable)

### What now feels better

- Page feels like a product, not a lab tool
- Customer Entry is the obvious starting point
- Role separation clear from tab labels
- No lab metrics in header

### What still feels weak

- Pilot intro above the fold may distract some users (acceptable; closable)
- Simulation Assistant still opens as modal (unchanged)

---

## 9. Final judgment

| Question | Answer |
|----------|--------|
| Did the page become more focused? | **Yes.** Left nav removed, header simplified, content area full-width. |
| Did the page become more customer-first? | **Yes.** Customer Entry larger, input more prominent, hierarchy clearer. |
| Is the customer-entry role now clearer? | **Yes.** Tab "客户入口 — 客户", subtitle for customers. |
| Is the broker-workbench role now clearer? | **Yes.** Tab "Broker Workbench — 办公室", office-facing copy. |
| Does the page now feel more sellable / demo-ready? | **Yes.** Product surface, not lab. |
| What still remains the biggest layout weakness? | Pilot intro above the fold (minor; closable). |
| What should the founder inspect next? | Live demo flow: paste message → triage → handoff; Broker Workbench → Load founder demo queue. |

---

## 10. Iteration log

### Loop 1

- **What changed**: Left nav hidden, header simplified, Customer Entry larger (800px, 8 rows), Simulation Assistant de-emphasized, tab role hints
- **What got better**: Focus, customer-first prominence, no lab metrics
- **What did not improve**: Pilot intro, Broker Workbench content
- **Worth it**: Yes
- **Next step**: Loop 2 — Broker Workbench copy, role clarity

### Loop 2

- **What changed**: Broker Workbench office-facing copy, "返回应用" link, Space import fix
- **What got better**: Role clarity, office framing, navigation
- **What did not improve**: Pilot intro, Simulation Assistant
- **Worth it**: Yes
- **Next step**: Stop; redeploy; report

### Loop 3

- **Used**: No
- **Reason**: Sufficient polish; further changes would be scope creep

---

## 11. 中文宏观总结

- **左侧导航是不是弱化了？** 是。Unified Intake 页面左侧导航完全隐藏，不再分散注意力。
- **中间输入区是不是更明显了？** 是。maxWidth 800，padding 32，输入框 8 行，标题更大。
- **客户入口是不是更像给客户用的？** 是。Tab 标注「— 客户」，副标题明确面向客户。
- **Workbench 是不是更像给助手用的？** 是。Tab 标注「— 办公室」，副标题「办公室工作台：粘贴客户消息…」。
- **页面是不是更像一个可以卖的产品页了？** 是。无左侧导航、无 lab 指标，整体更像产品页。
- **发布以后你让我重点看哪里？** 打开 https://ui-smoky-beta.vercel.app/workbench/unified-intake，看：1) 客户入口是否一眼可见；2) 粘贴消息 → 提交 → 查看工作台 流程；3) Broker Workbench → Load founder demo queue 演示路径。

---

## 12. COPY/PASTE DECISION BLOCK

UNIFIED INTAKE FOCUS MODE SPRINT — FOUNDER SUMMARY

Biggest UI/layout improvement: Left nav hidden + header simplified on Unified Intake. Page now feels like a product surface, not a lab tool.

Biggest remaining weakness: Pilot intro above the fold (closable; minor).

Customer-first clarity: Improved. Tab labels and copy clarify 客户 vs 办公室.

Redeploy: Success. https://ui-smoky-beta.vercel.app/workbench/unified-intake

What to inspect next: Customer Entry prominence and paste→submit flow; Broker Workbench → Load founder demo queue; 返回应用 link when you want to go back to main app.
