# REMOTE / DEMO ENV REBASELINE + PRECHECK — Final Report

## Environment re-baselined

- **Service:** Google Cloud Run `fiqa-api` (project `optimal-disk-472305-e2`, region `us-west1`).
- **Revision deployed (this sprint):** `fiqa-api-00047-b8x` (supersedes prior revision such as `00046-*` documented in earlier sprints).
- **Public URL:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

## What was proven (evidence)

1. **Before deploy:** `POST .../api/inbox/triage` with `soft_route: "add_car"` returned **`add_car_turn_intent": null`**.
2. **After deploy:** Same request returned a **non-null** object, e.g. `intent_family`, `handoff_base_key`, `phrase_storage_key` populated.
3. **`scripts/test_inbox_triage_api.py --url https://fiqa-api-g7zatxrycq-uw.a.run.app`:** **All tests passed** (including persist + append paths).
4. **Late-turn / post-submit:** Multi-turn flow: formal submit with non-empty customer line → follow-up “大概多久能出报价？” → **`add_car_turn_intent.intent_family`** reflected timeline-style classification; **`client_reply_draft`** opened with **关于时间安排与进度：** (intent-specific head, not only generic office closure).
5. **Vercel:** Fetched `https://ui-smoky-beta.vercel.app/assets/index-*.js`; bundle contains **`https://fiqa-api-g7zatxrycq-uw.a.run.app`**—aligned with rebaselined backend without a new UI deploy this session.

## Smoke run summary

| Check | Result |
|-------|--------|
| Remote API test script | PASS (full suite) |
| Add-Car intent visibility | PASS (post-deploy) |
| Multi-turn formal submit + timeline follow-up | PASS (intent + reply head observed) |

## What remains uncertain / watch items

- **Post-submit lifecycle label on some turns:** One probe showed `lifecycle_status: "handoff_pending"` on a post-submit follow-up while the case had `formal_submitted_at`; worth a future narrow truth/lifecycle audit—not blocking “intent visible + reply head” proof.
- **Cold start / min instances:** Cost-safe `min-instances: 0` means first request after idle can be slower; use `scripts/warmup_for_demo.sh` before live demos if needed.
- **Vercel dashboard env:** Bundle was verified by scrape; long-term, keep Production `VITE_API_BASE_URL` set in Vercel so CLI `-b` is not required.

## Recommendation: frontend Role C Plus

**Yes—consideration is now justified** for planning Role C Plus **on the condition** that UI work continues to target the **documented Cloud Run URL** and occasional **remote smoke** (this script + one Add-Car intent check) runs after backend deploys. This sprint removed the specific failure mode “production missing `add_car_turn_intent` while repo has it.”

## Code / repo files changed

**None** in application code for this sprint—operational deploy only plus these sprint markdown files under `docs/sprints/REMOTE_DEMO_ENV_REBASELINE_PRECHECK_SPRINT/`.
