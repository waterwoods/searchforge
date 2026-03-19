# If Something Goes Wrong — Broker Demo

Quick fixes for common issues.

## Backend not running

**Symptom:** Status bar shows "Disconnected", orange banner.

**Fix:**
```bash
bash scripts/run_demo_local.sh
```
Wait for "Demo ready", then refresh the page.

**Fallback:** Use Offline mode. Click the 5 recommended questions. Demo works.

---

## Qdrant Cloud 404 (live retrieval fails)

**Symptom:** demo_prep says "Use Offline Demo", or questions return "embedding_warming" / 404.

**Fix A — One-command recovery (backend already running on 8001):**
```bash
bash scripts/restore_8001_readiness.sh
```
Kills existing 8001, restarts with USE_LOCAL_QDRANT=1, waits for /ready. Requires local Qdrant + seeded collection.

**Fix B — Full demo with local Qdrant:**
```bash
# 1. Start Qdrant
docker compose up -d qdrant

# 2. Seed collection (once; ~1 min)
bash scripts/seed_local_qdrant.sh

# 3. Run demo with local Qdrant
USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh
```

Then open http://localhost:5173/demo. Live retrieval works.

**Fallback:** Use Offline mode. Click the 5 recommended questions.

---

## Blank screen / white screen

**Symptom:** Page loads but nothing shows.

**Fix:** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R). Check browser console for errors.

---

## Port already in use

**Symptom:** "Address already in use" when starting backend or UI.

**Fix:**
```bash
# Kill backend
pkill -f "uvicorn services.fiqa_api"

# Kill UI
pkill -f "vite.*5173"
```
Then wait 2 seconds and run `bash scripts/run_demo_local.sh` again.

---

## Demo prep says "Backend not running"

**Symptom:** demo_prep_one_command.sh exits with "Backend not running".

**Fix:** Start the demo first:
```bash
bash scripts/run_demo_local.sh
```
In another terminal, run `bash scripts/demo_prep_one_command.sh` again.

---

## Seed script fails (no passing.json)

**Symptom:** `seed_local_qdrant.sh` says "No passing.json found".

**Fix:** Discovery data is required. Ensure `results/auto_insurance_discovery/passing.json` or `results/auto_insurance_discovery/runs/*/passing.json` exists. If not, run discovery first (see `scripts/discover_auto_insurance_sources.py` or similar).

---

## Still stuck?

- **Offline mode always works.** Click the 5 recommended questions. No backend needed.
- See `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` for the fallback script.
