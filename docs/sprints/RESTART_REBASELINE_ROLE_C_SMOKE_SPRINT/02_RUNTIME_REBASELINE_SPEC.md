# Runtime re-baseline spec

## Hypothesis

The process bound to **8001** was **stale** (started before `add_car_turn_intent` was wired into the triage JSON response, or before the latest `triage.py` / `add_car_intent.py` changes). Python does not hot-reload those modules without restart.

## Chosen path

**Local restart only:** stop listener on **8001**, start:

`PYTHONPATH=<repo> TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 127.0.0.1 --port 8001`

with `.env` / `.env.cloudrun` sourced when present (matches `scripts/run_demo_local.sh` / prior operator habit).

**Not executed in this sprint:** Cloud Run or Docker 8000 redeploy — treat as **separate** proof if production URL must match repo.

## Proof expectations (HTTP)

1. **Intent visibility:** `POST /api/inbox/triage` with `soft_route: "add_car"` returns `add_car_turn_intent` as an **object** with at least `intent_family`, `handoff_base_key`, and (when present) `phrase_storage_key` / `truth_notes`.
2. **Reply-head differentiation:** A **late-turn** message (e.g. timeline question) resolves to an intent such as `timeline_question` and the draft acknowledges that job (not only generic collection).
3. **Identity/lifecycle:** Spot-check `still_needed_fields` and lifecycle fields for coherence with current truth rules (full regression is out of scope).

## Smoke expectations

Run **three** bounded variants against **8001**:

- `price_sensitive` / `tough` / **4** turns  
- `family_vehicle` / `realistic` / **4** turns  
- `materials_first` / `realistic` / **4** turns  

Optional: `--jsonl` sample to confirm trace rows carry `add_car_turn_intent` sub-objects.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| Fresh 8001 process from repo | Yes |
| `add_car_turn_intent` non-null on Add-Car triage | Yes |
| Short Role C smoke completes (no 4xx/5xx) | Yes |
| Trace / JSONL shows intent payloads | Yes (sampled) |
| Remote production aligned | **Not verified** this sprint |
