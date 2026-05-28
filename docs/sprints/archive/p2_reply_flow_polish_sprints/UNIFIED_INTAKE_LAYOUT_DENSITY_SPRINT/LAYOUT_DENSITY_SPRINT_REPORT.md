# Unified Intake / Workbench Layout Density + Professional Screen Utilization Report

## 1. Sprint theme

- **Chosen:** Customer Entry = **Stripe-like** formal portal (contained cards, trust-forward). Workbench = **Amazon-style two-pane operations** + **medical/pro-monitoring** clarity (sticky queue, status legibility, less “floating demo”).
- **Why now:** Logic is strong; **visual containment and screen usage** were undermining trust and “real product” perception on wide screens.

## 2. Document set created

- `docs/sprints/UNIFIED_INTAKE_LAYOUT_DENSITY_SPRINT/README.md`
- `01_LAYOUT_DENSITY_BLUEPRINT.md`
- `02_VISUAL_REFERENCE_MIX_SPEC.md`
- `03_CUSTOMER_ENTRY_LAYOUT_SPEC.md`
- `04_WORKBENCH_OPERATIONS_LAYOUT_SPEC.md`
- `05_EXECUTION_OUTLINE.md`
- `06_ACCEPTANCE_CRITERIA.md`
- `07_FOUNDER_INSPECTION_NOTES.md`
- `LAYOUT_DENSITY_SPRINT_REPORT.md` (this file)

## 3. Baseline layout/density audit

- **Strongest current parts:** Meaningful copy and tags in case sheet; demo KPI row; triage tags and “您的下一步” emphasis; light theme for intake inside dark shell.
- **Biggest screen-utilization weakness:** Workbench was a **single narrow-centered stack** (~1180px) with **queue below** the fold—wide monitors showed **empty side margins** and weak “console” rhythm.
- **Biggest professionalism gap:** **No product chrome** tying customer + broker surfaces; pilot alert **narrower than tabs**, reading as bolt-on.
- **Biggest customer-entry density gap:** **800px** column on gray with **no outer portal frame** → “floating card” demo feel.
- **Biggest workbench density gap:** **Vertical-only** layout; queue not **co-visible** with paste/case editing on desktop.

## 4. 10–20 point breakdown

1. **Why it felt floating:** Centered narrow columns on **full-width** content area without a **bounded page shell** or **portal frame**.
2. **Why empty space hurt trust:** Unused horizontal field reads as **unfinished / internal prototype**, not a **deliberate service boundary**.
3. **Stripe-like structure is good for:** **Trust**, **hierarchy**, **one primary surface**, **controlled whitespace** without losing containment.
4. **Amazon-style layout is good for:** **Inventory + detail** (queue + editor), **scan-first operations**, **dense labeled modules**.
5. **Medical-device UI principles are good for:** **Persistent status**, **unambiguous section framing**, **high-signal labels** (borrowed lightly—no alarm chrome).
6. **Do not copy from Stripe:** Marketing page length, pricing density, dev-docs layout on the **customer** side.
7. **Do not copy from Amazon:** Retail navigation/ads; **do not** make intake **operations-dense**.
8. **Do not copy from med monitors:** Alarm aesthetics, ultra-dense vitals grids on **customer** entry.
9. **Customer entry should feel like:** A **formal insurance intake portal**—calm, guided, **one white portal** on neutral rail.
10. **Workbench should feel like:** A **real office console**—**queue visible while working** a case on desktop.
11. **What moved above the fold (desktop):** **演示队列 + 最近 case** in **left column** beside paste/case (xl breakpoint).
12. **Card/container width:** Customer portal **920px** max; page shell **1280px** max for shared chrome.
13. **Screen utilization:** **Two-column xl** workbench; aligned **full-width** alert within shell.
14. **Status visibility:** Unchanged logic; **spatial proximity** of queue to workflow improves **operational scan** (Amazon/med hybrid intent).
15. **What most improves professionalism:** **Product identity strip** + **consistent shell** + **non-floating customer portal**.
16. **What most improves commercial feel:** “This is **one product** with **two modes**,” not two unrelated demos.
17. **Deferred:** Typography scale system, illustration, motion, deep design tokens, responsive tablet-specific tweaks, true split-pane resizable columns.
18. **Founder should inspect visually:** Shell header, customer portal border, workbench **left queue + right workflow** at 1440px.
19. **Future sprints should align to:** Shared **design tokens** for spacing/radius; optional **table-style queue** for even denser ops; screenshot-based **visual regression** for intake.

## 5. Iteration loop 1

- **Fixed:** Customer **portal frame** (white bounded surface, shadow, radius); **wider** column (**920px**); slightly tighter vertical rhythm; introduced shared constants for shell width.
- **Why:** Highest ROI for “not a floating demo” on the **default customer tab**.
- **Feels more professional:** Single **contained** intake surface; less arbitrary gray margin.
- **Did not improve:** Workbench still **single-column** until loop 2; no global typography pass.
- **Worth it:** **Yes**—low risk, immediate trust lift.

## 6. Iteration loop 2

