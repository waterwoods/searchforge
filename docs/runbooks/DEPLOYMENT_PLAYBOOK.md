# Deployment Playbook — Chen Kui Insurance Unified Entry

**Purpose:** Repeatable release operations for backend (Cloud Run) and frontend (Vercel).  
**Use:** Reference doc. Use `RELEASE_CHECKLIST.md` every release.

---

## 1. Scope of a Release

| Component | Host | Deploy Command |
|-----------|------|----------------|
| Backend | GCP Cloud Run | `bash scripts/deploy_rag_demo.sh` |
| Frontend | Vercel | `cd ui && vercel --prod` |
| Config | Baked into backend image | `configs/` copied in Dockerfile |

**Release = backend + frontend + env alignment.** Both must be live and aligned.

---

## 2. Pre-Deploy Checks

| Check | How |
|-------|-----|
| **Latest changed files** | `git status`, `git diff --stat` |
| **Local build** | `cd ui && npm run build` |
| **Local tests** | `bash scripts/guardrail_inbox_triage.sh`, `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001` |
| **Which side changed** | Backend only / frontend only / both |
| **Env assumptions** | `.env.cloudrun` has QDRANT_*, OPENAI_API_KEY, ALLOWED_ORIGINS |
| **Vercel target** | Production alias (e.g. `ui-smoky-beta.vercel.app`) |
| **Cloud Run target** | `fiqa-api` in `us-west1` |

---

## 3. Backend Deploy Procedure

### Standard path

```bash
# 1. Load env
cp configs/demo.env.example .env.cloudrun   # if first time
# Edit .env.cloudrun: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS

# 2. Deploy
bash scripts/deploy_rag_demo.sh
```

### What success looks like

- Script exits 0
- Output shows Service URL
- `curl <URL>/healthz` → 200
- `curl <URL>/readyz` → JSON with `ok` field

### What `/readyz` means

| `ok` | Meaning |
|------|---------|
| `true` | Qdrant + embedding ready (full RAG path) |
| `false` | Qdrant or embedding not ready |

### What `/readyz` does NOT mean

- **In DEMO_MODE:** Qdrant and embedding are optional. Inbox triage (rule/LLM path) works even when `/readyz` is `not_ready`.
- **Triage path:** `POST /api/inbox/triage` does not require Qdrant. If `/readyz` fails but `/healthz` passes, triage may still work.
- **Do not trust `/readyz` alone** to decide if the intake path is usable. Run one triage API check.

### When triage path works

- `/healthz` returns 200
- `OPENAI_API_KEY` set (for LLM triage) or rule-only fallback
- `configs/` present in image (Dockerfile copies `configs/`)

### When not to trust it

- `/healthz` fails → service not running
- CORS errors in browser → `ALLOWED_ORIGINS` mismatch
- Triage returns 500 → check logs, configs, OpenAI key

---

## 4. Frontend Deploy Procedure

### Standard path

```bash
cd ui
vercel --prod
```

### Verify production alias

- Vercel prints deployment URL (e.g. `https://ui-xxx.vercel.app`)
- **Production alias** (e.g. `ui-smoky-beta.vercel.app`) must point to this deploy
- In Vercel dashboard: Project → Settings → Domains — confirm production domain

### Confirm latest code is live

- Open production URL in browser
- Check for visible UI changes (e.g. new button, text)
- Hard refresh (Ctrl+Shift+R) to avoid cache
- If unsure: add a temporary visible marker, deploy, verify, remove

### Frontend env

| Variable | Required | Notes |
|----------|----------|-------|
| `VITE_API_BASE_URL` | Yes | Cloud Run URL (no trailing slash). Set in Vercel Project Settings → Environment Variables → Production |

---

## 5. Post-Deploy Verification

| Check | Command / Action |
|-------|------------------|
| Backend health | `curl <Cloud Run URL>/healthz` |
| Backend ready | `curl <Cloud Run URL>/readyz` |
| Triage API | `python3 scripts/test_inbox_triage_api.py --url <Cloud Run URL>` |
| Frontend loads | Open `https://<Vercel URL>/workbench/unified-intake` |
| CORS | No CORS errors in browser console when UI calls API |
| Visible UI | Confirm expected UI changes |
| Top trial flow | Paste "Notice: Policy will be cancelled in 7 days" → Start case → verify triage |

---

## 6. Production Truth Checks

| Concept | Meaning |
|---------|---------|
| **Deployed** | Build succeeded, service/revision created |
| **Live** | Service responds, correct revision serving traffic |
| **Frontend live** | Production alias serves latest deploy; UI loads |
| **Backend live** | Cloud Run revision is active; API responds |
| **Aligned** | Frontend `VITE_API_BASE_URL` = backend URL; backend `ALLOWED_ORIGINS` includes frontend URL |

**"Build passed" ≠ "production truly live"** — always verify in browser and with one API call.

---

## 7. Known Deployment Gotchas

See [KNOWN_DEPLOYMENT_GOTCHAS.md](./KNOWN_DEPLOYMENT_GOTCHAS.md) for full list. Summary:

- `/readyz` false-negative for intake path (DEMO_MODE)
- `configs/` must be in Docker image (verify Dockerfile)
- Vercel production alias may be stale
- ALLOWED_ORIGINS must match real Vercel URL
- Local success ≠ production success
- Browser/manual verification required for user-visible changes

---

## 8. Manual Smoke Checks

Before claiming success:

1. Open production frontend URL
2. Customer Entry: paste cancellation notice → verify triage
3. Broker Workbench: load case → verify status/notes
4. Simulation Assistant: run one scenario
5. No CORS errors in console

---

## 9. Roll-Forward / Retry Guidance

| Situation | Action |
|-----------|--------|
| Backend deploy failed | Check gcloud auth, project, logs; fix `.env.cloudrun`; retry |
| Frontend build failed | Fix build errors; `vercel --prod` again |
| CORS errors | Add/update `ALLOWED_ORIGINS` in `.env.cloudrun`; redeploy backend |
| `/readyz` not ready, triage needed | If `/healthz` OK, run triage API test; triage may work |
| Production alias wrong | Vercel dashboard → Domains → assign production |

---

## 10. When to Stop and Not Claim Success

- Do **not** claim success if:
  - CORS errors in browser
  - Triage API returns 500
  - Frontend shows old UI (alias not updated)
  - `ALLOWED_ORIGINS` does not include frontend URL
  - No manual browser verification for user-visible changes

---

## Quick Reference

| Task | Command |
|------|---------|
| Backend deploy | `bash scripts/deploy_rag_demo.sh` |
| Frontend deploy | `cd ui && vercel --prod` |
| Triage API test | `python3 scripts/test_inbox_triage_api.py --url <URL>` |
| Local guardrail | `bash scripts/guardrail_inbox_triage.sh` |

---

## How to Use This System

| Artifact | When to use |
|----------|-------------|
| **Playbook** | Reference when unsure; first-time deploy; troubleshooting |
| **Checklist** | **Every release** — must-check before saying success |
| **Cursor prompt template** | Every meaningful deploy; paste into Cursor for standardized release flow |
| **Human browser verification** | Every user-visible change; every trust-related change |

**Fastest release rhythm (small team):** Checklist every release; playbook as reference; Cursor template when using Cursor for deploy; always do manual browser check for UI/trust changes.
