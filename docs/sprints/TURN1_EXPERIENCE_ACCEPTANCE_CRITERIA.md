# Turn 1 Experience — Acceptance / SLA Criteria

**Sprint:** Controlled Multi-Agent Iteration Sprint

---

## 1. Must Pass

| Criterion | Check | Fail if |
|-----------|-------|---------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | Exit non-zero |
| Build | `cd ui && npm run build` | Build fails |
| Customer Entry inline loading | Manual: paste message, submit | No inline "正在整理" or equivalent visible in conversation during wait |
| Broker Workbench loading | Manual: paste, Triage | Loading card not visible or unclear |

---

## 2. Improvement Required

- **Customer Entry:** User must see inline feedback in the conversation area within ~100 ms of submitting. No blank gap.
- **Broker Workbench:** Loading text must be broker-friendly and consistent (e.g. "正在整理 case..." or "正在分析消息...").

---

## 3. Acceptable Friction

- Turn 1 latency (1.5–5+ s) unchanged; we are not optimizing backend.
- Loading text in Chinese or mixed Chinese/English; broker audience is Chinese-speaking.
- No skeleton UI; simple text + spinner is sufficient.

---

## 4. Not Acceptable

- Regression: scenario pack fails, guardrail fails.
- Loading state disappears or is hidden.
- Over-promising ("Almost done!" when we don't know).
- Breaking existing Copy draft, case card, or queue behavior.

---

## 5. Success Definition

Sprint succeeds if:
1. Customer Entry shows inline loading feedback during Turn 1.
2. Broker Workbench loading remains clear and consistent.
3. All automated checks pass.
4. Product critic agrees first-impression feel is improved.
