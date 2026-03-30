# ROLE D — Branch-driven variation + live API + deploy (Final report)

## Implemented

- **`ui/src/components/simulation/roleDReplay.ts`**
  - `detectRoleDBranchFamilies(note)` — keyword → branch families.
  - `applyLaterTurnBranches` — up to 4 families, unique later slots, hashed suffix choice from fixed pools.
  - Subtitle shows **自述分支** when any family fires.
- **`ui/src/components/simulation/ScenarioReplayTab.tsx`**
  - Copy updates: note drives **首轮 + 关键词驱动后续轮次**; helper text lists keyword examples.
- **`ui/package.json`** — `engines.node` set to **`20.x`** for predictable Vercel Node.
- **`ui/vercel.json`** — build command prefixes **`NODE_OPTIONS=--max-old-space-size=6144`** to reduce OOM risk on large bundles.

## Partial / limitations

- Branching is **suffix overlay**, not full alternate scripts per family (strong but bounded v1).
- Keyword detection is **regex**, not semantic; false positives/negatives possible.
- **Vercel dashboard** env: if `VITE_API_BASE_URL` is localhost, builds fail until fixed; this session used **CLI `-b VITE_API_BASE_URL=…`** for successful prod deploy.

## Live API

- **Already wired before this sprint:** replay uses `triageMessage` → `POST /api/inbox/triage` with `add_car` soft route. No change required for “real path” beyond confirmation.

## Deploy result

- **Backend:** No code changes; **no** new Cloud Run revision from this sprint.
- **Frontend:** **Production** deploy succeeded with explicit build env:
  - Command: `cd ui && vercel deploy --prod --yes -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`
  - Alias: **`https://ui-smoky-beta.vercel.app`**
  - Preview (same session, earlier attempt): `https://ui-rgkrxxjug-andys-projects-1f411b73.vercel.app` (preview URL rotates per deploy).

## Smoke result

- **Direct:** `GET https://ui-smoky-beta.vercel.app` → 200; `GET https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz` → 200; sample `POST /api/inbox/triage` (add_car) → JSON.
- **Not run in this session:** full browser click-through of Simulation tab + Role D on production (inferred from code path + API smoke).

## Validation

- `bash scripts/guardrail_inbox_triage.sh` → **PASS** (backend regression).

## Recommended next sprint

1. **Vercel env hardening:** set Production + Preview `VITE_API_BASE_URL` to Cloud Run **https** in dashboard so CLI `-b` is not required.
2. **Deeper branch v2:** optional **full-line variants** for 1–2 mid-turn indices per (template × family) without increasing turn count—still no LLM.
3. **Production E2E:** scripted Playwright or manual checklist for Simulation tab + Role D on `ui-smoky-beta.vercel.app`.
