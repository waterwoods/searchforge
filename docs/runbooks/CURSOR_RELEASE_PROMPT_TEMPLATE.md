# Cursor Release Prompt Template

**Use for future redeploys and online verification.** Copy, fill placeholders, paste into Cursor.

---

## Template

```
You are running a release for SearchForge → Chen Kui Insurance Unified Entry.

**Mission:** Deploy backend and/or frontend, verify online truth, and report.

**Context:**
- Backend: GCP Cloud Run (fiqa-api, us-west1)
- Frontend: Vercel (production alias: ui-smoky-beta.vercel.app — update if different)
- Playbook: docs/runbooks/DEPLOYMENT_PLAYBOOK.md
- Checklist: docs/runbooks/RELEASE_CHECKLIST.md
- Gotchas: docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md

**Tasks:**
1. Inspect latest changes: `git status`, `git diff --stat` — what changed (backend/frontend/both)?
2. Run local checks: `cd ui && npm run build`; `bash scripts/guardrail_inbox_triage.sh` (if server up: `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001`)
3. Deploy backend if backend changed: `bash scripts/deploy_rag_demo.sh` (requires .env.cloudrun)
4. Deploy frontend if frontend changed: `cd ui && vercel --prod`
5. Verify online truth:
   - curl <Cloud Run URL>/healthz
   - curl <Cloud Run URL>/readyz (note: ok:false may be OK for triage-only; see gotchas)
   - python3 scripts/test_inbox_triage_api.py --url <Cloud Run URL>
   - Confirm Vercel production alias and ALLOWED_ORIGINS alignment
6. Distinguish: directly observed (curl, script output) vs inferred
7. Print a concise release report:
   - What was deployed
   - Health/readyz/triage results
   - Frontend URL and alias status
   - Any blockers or manual steps (e.g. browser verification)
   - Final: ready for trial / blocked / needs human check
```

---

## Usage Notes

- Replace `<FILL: ...>` with actual production alias
- If only backend changed, skip frontend deploy
- If only frontend changed, skip backend deploy
- Always run triage API test against production URL
- Do not assume success from script exit alone; report observed results
