# Workbench Audit — TOP 30 Improvements

**Method:** Review workbench UX from UnifiedIntakePage, BrokerWorkbenchTab, CUSTOMER_LANGUAGE_GUIDE, and broker trial docs (non-archived). Rank by ROI, difficulty, risk for a paying Chen Kui office.

**Scale:** ROI / Difficulty / Risk — each 1 (low) to 5 (high). **Priority score** = ROI × 2 − Difficulty − Risk (higher = do first).

---

## What broker sees first (today)

1. **陈魁团队 header** + Add-Car-first pilot intro alert (info-heavy)  
2. **Default tab: 客户报送** — customer-facing portal, not broker triage  
3. If they find **办公室工作台:** summary tiles (总数, 高风险) → 加载演示队列 → queue list with many tags  

## What feels valuable

- **下一步** preview on queue cards without opening case  
- **已收集 / 还缺** chips on case detail  
- **当日处理 / 需核实收到** queue readiness labels  
- Editable draft + copy to WeChat workflow  
- **加载演示队列** for safe learning  
- Cancellation case urgency obvious when demo queue loaded  

## What feels confusing

- Four tabs; trial docs assume one  
- Add-Car-first messaging vs cancellation-first demo  
- Mixed 中文 + English ("case", "Unified Intake" in nav)  
- Too many queue tags on one card  
- 演示队列 vs real paste workflow unclear  

## What feels like engineer artifact

- `PG 已镜像` / `PG 缺失` / `镜像不一致` tags  
- `路由/指标` debug tag  
- `数据接口` + localhost/API URL in queue header  
- Segmented filters: 镜像异常, 旧识别, 测试, 正式  
- Monospace 服务记录编号 everywhere  
- `13/13 个 case 已就绪` (English "case")  
- workbench_lane_kind, quote_ready_status internal labels leaking  

---

| # | Improvement | ROI | Diff | Risk | Pri | Notes |
|---|-------------|-----|------|------|-----|-------|
| 1 | Default broker trial URL to `?tab=broker` or remember last tab | 5 | 2 | 1 | 7 | Fixes #1 confusion instantly |
| 2 | Hide PG mirror tags + trust line in product-only UI | 5 | 2 | 1 | 7 | Pure broker trust |
| 3 | Hide API endpoint label in product-only UI | 5 | 1 | 1 | 8 | **Do first** |
| 4 | Hide 路由/指标 debug tag in product-only | 4 | 1 | 1 | 6 | |
| 5 | Replace "case" with 服务记录 in all broker-visible strings | 4 | 2 | 1 | 5 | |
| 6 | Collapse pilot intro alert by default for production | 4 | 1 | 2 | 5 | |
| 7 | Auto-open cancellation case after demo queue load | 5 | 2 | 2 | 6 | Matches demo script |
| 8 | Add 练习场景 inline panel (product-only) replacing hidden Simulation tab | 5 | 4 | 2 | 4 | Playbook dependency |
| 9 | One-line broker wayfinding: "经纪人：请用本页粘贴客户消息" on workbench | 5 | 1 | 1 | 8 | |
| 10 | Simplify queue filters to 全部 / 需今天处理 / 24小时内 | 4 | 2 | 2 | 4 | Remove mirror/legacy |
| 11 | Prominent **复制案例快照** for support | 4 | 2 | 1 | 5 | |
| 12 | Paste area default copy: "原样粘贴微信/通知文字，不用整理" | 4 | 1 | 1 | 6 | |
| 13 | First-request loading state: "首次分析约30秒" | 4 | 2 | 1 | 5 | |
| 14 | Align BROKER_ONE_PAGER labels with UI (加载演示队列) | 3 | 1 | 1 | 4 | Doc fix |
| 15 | Reduce queue card tag count (show max 3 + expand) | 4 | 3 | 2 | 3 | Scanability |
| 16 | Rename 高风险 → 需当天处理 | 3 | 1 | 1 | 4 | |
| 17 | Hide 管理 → 标为测试 from non-founder builds | 3 | 2 | 2 | 2 | |
| 18 | Short 服务记录编号 (last 6 chars) in list; full on detail | 3 | 2 | 1 | 3 | |
| 19 | Sticky **下一步** + draft on case detail scroll | 4 | 3 | 2 | 3 | |
| 20 | Highlight **更新客户新消息** when case selected | 4 | 2 | 1 | 5 | |
| 21 | Footer: 支持微信 XXX · 不自动发送 | 3 | 1 | 1 | 4 | |
| 22 | Reconcile Add-Car-first banner with cancellation demo (pick one lead) | 5 | 2 | 3 | 5 | Product decision |
| 23 | Hide 我的办理 tab in broker-only trial mode | 3 | 2 | 2 | 2 | |
| 24 | Load chen_kui ui_copy.json into UI (today hardcoded) | 3 | 3 | 2 | 1 | Client pack exists |
| 25 | Empty queue: video/GIF 3-step "paste → review → copy" | 4 | 3 | 1 | 4 | |
| 26 | Mobile-friendly paste (many brokers on phone) | 3 | 4 | 2 | 0 | |
| 27 | Draft copy button label: 复制到微信（请先修改） | 4 | 1 | 1 | 6 | |
| 28 | Remove English "Unified Intake" from product-only sidebar | 3 | 1 | 1 | 4 | |
| 29 | Demo queue progress bar (1/13…) during load | 3 | 2 | 1 | 3 | |
| 30 | Case detail: collapse engineer sections behind "高级" | 3 | 3 | 2 | 1 | |

---

## Recommended sprint order (Week 1 UI)

1. Hide API endpoint + PG tags + debug tags (product-only) — items 2–4, 9  
2. Broker tab default + auto-open cancellation — items 1, 7  
3. Copy/label pass — items 5, 12, 16, 27  
4. Playbook + inline practice — items 8, 14  

---

*End of workbench audit*
