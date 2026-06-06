# P16-O Phase 2 — Empty State Redesign

**Date:** 2026-06-01  
**Component:** `CustomerEntryTab.tsx` (turns.length === 0)

---

## Before

Customer saw:

- Hero H2 + long portalServiceTagline paragraph
- 3-step flow track
- ①②③ numbered instructions
- 办理类型 label
- Three equal buttons (加车 / 联系人工 / 其他事项)
- Structured form collapse header visible
- De-emphasized textarea below fold
- 场景仿真 link

**~16–18 visible objects**

---

## After (Typeform-style)

Customer sees:

```
请把您的需求发给我们
取消通知、加车、补材料都可以

[ ─────────────────────────────── ]
[  例如：刚买了 Tesla Model Y…      ]
[ ─────────────────────────────── ]

[        发送给办公室        ]

我们不会自动回复；办公室确认后再联系您

逐项填写加车信息 · 更多类型 · 需要人工？
```

**~8 visible objects** (−44%)

---

## Implementation

| Element | Treatment |
|---------|-----------|
| Headline | `portal_message_first_headline` |
| Subline | `portal_message_first_subline` |
| Textarea | Hero position, autofocus, inline examples in placeholder |
| Primary CTA | `portal_send_cta` — single block button |
| Trust line | `portal_trust_line` — one sentence centered |
| Structured add-car | Footer link → expands fields inline |
| 联系人工 | Footer link only |
| 更多类型 | Dropdown footer link |
| Flow track | Hidden until turns.length > 0 |
| Resume hints | Kept when single/multi in-progress case |

---

## Copy Source

`configs/clients/chen_kui/ui_copy.json` — keys `portal_message_first_*`, `portal_trust_line`, `portal_send_cta`

---

*End of P16-O Phase 2 — Empty State Implementation*
