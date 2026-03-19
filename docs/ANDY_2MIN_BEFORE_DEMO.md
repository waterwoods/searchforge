# 2-Minute Before Demo Checklist

Run this right before the broker meeting.

**Default prep (one command):** `bash scripts/demo_pre_checklist.sh` — runs guardrail + validation (if backend up) + writes checklist. Use `--strict` to fail on drift.

**Demo path:** `bash scripts/run_demo_local.sh` → backend **8001**, UI 5173. Vite proxy targets 8001. (Docker uses 8000; validation scripts accept `--port 8000`.) **Recovery:** If 8001 returns 503 embedding_warming → `bash scripts/restore_8001_readiness.sh`

## ☐ 1. Run prep

```bash
bash scripts/demo_pre_checklist.sh
```

*(Quick path when backend already up: `bash scripts/demo_prep_one_command.sh` — 30 sec, no checklist file.)*

## ☐ 2. Demo ready?

- **"Use Live path"** (checklist) or **"Ready for Live Demo"** (quick) → Open http://localhost:5173/demo. You're good.
- **"Use Offline path"** → Open http://localhost:5173/demo. Click the 5 recommended questions. Demo works.

## ☐ 3. Browser tab open

- URL: http://localhost:5173/demo
- Status bar shows **Live** (green) or **Offline** (orange)

## ☐ 4. Optional: warm backend before demo

If backend was idle, warm it 2–3 min before demo to avoid cold start:

```bash
bash scripts/warmup_for_demo.sh
```

(For Cloud Run: `bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app`)

## ☐ 5. If backend not running

```bash
bash scripts/run_demo_local.sh
```

Wait for "Demo ready", then open the URL.

## ☐ 6. Optional: local Qdrant mode

If Cloud is down and you want live retrieval:

```bash
docker compose up -d qdrant
bash scripts/seed_local_qdrant.sh
USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh
```

---

**That's it.** Open `docs/runbooks/BROKER_VALUE_VALIDATION_MEETING_PACK.md` and go.

**Unified Intake / Chen Kui trial:** Use `docs/FOUNDER_DEMO_SOP.md` — URL: http://localhost:5173/workbench/unified-intake
