# TOP 30 Workbench Improvements — P11

**Sources:** P10 WORKBENCH_AUDIT, BrokerWorkbenchTab UX, CUSTOMER_LANGUAGE_GUIDE, broker trial docs.  
**Perspective:** Chen Kui office — valuable vs confusing vs engineer leftovers.

---

## What feels valuable

- **下一步** preview on queue cards without opening case  
- **已收集 / 还缺** chips on case detail  
- **当日处理 / 需核实收到** queue readiness labels  
- Editable draft + copy to WeChat workflow  
- **加载演示队列** for safe learning  
- Cancellation urgency obvious when demo queue loaded  
- Human confirmation badge when AI collected data  
- Reopen case + paste follow-up continuity  
- Work now vs waiting queue split  

---

## What feels confusing

- Four tabs; trial docs assume one (办公室工作台)  
- Add-Car-first messaging vs cancellation-first demo  
- Mixed 中文 + English ("case", "Unified Intake" in nav)  
- Too many queue tags on one card  
- 演示队列 vs real paste workflow unclear  
- 客户报送 vs 办公室工作台 — two doors, no clear "broker start here"  
- Pilot intro alert wall of text  
- 我的办理 tab purpose unclear  
- Filter labels (镜像异常, 旧识别, 测试, 正式) meaningless to broker  

---

## What feels like engineer leftovers

- `PG 已镜像` / `PG 缺失` / `镜像不一致` tags  
- `路由/指标` debug tag  
- `数据接口` + localhost/API URL in queue header  
- Segmented filters: 镜像异常, 旧识别, 测试, 正式  
- Monospace 服务记录编号 everywhere  
- `13/13 个 case 已就绪` (English "case")  
- workbench_lane_kind, quote_ready_status internal labels  
- SIM1–SIM3 references in operator scripts  
- Platform/lab sidebar routes if product-only leak  

---

## TOP 30 Improvements (ranked by broker payment ROI)

| # | Improvement | Priority | Notes |
|---|-------------|----------|-------|
| 1 | Default trial URL to 办公室工作台 (`?tab=broker`) | **P0** | Fixes #1 Day-1 failure |
| 2 | Hide API endpoint label in product-only UI | **P0** | Instant trust |
| 3 | Hide PG mirror tags + trust line in product-only | **P0** | "Not finished" signal |
| 4 | Hide 路由/指标 debug tag in product-only | **P0** | Pure broker surface |
| 5 | One-line wayfinding: "经纪人：请在本页粘贴客户消息" | **P0** | Replaces tab confusion |
| 6 | Auto-open cancellation case after demo queue load | **P1** | First value moment |
| 7 | Inline 练习场景 panel (3 scenarios) — replace hidden Simulation | **P1** | Playbook works on prod |
| 8 | Replace "case" with 服务记录 in broker-visible strings | **P1** | Language consistency |
| 9 | Paste area copy: "原样粘贴微信/通知文字，不用整理" | **P1** | Sets workflow expectation |
| 10 | First-request loading: "首次分析约30秒" | **P1** | Prevents "broken" abandon |
| 11 | Demo queue progress: "正在加载13条示例 (3/13…)" | **P1** | Prevents 30s abandon |
| 12 | Prominent **复制案例快照** for support | **P1** | Faster L2 escalation |
| 13 | Collapse pilot intro alert by default (production) | **P1** | Less Day-0 overwhelm |
| 14 | Simplify queue filters → 全部 / 需今天处理 / 24小时内 | **P1** | Remove engineer filters |
| 15 | Draft copy button: 复制到微信（请先修改） | **P1** | Reinforces control |
| 16 | Highlight **更新客户新消息** when case selected | **P1** | Follow-up discoverability |
| 17 | Reconcile Add-Car-first banner with cancellation demo | **P1** | Product story decision |
| 18 | Reduce queue card tags (max 3 + expand) | **P2** | Scanability |
| 19 | Rename 高风险 → 需当天处理 | **P2** | Clearer urgency |
| 20 | Short 服务记录编号 in list; full on detail | **P2** | Less monospace noise |
| 21 | Sticky **下一步** + draft on case detail scroll | **P2** | Action always visible |
| 22 | Footer: 支持微信 XXX · 不自动发送 | **P2** | Support + trust |
| 23 | Empty queue: 3-step GIF "paste → review → copy" | **P2** | Zero-state onboarding |
| 24 | Align BROKER_ONE_PAGER labels with UI (加载演示队列) | **P2** | Doc/UI parity |
| 25 | Hide 管理 → 标为测试 from non-founder builds | **P2** | Less accidental misuse |
| 26 | Hide 我的办理 tab in broker-only trial mode | **P2** | Single front door |
| 27 | Remove English "Unified Intake" from product-only sidebar | **P2** | 中文-first office |
| 28 | Load chen_kui ui_copy.json into UI | **P2** | Client pack exists unused |
| 29 | Mobile-friendly paste area | **P3** | Many brokers on phone |
| 30 | Collapse engineer sections behind "高级" on case detail | **P3** | Power users only |

---

## Recommended Week 1 sprint order

1. **Trust pass:** Hide API URL, PG tags, debug tags (#2–4)  
2. **Front door:** Broker tab default + wayfinding banner (#1, #5)  
3. **First value:** Auto-open cancellation + loading states (#6, #10, #11)  
4. **Playbook parity:** Inline practice + doc label sync (#7, #24)  

---

*End of workbench improvements*
