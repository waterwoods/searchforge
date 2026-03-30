# REMOTE / DEMO ENV REBASELINE + PRECHECK — Blueprint

## Sprint goal

Re-baseline the **real demo-facing backend** (Cloud Run `fiqa-api`) so it runs the same Add-Car **Truth → Intent → Reply** stack as the current repo, then prove it on the **public HTTPS URL** with a short smoke—not localhost only.

## Why now

Local `8001` had already been re-baselined, but the **outward demo stack** (what Andy shows on Vercel) calls **Cloud Run**. A live probe before this sprint showed **`add_car_turn_intent: null`** on Add-Car triage while the repo serializes structured intent—classic **stale revision** risk. Without aligning production, Role C Plus and demos would be built on a false sense of “current.”

## Read-first docs (aligned)

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — service record, Add-Car wedge, state-driven flow.
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical path, health endpoints, Vercel + Cloud Run deploy truth.
3. `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` — Truth constrains Intent constrains Reply.

## Scope

**In scope:** Remote runtime alignment (deploy/restart), live proof on `https://fiqa-api-g7zatxrycq-uw.a.run.app`, short remote smoke, mapping to Vercel alias `https://ui-smoky-beta.vercel.app`, lightweight sprint docs.

**Out of scope:** Frontend Role C Plus implementation, large batteries, product redesign, unrelated features.

## Target outcome

- Cloud Run serves a **new revision** built from the current repo.
- `POST /api/inbox/triage` on Add-Car paths returns a **non-null `add_car_turn_intent`** object.
- At least one **post-submit late turn** shows **intent-aware reply head** (not only generic office block).
- `scripts/test_inbox_triage_api.py --url <Cloud Run>` passes against production.
