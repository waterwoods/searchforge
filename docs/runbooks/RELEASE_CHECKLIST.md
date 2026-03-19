# Release Checklist — Chen Kui Insurance Unified Entry

**Use every release.** Must-check before saying success.

---

## Pre-Deploy

- [ ] `git status` — know what changed
- [ ] Which side changed? (backend only / frontend only / both) — determines deploy path
- [ ] `cd ui && npm run build` — frontend builds
- [ ] `bash scripts/guardrail_inbox_triage.sh` — local triage guardrail passes
- [ ] `.env.cloudrun` has QDRANT_*, OPENAI_API_KEY, ALLOWED_ORIGINS (if frontend on Vercel)

---

## Backend Deploy

- [ ] `bash scripts/deploy_rag_demo.sh` — exits 0
- [ ] `curl <Cloud Run URL>/healthz` — 200
- [ ] `curl <Cloud Run URL>/readyz` — inspect (ok:false OK if triage-only; see gotchas)
- [ ] `python3 scripts/test_inbox_triage_api.py --url <Cloud Run URL>` — PASS (one real triage check)

---

## Frontend Deploy

- [ ] `cd ui && vercel --prod` — succeeds
- [ ] Vercel production alias confirmed (dashboard or printed URL)
- [ ] `VITE_API_BASE_URL` in Vercel = Cloud Run URL (production env)

---

## Post-Deploy

- [ ] Open `https://<Vercel URL>/workbench/unified-intake` — loads
- [ ] No CORS errors in browser console
- [ ] Paste "Notice: Policy will be cancelled in 7 days" → Start case → triage works
- [ ] Visible UI change confirmed (if UI changed)
- [ ] Trust/state badge correct (if relevant)
- [ ] Simulation Assistant: run SIM3 or SIM15; verify replay shows Collected/Still needed when present

---

## Final Truth

- [ ] **Backend live:** API responds; triage test passed
- [ ] **Frontend live:** Production alias serves latest; no CORS
- [ ] **Aligned:** ALLOWED_ORIGINS includes frontend URL; VITE_API_BASE_URL = backend

---

**Do not claim success until all checked.**
