# Release Checklist Dry Run + Process Acceptance Report

**Sprint:** Release Checklist Dry Run + Process Acceptance Sprint  
**Date:** 2025-03-12  
**Scope:** Validate release system usability; no product changes.

---

## 1. Initial audit of the release system

### What is already good

- **Checklist length:** ~15 checkboxes, ~50 lines — short enough to use every release.
- **Playbook structure:** Clear sections (scope, pre-deploy, backend, frontend, post-deploy, gotchas, roll-forward). Good reference.
- **Gotchas doc:** 9 concrete pitfalls with symptom → cause → fix → avoid. Very useful.
- **Cursor template:** Tasks 1–7 map cleanly to checklist; reminds about truth checks and triage-only readyz.
- **INDEX.md:** Links all runbooks; easy to find.
- **Dockerfile:** Confirms `COPY configs/ /app/configs/` — gotcha #3 is already satisfied.
- **Deploy script:** Validates .env.cloudrun, Qdrant, prints service URL, runs healthz/readyz. Aligns with checklist.

### What is clunky

- **readyz contradiction:** `DEPLOYMENT_READINESS.md` and `DEPLOYMENT_MANUAL_STEPS.md` say "readyz → ok: true". Gotchas correctly say ok:false is OK for triage-only. Could block releases when triage works.
- **Checklist missing "which side changed":** Playbook has it; checklist does not. Operator may deploy both when only one changed, or forget to deploy one when both changed.
- **Cursor template placeholder:** `<FILL: e.g. ui-smoky-beta.vercel.app>` — real alias is known (ui-smoky-beta.vercel.app). Template could ship with default.
- **Overlap:** DEPLOYMENT_READINESS, playbook, checklist all have post-deploy checks. DEPLOYMENT_READINESS is first-deploy oriented; playbook/checklist are release-oriented. Acceptable but could confuse.

**Classification:** Usable but clunky — needs small cleanup before real use.

---

## 2. Dry-run execution summary

### Pre-deploy

| Check | Result |
|-------|--------|
| `git status` | Ran; 46 modified files, many untracked. Backend + frontend both changed. |
| `cd ui && npm run build` | PASS (21s) |
| `bash scripts/guardrail_inbox_triage.sh` | PASS (49 scenarios, 38 multi-turn, 27 adversarial, 15 sim assistant) |
| `.env.cloudrun` | Exists; QDRANT_*, OPENAI_API_KEY, ALLOWED_ORIGINS documented in demo.env.example |
| Which side changed? | Both — would deploy backend and frontend |

### Backend path

- Deploy script exists and is well-structured.
- Script runs healthz/readyz; prints "readyz FAILED (may be normal...)" — aligns with gotchas.
- Script does **not** run triage API test — checklist correctly requires it separately.
- **Ambiguity:** Checklist says "inspect (ok:false OK if triage-only; see gotchas)" — clear. DEPLOYMENT_READINESS said "ok: true" — fixed.

### Frontend path

- `cd ui && vercel --prod` is documented.
- Production alias: ui-smoky-beta.vercel.app (from CHEN_KUI_TRIAL_PACK).
- VITE_API_BASE_URL must be set in Vercel for production.
- **Ambiguity:** "Vercel production alias confirmed" — operator must know to open dashboard or printed URL. Playbook says "open printed URL and confirm visible changes." Adequate.

### Post-deploy verification

- Order: healthz → readyz → triage API → browser load → CORS → triage flow → visible UI.
- **Sensible:** healthz first (service up), then readyz (inspect, don’t block), then triage (real intake path), then browser (user truth).
- **Gap:** Checklist doesn’t say "run triage API against production URL" explicitly in post-deploy — it’s in Backend Deploy. For backend-only release, post-deploy would still need triage. Acceptable; Backend Deploy covers it.

### Friction observed

1. **readyz contradiction** — would cause false blocks.
2. **No "which side changed"** — easy to deploy wrong subset.
3. **Template placeholder** — minor friction; default alias helps.

---

## 3. Process fixes made

