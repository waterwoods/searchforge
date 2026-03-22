# Demo Queue Interaction Spec

**Sprint:** Workbench Demo UX + Visual Bug Fix Sprint

---

## 1. What "加载演示队列" Is Supposed to Do

- Load 13 preset demo cases into the workbench via `triageMessage` API
- Skip cases already present (by source_text match)
- Open the cancellation-risk case first (or strongest existing if already loaded)
- Refresh the "最近 case" list
- Show clear feedback at each stage

---

## 2. UI Feedback During Click

| Stage | Expected behavior |
|-------|-------------------|
| **Loading started** | Button shows loading spinner; disabled |
| **Loading in progress** | Inline or toast: "正在加载演示队列…" (optional, button state is primary) |
| **Loading succeeded (new cases)** | Toast + inline: "已加载 X 个 case，见下方「最近 case」" |
| **Loading succeeded (already ready)** | Toast: "演示队列已就绪" |
| **Loading failed** | Error Alert visible; message.error toast; button re-enabled |

---

## 3. Success / Failure / Empty-State Appearance

| State | Visual |
|-------|--------|
| **Success (new)** | message.success; Tag updates to green "13/13 个 case 已就绪"; optional scroll hint |
| **Success (already ready)** | message.info; Tag stays green |
| **Failure** | Alert type="error" above content; message.error; setError(msg) |
| **Empty queue (before load)** | Tag blue "0/13 个 case 已就绪"; empty state in 最近 case |

---

## 4. How Founder Should Understand the Result

- **Button loading** → Action in progress
- **Toast message** → Outcome (success/fail/already ready)
- **Tag count** → How many of 13 are loaded
- **Scroll to 最近 case** → Cards visible; cancellation first
- **Error Alert** → If visible, load failed; check backend/network

---

## 5. Root-Cause Targets (Not Cosmetic)

- No click handler → Handler exists; verify wiring
- Failed fetch → Ensure error surfaces (Alert + toast)
- Stale state → loadRecent() after loop; verify
- Missing feedback → Add Chinese toasts; ensure visibility
- Data loads but hidden → 最近 case below fold; add scroll hint or inline summary
- Empty state mismatch → Already has empty copy
- Logic regression → Verify triageMessage, loadRecent, setCurrentCase
