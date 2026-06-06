# P16-N Phase 6 — Single-Task Flow (Paper Design)

**Date:** 2026-06-01  
**Constraint:** Design only — no code, no capability changes  
**Goal:** One task per screen; customer completes intake with almost no explanation

---

## Design Principles (from Stripe · Calendly · Typeform · Apple Setup)

1. **Message before category** — infer intent from natural language  
2. **One primary control per viewport** — everything else is link or next screen  
3. **Progress appears after commitment** — not before first keystroke  
4. **Success = stop** — explicit "you're done; we'll contact you"  
5. **Office complexity stays on office side** — customer never sees broker_next_step

---

## Ideal Flow — Add Car (Flagship Path)

### Step 1 — Customer Starts

**Screen:** Welcome  
**Task:** Understand what this is  

```
[Broker avatar] 陈魁团队 · 车险服务

请把您的需求发给我们
取消通知、加车、补材料都可以

[ ─────────────────────────────── ]
[  例如：刚买了 Tesla Model Y，想加进保单  ]
[ ─────────────────────────────── ]

[        发送给办公室        ]

我们不会自动回复；办公室确认后再联系您

小字：想逐项填写加车信息？点这里
```

**Removed from current:** flow track, 3 buttons, ①②③, category label, structured form visible

---

### Step 2 — Customer Provides Information

**Screen:** Conversation (one question at a time)  
**Task:** Answer the current question only  

```
加车报价 · 第 2 步，共 3 步
● ○ ○

办公室需要确认：

「请提供车辆年份和车型」

[ ─────────────────────────────── ]
[  2024 Tesla Model Y              ]
[ ─────────────────────────────── ]

[        发送        ]

展开 · 已记录的内容（2 项）
```

**Removed from current:** full record rail, bubble tags, transaction banner, thread default-open

**System behavior (unchanged capability):** Multi-turn triage continues; UI shows only `next_best_question` + compact collected summary collapse

---

### Step 3 — Customer Submits

**Screen:** Confirm handoff  
**Task:** One confirmation action  

```
资料已齐 ✅

请确认送交办公室处理

称呼：________    手机：________
（若已在上方对话提供，可留空）

[     确认提交，开始处理     ]

提交后办公室会核对并联系您报价
```

**Removed from current:** dual path (chat phone vs button), alert stack, identity strip, button subline essay

---

### Step 4 — Office Receives

**No customer screen** — broker workbench unchanged (out of P16-N scope)

Customer sees nothing during office processing except optional status in 我的办理

---

### Step 5 — Customer Sees Confirmation

**Screen:** Done  
**Task:** Know they're finished  

```
✅  已收到您的加车报价请求

办公室正在处理。您无需重复发送相同信息。
有进展时会联系您。

参考编号：AC-2024-xxx  [复制]

[ 查看办理进度 ]     [ 提交新问题 ]

有补充？ [ 追加到本条记录 ]  ← link, not panel
```

**Removed from current:** AddCarFlowExplanation, UTC footnote, structured snapshot default-open, broker_next_step, 查看工作台, boundary essay, duplicate alerts

---

## Ideal Flow — Non–Add-Car (Cancellation / Missing Doc / Remove Car)

Same Steps 1–5 with **no add-car-specific copy** until intent detected.

| Detected intent | Step 2 headline | Step 3 difference |
|-----------------|-----------------|-------------------|
| Cancellation / payment | 付款问题 · 第 1 步 | No structured fields; faster handoff |
| Missing document | 补材料 · 第 1 步 | Ask what's missing; note "可描述已发微信" |
| Remove car | 保单变更 · 第 1 步 | Ask which vehicle |
| Claim | 事故报险 · 第 1 步 | Safety-first copy |

**Key:** Customer never picks category — system detects from Step 1 message

---

## Ideal Flow — Status Check

**Screen:** My Requests (mostly keep current — already good)

```
我的办理

[ 加车 · Tesla Model Y        处理中 ]
[ 付款问题                    待补充 ]

─────────────────────────
加车 · Tesla Model Y

状态：办公室处理中
下一步：请等待联系

[ 去补充信息 ]  ← only if still_needed > 0
```

**Simplify:** Hide field chip dump; show one next sentence

---

## Screen Count Comparison

| Flow | Current screens (mental) | Ideal screens |
|------|-------------------------|---------------|
| Add-car empty → done | 1 overloaded + 3–5 dense | 5 focused |
| Remove car | Same overload as landing | 3–4 (shared Step 1) |
| Upload docs | Same + upload confusion | 3–4 |
| Status check | 2 (good) | 2 (lighter detail) |

---

## Navigation Model

```
Customer URL (/portal or ?tab=customer only)
  ├── 报送 (default) — Steps 1–5
  └── 我的办理 — Status only

No broker tab · No simulation · No tab suffixes
```

---

## What Stays in Capability (Hidden, Not Removed)

- Structured add-car fields → behind link in Step 1  
- AddCarRecordSummaryRail data → collapsed "已记录的内容"  
- Append-to-same-case → link on confirmation only  
- Case ID → small reference on confirmation  
- All triage / handoff / lifecycle logic — **unchanged**

---

## Success Metric

Cold customer completes add-car intake **without asking "which button?"** — measured by:

- Landing 5s score ≥ 75  
- Single primary on every screen  
- ≤ 8 visible objects on empty state

---

*End of P16-N Phase 6 — Single-Task Flow*
