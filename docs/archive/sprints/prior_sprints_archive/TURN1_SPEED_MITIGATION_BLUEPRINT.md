# Turn 1 Actual Speed Mitigation — Sprint Blueprint

**Sprint:** Turn 1 Actual Speed Mitigation Sprint  
**Date:** 2026-03-14  
**Mode:** Root-cause audit → option analysis → lightweight mitigation

---

## 1. Why Turn 1 matters

The first message sets the first impression. When Chen Kui (or any prospect) pastes a message and waits 5+ seconds with no clear feedback, they may think the system is slow or broken. Trust erodes before the first response appears.

## 2. Why it is still weak

- **Turn 1 always goes through LLM** — by design, for intent classification
- **Cold start** — Cloud Run `min-instances=0` → 5–15 s when idle
- **LLM latency** — 1.5–5 s typical
- **Retrieval** — +0.5–2 s when notice/document confusion
- **Net:** Warm path ~2–6 s; cold path 5–20+ s

## 3. What "good enough" means for demo/pilot

- **Warm path:** 2–4 s acceptable for LLM-first reply
- **Cold path:** Avoid 5–15 s surprise; pre-warm or min_instances
- **Perceived:** "正在整理 case..." already reduces dead-wait; no blank gap

## 4. Why this sprint matters commercially

First paid pilot within 2–3 weeks. Turn 1 latency is the strongest blocker to small-client confidence. Mitigations must be startup-grade: low cost, low complexity, measurable impact.

## 5. Out of scope

- Large infra migration
- Observability platform
- Full architecture rewrite
- Realism pack, CRM, auth
- Streaming replies (complex, small gain for demo)

---

*See: `docs/sprints/TURN1_SPEED_MITIGATION_EXECUTION_OUTLINE.md`, `docs/sprints/TURN1_SPEED_MITIGATION_ACCEPTANCE_CRITERIA.md`*

---

**Full report:** See `docs/sprints/TURN1_SPEED_MITIGATION_REPORT.md` (or run sprint report generation).
