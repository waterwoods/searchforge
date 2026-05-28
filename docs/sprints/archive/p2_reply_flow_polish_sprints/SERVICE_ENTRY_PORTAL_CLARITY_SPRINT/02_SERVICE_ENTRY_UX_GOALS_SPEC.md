# Service-entry UX goals (plain language)

## 1. Identity clarity

- **Top chrome**: Broker brand (金盾保险 · 陈魁团队) + **configurable** tagline (`portal_brand_tagline`) so the visitor knows *which office* and *which lane* (车险受理入口).
- **Customer tab hero**: Title is **受理/报送** framed, not “助手” or generic “服务”.

## 2. Service purpose clarity

- One **primary paragraph** explains: you are **submitting** information; the system **structures** it into a **business record**; the **office** verifies, acts, and follows up—**no auto-send to carriers/clients** without office confirmation (aligned with pilot intro).

## 3. Transaction clarity

- **Add-car flow**: Blue ribbon keeps **当前办理：加车报价** + subtitle (from existing `ui_copy`).
- **In-form**: Tags show **当前办理** / **当前主题** with closable intent chip.
- **Non–add-car**: Progress card title uses **当前受理进度** instead of vague “整理中”.

## 4. State clarity

- Progress card: **主题 / 报价状态 / 已收集 / 还需 / 下一步建议 / lifecycle** — unchanged logically; annotation text shifted from “实时更新” to **状态随报送更新** (feeds recorded, not “chat streaming”).

## 5. Result clarity

- Post-handoff: **closure headline**, **办公室办理摘要** (was “回复摘要”), **系统记录到的要点**, **办公室后续可能还需**, timing alert, **服务记录** lines — reads as **case outcome**, not a single chat reply.

## 6. Reduced chat feel

- Thread labels: **您的报送** / **办公室整理回复** (not “您” vs office name only).
- Primary CTA after first turn: **提交补充** (not “发送”).
- Loading: **办公室正在整理您的报送** (not “马上就好”).
- Session restore toast: **已恢复未完成的报送** (not “已恢复对话”).

## 7. Increased business-entry feel

- Empty state headline: **请先选择办理类型，或直接填写下方报送内容** (not “今天有什么可以帮您？”).
- First-submit button when not add-car: **提交报送**.
- Tab label: **客户报送 — 受理入口** (config-driven).
