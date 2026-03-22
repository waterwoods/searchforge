# Founder Verification Spec

**Sprint:** Workbench Demo UX + Visual Bug Fix Sprint

---

## 1. Exactly What the Founder Should Click

1. Open http://localhost:5173/workbench/unified-intake
2. Switch to **办公室工作台** tab (if not default)
3. Click **加载演示队列**
4. Observe: button loading → outcome → Tag count → 最近 case section
5. Scroll to **最近 case**; click a case card
6. Verify: cards readable; tags readable; no need to highlight text

---

## 2. What Should Happen

| Step | Expected |
|------|----------|
| Click 加载演示队列 | Button shows loading spinner |
| During load (~15–30 s) | Spinner visible; no other action needed |
| On success (new cases) | Toast: "已加载 X 个 case" or similar; Tag → green 13/13 |
| On success (already ready) | Toast: "演示队列已就绪" |
| On failure | Red Alert; toast error; button re-enabled |
| Scroll to 最近 case | Cards visible; cancellation-risk first; readable |
| Click case card | Case opens; content readable |

---

## 3. What "Fixed" Looks Like

- **Queue:** Founder knows load succeeded or failed; no guessing
- **Cards:** Readable without highlighting; tags and text clear
- **Trust:** Workbench feels stable; not broken-MVP

---

## 4. Screenshots / States to Verify

- [ ] Button loading state
- [ ] Success toast (Chinese)
- [ ] Tag "13/13 个 case 已就绪" (green)
- [ ] 最近 case cards readable
- [ ] Error state (if backend down): Alert + toast