| File | Change | Why |
|------|--------|-----|
| `docs/DEPLOYMENT_READINESS.md` | readyz: "ok: true" → "inspect (ok:false OK for triage-only; see runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md)" | Align with gotchas; avoid blocking when triage works. |
| `docs/runbooks/DEPLOYMENT_MANUAL_STEPS.md` | Same readyz fix | Same reason. |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Added "Which side changed? (backend only / frontend only / both)" to Pre-Deploy | Ensures deploy path matches changes. |
| `docs/runbooks/CURSOR_RELEASE_PROMPT_TEMPLATE.md` | Placeholder → "ui-smoky-beta.vercel.app — update if different" | Ship with real default; less friction. |

---

## 4. Second-pass usability check

- **Easier now?** Yes. readyz no longer blocks triage-only releases. "Which side changed" prompts correct deploy path. Template has real alias.
- **Still awkward?** Minor: DEPLOYMENT_READINESS and playbook both have post-deploy sections. DEPLOYMENT_READINESS is first-deploy; playbook is release. Keeping both is fine — different audiences.
- **Checklist flow:** Pre-deploy → Backend → Frontend → Post-deploy → Final Truth. Order is good.

---

## 5. Recommended future release rhythm

### Every release (must-do)

1. Run `RELEASE_CHECKLIST.md` top to bottom.
2. Pre-deploy: git status, npm build, guardrail, env check, which side changed.
3. Deploy backend if backend changed; deploy frontend if frontend changed.
4. Post-deploy: healthz, readyz (inspect only), triage API test, browser load, CORS check.
5. Final truth: backend live, frontend live, aligned (ALLOWED_ORIGINS + VITE_API_BASE_URL).
6. Do **not** claim success until all checked.

### Only when needed

- **Playbook:** First-time deploy, troubleshooting, roll-forward.
- **Gotchas:** When something fails (readyz, CORS, configs, alias).
- **Cursor template:** When using Cursor for deploy; paste and fill.

### When browser verification is mandatory

- Every user-visible change (UI, copy, flows).
- Every trust/state-related change.
- After first deploy to new URL/alias.

### When to trust deploy success

- healthz 200 + triage API PASS + browser loads + no CORS.
- readyz ok:false is **not** a blocker for triage-only; run triage API instead.

---

## 6. Final verdict

**Accept as default release process** — with one caveat:

- **Caveat:** Human browser verification is required for user-visible changes. Checklist says it; operators must not skip it.

---

## 7. 中文总结

- **流程顺不顺手？** 顺手。checklist 短、步骤清晰，playbook 和 gotchas 互补。
- **Checklist 够不够短、够不够实用？** 够短（~15 项），够实用。补了「哪边改了」一项，避免误发。
- **哪些地方补强了？** (1) readyz 不再要求 ok:true，triage 可用即可；(2) 增加「backend/frontend/both」判断；(3) Cursor 模板默认填好生产别名。
- **以后发版怎么做最省心？** 每次发版跑一遍 RELEASE_CHECKLIST；有疑问查 playbook；出问题查 gotchas；用 Cursor 发版时贴模板。发完必须做一次浏览器验证（有 UI 改动时）。

---

## 8. COPY/PASTE RELEASE RHYTHM BLOCK

```
RELEASE RHYTHM — Chen Kui Insurance Unified Entry

Every release:
  1. RELEASE_CHECKLIST.md top to bottom
  2. Pre-deploy: git status, npm build, guardrail, env, which side changed
  3. Deploy backend if backend changed; frontend if frontend changed
  4. Post-deploy: healthz, readyz (inspect), triage API, browser, CORS
  5. Final truth: backend live, frontend live, aligned
  6. Do NOT claim success until all checked

When to consult:
  - Playbook: first deploy, troubleshooting
  - Gotchas: readyz/CORS/configs/alias failures
  - Cursor template: when using Cursor for deploy

Biggest gotchas:
  - readyz ok:false is OK for triage-only — run triage API, don't block
  - ALLOWED_ORIGINS must include real Vercel URL
  - Production alias may be stale after vercel --prod — confirm in dashboard
  - configs/ must be in Docker image (Dockerfile has COPY configs/)

When to trust deploy success:
  - healthz 200 + triage API PASS + browser loads + no CORS

When manual browser verification is mandatory:
  - Every user-visible change
  - Every trust/state change
  - After first deploy to new URL
```
