# ADD-CAR Pilot Verification + Handoff Credibility — Final report

## What was verified

- **Master alignment**: Stage 1 intake + structuring; Add-Car flagship; value = office-ready record + clear next step + handoff (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`, `PROJECT_TRUTH_SWITCH.md`).
- **Prior scorecard**: PAGE ~4/5, FLOW/STATE/HANDOFF ~3/5; gaps = chat-centric UX, engine tone on edges, workbench parity, ops truth (`ADD_CAR_INDUSTRIAL_SCORECARD_V1`).
- **Copy & UI wiring**: `clientConfig.ts` defaults + `configs/clients/chen_kui/ui_copy.json` — strong closure, post-handoff thread deemphasis, workbench subtitle/id hint, broker-next preview labels.
- **Engine (rule path)**:
  - `triage_conversation` spot checks: full Add-Car single turn → `handoff_ready`, standard add-car handoff draft; Add-Car + WeChat/materials sent → `follow_up_type: already_sent`, stitched **add_car_materials_sent** draft, concrete `broker_next_step`.
  - Multi-turn incomplete + “还缺什么材料？” → remains collecting, asks for ZIP (appropriate; does not fake handoff).
  - Isolated “行驶证我微信发过了” with **no** vehicle context → `handoff_ready: false`, generic clarification (expected gap for stray messages).
- **Regression**: `LLM_GENERATION_ENABLED=0 bash scripts/guardrail_inbox_triage.sh` — **PASS** (64/64 scenario pack, 69 multi-turn sims, broker stress incl. BS11 Add-car materials sent, HT13, case boundary, cross-client A/B, etc.).
- **Add-Car realistic battery**: `scripts/run_add_car_realistic_intake_scenarios.py` — completed successfully (JSON summary).

## What felt credible

- **Commercial narrative**: Portal hero, transaction ribbon, result card, service record id, and closure blocks match “报送 → 办公室接手” positioning.
- **Handoff copy depth**: “无需再重复一遍,” append-vs-new-issue hints, timing copy, and post-handoff section labels reduce “black hole” anxiety.
- **Already-sent (in full Add-Car context)**: Engine + `handoff_phrases.json` stitched `add_car_materials_sent` reads as desk-verification, not argument.
- **Office side (code review)**: Workbench detail shows copyable case id, `AddCarCaseStatusStrip`, broker next preview, collection/handoff tags — credible continuation of the same record model.

## What felt weak

- **FLOW still chat-primary**: Scorecard point holds—the user still orients by thread bubbles despite cards/tracks.
- **Stray already-sent**: Single-line “发过了” without case context stays in clarification limbo—reasonable technically, weaker for customer reassurance if that’s their first message.
- **Not live-checked**: No browser run on 8001 in this session (guardrail skipped API test); visual/timing trust not empirically re-verified here.
- **Commercial ceiling**: JSON persistence, auth/PII, LLM path ≠ guardrail path remain real pilot conversation topics.

## What changed

- **No product code or config changes** in this sprint—diagnosis only; guardrail already green.

## Recommended next sprint

1. **Highest leverage (commercial)**: 1–2 **real broker dry-runs** (same script + observation checklist as trial docs)—validate trust in the room, not only in sims.
2. **Product runner-up**: Live **8001 smoke + UI walkthrough** frozen checklist (happy path + materials sent + append) to close the “not visually verified” gap.
3. **Engine runner-up** (only if broker feedback demands): Narrow triage tweak for **orphan already-sent** messages (high-risk file—scope tightly).

## Sprint timing

- **Start**: 2026-03-28 (session)
- **End**: 2026-03-28 (session)
- **Elapsed**: ~35–45 minutes (reads, code review, offline triage, full guardrail, doc authoring)
