# Turn 1 Speed Mitigation — Acceptance / SLA Criteria

---

## What counts as useful improvement

- Cold start avoided (warmup or min_instances)
- Turn 1 perceived latency reduced (better feedback or faster path)
- First-impression risk materially lowered

## What counts as acceptable speed

- **Warm path:** 2–4 s for Turn 1 (LLM-dominated) — acceptable
- **Cold path:** No 5–15 s surprise; warmup or min_instances
- **Perceived:** "正在整理 case..." reduces dead-wait; acceptable

## What counts as acceptable cost

- Pre-demo warmup: ~1 h engineering, $0 operational
- min_instances=1: ~$35–70/mo (approximate; depends on region, CPU)
- Lighter Turn 1 path: 4–8 h engineering, quality risk

## What is too expensive or complex now

- Streaming replies
- Full architecture redesign
- Lighter first-pass model (quality risk)
- Broad retrieval gating (quality risk for pilot)

---

*See: `docs/sprints/TURN1_SPEED_MITIGATION_BLUEPRINT.md`*
