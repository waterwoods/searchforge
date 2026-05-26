# FUTURE_SAAS_OPERATING_SYSTEM — Final Report

**Sprint SSOT:** `docs/sprints/FUTURE_SAAS_OPERATING_SYSTEM_SPRINT.md`  
**Date:** 2026-05-07  

---

### 1. What changed technically

- Added sprint **SSOT** and this **final report** under `docs/sprints/`.
- Tightened **`validate_client_pack_layout`** (`pack_validation.py`) to require `ui_copy.json` and `handoff_phrases.json` in each `configs/clients/<client_id>/` directory — fail-fast for incomplete onboarding packs.

---

### 2. What changed operationally

- Explicit inventory of **product vs lab** surfaces, **onboarding stages**, and **deployment/replay** expectations in one place for operators and reviewers.
- Clear statement that **`UNIFIED_INTAKE_PRODUCT_ONLY`** gates **routers**, not necessarily all **inline** FastAPI routes on `app_main.py` — reduces false confidence during security or launch reviews.

---

### 3. What changed architecturally

- Documented **authority boundaries** (triage vs PG finalize vs JSON fallback vs regression scripts) and **tenant evolution** path (`client_id` → future `org_id`/composite keys).
- No large structural code refactor — intentional per sprint charter.

---

### 4. What changed product-wise

- **SKU narrative** sharpened: Unified Intake as the sellable wedge; RAG demo as adjacent; platform agents as non-SKU.
- **Trust positioning:** regression/replay vs live LLM; audit as future export, not compliance today.

---

### 5. What changed for onboarding

- New client packs cannot pass layout validation if core JSON files are missing — catches incomplete copy earlier than runtime `FileNotFound`-style failures.

---

### 6. What changed for supportability

- Single doc answers “what breaks support?” (readiness, env mismatch, DB flags, PII in analytics) and points to **observation prefixes** (`UNIFIED_INTAKE_DB_OBS`).

---

### 7. What changed for replay/audit

- **Replay:** boundaries documented (deterministic scripts vs chaotic live LLM).
- **Audit:** reaffirmed `audit_export.py` as stub; export key list is the contract seed.

---

### 8. What changed for SaaS readiness

- **Readiness matrix** and **scaling risks** enumerated — largest remaining gap called out: **inline lab routes** still mounted in product-only profile.

---

### 9. What still blocks real SaaS

- Auth, billing, automated tenant provisioning, immutable audit store, truthful **minimal API surface** (inline routes), multi-office RBAC.

---

### 10. What still blocks scaling

- Manual onboarding factory; monolith image; **no org-scoped row keys**; founder-centric support; **no** rate limiting / abuse controls at the edge.

---

### 11. What should happen next

1. **Engineering:** Gate or move **inline** lab endpoints behind `UNIFIED_INTAKE_PRODUCT_ONLY` (or `lab` sub-app) with tests.
2. **Product:** Decide **second pilot** pricing + onboarding checklist owner.
3. **Ops:** Single-page **env matrix** (Cloud Run + Vercel) checked into `docs/runbooks/` when stable.

---

### 12. What should NOT happen next

- Rewriting **triage** or **resolver** for “elegance” without a pilot-observed bug.
- Adding **Stripe** before repeatable tenant onboarding.
- Claiming **product-only** equals minimal attack surface **without** inline-route work.

---

### 13. What the future operating model is

- **Tenant recipe:** identify → provision deploy slot → apply schema → drop client pack → set secrets → run guardrails → hand off URLs → monitor analytics and obs logs.

---

### 14. What the future deployment model is

- **Logical** product-only on shared Cloud Run **today**; **physical** slim image + staged promotion **tomorrow**.

---

### 15. What the future onboarding model is

- **Scriptable checklist** with exit codes (partially started via pack validation); evolve to **Terraform + migration job + pack version pin**.

---

### 16. What the future tenant model is

- **`(org_id, case_id)`** composite identity, authenticated **org context**, optional **per-office** queues — **not** implementable without schema + API migration.

---

### 17. What the next 10x leverage point is

- **Closing the product-only gap** by removing or feature-flagging **all** non-product FastAPI routes — one move improves **security narrative, support surface, and SaaS credibility** more than any single intake feature.

---

### 18. FINAL_ONE_LINE

**We documented the real operating system and tightened pack onboarding checks; the next leap is making product-only mode honest by gating every lab route, not just routers.**

---

## Validation run (2026-05-07)

Executed:

| Step | Outcome |
|------|---------|
| `python3 -m compileall -q services/fiqa_api services/core` | PASS |
| `PYTHONPATH=. pytest tests/test_pack_validation.py -q` | PASS |
| UI `npm run build` (Node **v22.22.0** on `PATH`; Vite 7 rejects Node 20.18.x) | PASS |
| `cd ui && npx --yes madge --circular --extensions ts,tsx src` | PASS (no cycles) |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS — `http_p95_ms` 4946.46, rollup assertions passed |

**Skipped:** guardrail optional HTTP test (no server on port 8001). **Repo-wide compileall** still fails on unrelated broken files — use scoped compile for CI until those are repaired.