- **Fixed:** Workbench **Row/Col split** (`xl`: **9 / 15**); **演示队列 + 最近 case** moved **left**; **sticky** scrollable queue column; **console header** (title/tags) on **right** above paste; empty-state copy points to **右侧** paste.
- **Why:** Directly attacks **horizontal waste** and **operations scan** without touching backend or queue logic.
- **Improved vs loop 1:** **Meaningful multi-column** usage; queue **co-visible** with triage flow on wide screens.
- **Still weak:** On **smaller laptops**, columns **stack** (queue first)—good for mobile, acceptable tradeoff; KPI grid still **busy** in narrow left column.
- **Worth it:** **Yes**—largest structural professionalism jump for brokers.

## 7. Iteration loop 3

- **Fixed:** **Page shell** (`#e8eaed` rail + **1280px** inner), **product chrome card** (“统一服务入口” + Chen Kui copy), pilot **Alert** full shell width, **Tabs** `tabBarStyle` border, `App.tsx` route background aligned to rail.
- **Why:** Validates **Stripe vs ops** divergence at the **frame** level—customer calm shell, broker dense interior.
- **Improved vs loop 2:** Clear **product identity** and **section boundary** before tabs; less “orphan alert.”
- **Still weak:** No **pixel-perfect** Figma system; chunk-size Vite warnings unchanged; **git** noise on Vercel builder (`fatal: not a git repository`) is **non-fatal** but noisy.
- **Stopping now correct:** **Yes**—diminishing returns without a design-token sprint; current diff is a **clear** commercialization step.

## 8. Validation summary

- `cd ui && npm run build` — **pass** (local).
- Vercel production deploy — **pass** (see §9).

## 9. Deployment / release judgment

- **Frontend:** Deployed to production via `vercel --prod`.
- **Production URL:** `https://ui-lxseuxjyi-andys-projects-1f411b73.vercel.app`
- **Alias:** `https://ui-smoky-beta.vercel.app`
- **Warnings:** Vite large-chunk warning; Vercel build log `fatal: not a git repository` (build still succeeded).
- **Founder can inspect:** **Yes** on production URLs — navigate to **`/workbench/unified-intake`** (path under deployed app as configured).

## 10. Founder inspection list

1. Open **`/workbench/unified-intake`** at **~1440px** width — confirm **top chrome card** + full-width pilot alert.
2. **客户入口** — white **portal** with border/shadow; hero + actions read as **one surface**.
3. **办公室工作台** — **left**: 演示队列 + 最近 case; **right**: header + paste + case sheet.
4. Scroll case sheet on desktop — **left queue** stays **sticky** until viewport height exceeded.
5. **~768px** — columns stack; confirm no horizontal overflow.
6. Watch for **contrast** between **dark app header** and **light** intake (expected nested theme).

## 11. Final judgment

- **Biggest gain:** **Workbench two-pane operations layout** + **customer portal containment** + **shared product shell**.
- **Biggest remaining weakness:** No formal **design system tokens**; queue cards still **card-heavy** vs true data-grid ops UI.
- **More commercial?** **Yes**—materially less “floating prototype,” more **intentional system framing**.
- **Best next step:** Light **design tokens** (spacing, radius, border color) + optional **queue table** variant for broker-only density.

## 12. 中文宏观总结

- **为什么现在做这一轮：** 功能已够演示，但界面仍像「中间一条、两边空」，影响信任与付费意愿。
- **主要改了什么：** 客户入口加「门户框」与加宽；工作台改成宽屏 **左队列 / 右办理**；整页加统一 **产品顶栏与壳层**。
- **最大提升：** 办公室场景更像 **真实操作台**，客户场景更像 **正式服务门户**。
- **还差什么：** 没有完整设计体系/表格化队列；小屏仍是上下堆叠为主。
- **下一步最该做什么：** 定 **设计 token** + 视需要把「最近 case」做成更 **数据表/工单** 密度（仍保持客户页更疏）。

## 13. COPY/PASTE FOUNDER BLOCK

```
本轮最大界面/专业化提升：统一入口加了「产品顶栏 + 页面壳层」；客户入口变成单一白色「门户框」；办公室工作台在宽屏变成左（演示队列+最近 case）右（粘贴+case）双栏，队列可 sticky 对照办理。

最大仍偏弱：还没有完整设计体系/表格化工单列表；左栏变窄时 KPI 四宫格略挤。

需要重新部署吗：已执行 vercel --prod，生产可测。
生产地址：https://ui-smoky-beta.vercel.app（别名） / https://ui-lxseuxjyi-andys-projects-1f411b73.vercel.app
Andy 先 inspect：/workbench/unified-intake → 顶栏 → 客户入口门户框 → 办公室工作台左右分栏。
```

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

宽屏上页面显得空、模块像「漂浮 demo」，削弱信任与商业化观感；需要用 **结构** 而不是花哨动效把产品「框」成正式系统。

### 主要用了什么方法/技术

文档先行（蓝图 + 参考混合 + 双面前后规范）+ `UnifiedIntakePage.tsx` / `App.tsx` 布局改造：门户容器、**Ant Design** `Row`/`Col` 分栏、`sticky` 队列列、统一壳层与 Tabs 分隔。

### 这轮最大的提升

办公室工作台 **左右分栏 + 队列常显**；客户入口 **单一门户面**；整页 **统一产品身份条**。

### 现在还差什么

设计 token、表格化队列、以及更细的断点打磨；未做动效/插画级包装。
