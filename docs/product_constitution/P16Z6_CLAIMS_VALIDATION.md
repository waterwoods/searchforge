# P16-Z6 Phase 6 — Claims Battery Validation

**Date:** 2026-06-02  
**Method:** 10 multi-turn claims scenarios × 3–4 turns each; rules-based triage (production fallback)  
**Engine:** `triage_conversation` with accumulating `turns`

---

## Rubric (per turn, max 25)

- Turn 1: claim category/summary + broker_next_step depth  
- Turn 2+: message count in summary + prior keyword retention + broker step  

**Overall battery avg:** 16.4 / 25 per turn (pre-UI thread; engine-only)

---

## Scenario summary

| ID | Turns | Avg/25 | Case | Timeline | Memory | Next action |
|----|-------|--------|------|----------|--------|-------------|
| C1 | 4 | 12.8 | ⚠️ | ⚠️ | ⚠️ | ✅ T1 |
| C2 | 3 | 13.0 | ⚠️ | ⚠️ | ⚠️ correction | ✅ T1 |
| C9 | 3 | 15.7 | ✅ | ⚠️ | ✅ C9-T2 correction | ⚠️ |
| C3–C8 | 3 | 18.3 | ✅ | ⚠️ | ✅ EN keywords | ✅ |
| C10 | 3 | 13.0 | ⚠️ | ⚠️ | ⚠️ total-loss correction | ✅ T1 |

---

## TOP 10 claims failures

| # | Failure | Example |
|---|---------|---------|
| 1 | Prior turn facts weak in summary on Turn 3–4 | C1 progress anxiety — plate/photos not in headline |
| 2 | Correction turns drop FNOL context | C2 “不是全损”, C10 “不是全损” — partial prior prepend |
| 3 | `collected_fields` not accumulating plate/photos | C1-T2 plate in message, not always in collected |
| 4 | Mixed claim + payment pivot noise | C5 “不是payment” on claim thread |
| 5 | `broker_next_step` generic on late turns | C1-T4 urgency |
| 6 | Attachment / scan turn weak classification | C1-T3 supplemental letter |
| 7 | Injury + claim complexity | C8 adjuster script thin |
| 8 | Timeline UI not in engine run | Perceived loss until broker opens thread card |
| 9 | `waiting_on: carrier` never auto-set | Progress-check messages |
| 10 | Chinese keyword scoring blind spots | Battery regex under-credits valid summaries |

---

## TOP 10 claims successes

| # | Success | Example |
|---|---------|---------|
| 1 | Turn 1 FNOL routing strong | C1, C3–C8, C9 |
| 2 | Hit-and-run / uninsured templates exist | C1, C3, C6 |
| 3 | Policy # extraction on paste | C4 `8829101` |
| 4 | Multi-turn message count in summary | Most Turn 2+ |
| 5 | Prior turn prepend helps correction cases | C9 “不是事故” chain |
| 6 | Append API + `case_messages` persistence | Guardrail FA3 claim photos |
| 7 | EN claim threads score higher | C3–C8 @ 18.3 |
| 8 | `broker_next_step` actionable on Turn 1 | Evidence collection steps |
| 9 | Thread render (Z6 UI) fixes ~80% re-read pain | Design intent (P16-Z4) |
| 10 | No new FNOL engine required for pilot | Invest in memory not greenfield |

---

## Verdict

Claims **Turn 1 is pilot-ready**; **Turn 2+ memory** improves with Z6 thread + correction prepend but still needs claim-specific collected merge and plate/photo in summary — next sprint slice, not Z6 scope.
