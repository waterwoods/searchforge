# Hybrid Unified Entry — Founder Demo / Inspection Notes

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. What the Founder Should Inspect After Deployment

| Area | Inspect |
|------|---------|
| **First screen** | Welcome message visible? 5 buttons visible? Free-text input below? |
| **Button behavior** | Click one → does it highlight? Click again → does it deselect? |
| **Free text** | Can you type without clicking any button? Does it work? |
| **Combined** | Click "获取报价" then type add-car message → does it flow naturally? |
| **Customer vs office** | Tab "客户入口" vs "Broker Workbench" — is the separation clear? |
| **Handoff** | After multi-turn, does "查看工作台" work? Does case appear in queue? |

---

## 2. Behaviors That Matter Most

| Behavior | Why |
|----------|-----|
| **Welcome feels friendly** | Sets tone; reduces bounce |
| **Buttons don't block** | User can always type; no lock-in |
| **Free text prominent** | Power users and edge cases |
| **Page feels like product** | Not lab; not intimidating |
| **Office tab secondary** | Customer entry is the front door |

---

## 3. Scenarios That Best Show the New Model

| Scenario | Steps | What to look for |
|----------|-------|------------------|
| **Button + matching text** | Click "获取报价" → type "我想加一台2021 Tesla Model Y" | Smooth flow; add-car triage |
| **Button + conflicting text** | Click "付款" → type "我想加一台新车" | (Loop 2) Reroute acknowledgment |
| **Free text only** | Type "刚出事故了" without button | Claim intake; no button needed |
| **Case creation** | Multi-turn to handoff → "查看工作台" | Case in queue; handoff message clear |
| **Office handoff** | Complete intake → switch to Broker tab | Case visible; broker can act |

---

## 4. Quick Checklist for Andy

- [ ] Open Customer Entry tab
- [ ] See "How can I help today?" (or 今天有什么可以帮您？)
- [ ] See 5 buttons: 获取报价, 保单变更, 报事故, 付款/账单, 上传材料/联系客服
- [ ] See free-text input below
- [ ] Click one button → it highlights
- [ ] Type a message → submit works
- [ ] Click "模拟演示" → Simulation Assistant opens
- [ ] Switch to Broker Workbench → office view
- [ ] Load founder demo queue → cases appear

---

## 5. What "Success" Looks Like

The page should feel:
- **Welcoming** — not cold or mechanical
- **Easy to start** — buttons help; free text always available
- **Not intimidating** — no long forms, no overload
- **Product-like** — polished SaaS intake, not lab tool

---

*See also: UX/Interaction Design Spec, Acceptance/SLA Criteria*
