# Execution Outline — Founder / Broker Trial Execution Sprint

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20  
**Target budget:** 45–90 minutes

---

## 1. Workstreams

| Role | Responsibility |
|------|----------------|
| Product/trial planner | Scenario pack, acceptance criteria, loop plan |
| Founder trial runner | Run customer + workbench paths; time-to-understand |
| Broker workflow evaluator | Next-step quality; scan-ability; trust |
| QA / simulation worker | Guardrails + simulation packs + API tests |
| Fix-now triage worker | Classify; implement smallest fix; retest |
| Acceptance reviewer | Deploy judgment; readiness statement |

---

## 2. Multi-loop plan

| Loop | Activity |
|------|----------|
| **0 — Baseline audit** | Read UI + configs; run automated packs; note strengths/risks |
| **1 — Trial execution** | Execute scenario pack; capture friction |
| **2 — Classify + fix** | Fix-now only; validate |
| **3 — Retest** | Re-run highest-value scenarios + guardrail |
| **4 (optional)** | Only if one obvious low-risk trust fix remains |

---

## 3. Validation commands

```bash
bash scripts/guardrail_inbox_triage.sh
# With server on 8001:
PYTHONPATH=. python3 scripts/test_inbox_triage_api.py --url http://localhost:8001
```

If UI changed:

```bash
cd ui && npm run build
```

---

## 4. Deployment approach

- **Backend change:** redeploy fiqa/RAG API per `docs/ANDY_QUICK_START.md` / team runbook.  
- **Frontend change:** redeploy UI alias per project standard.  
- If **no code change:** document “no redeploy required.”  

---

*End of Execution Outline*
