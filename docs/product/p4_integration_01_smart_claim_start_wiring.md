# P4 Integration 01 — Smart Claim Start Wiring

**Status:** Implemented — Mini Program flag **OFF (Pilot intentional)**; Cap 01–03 Founder QA is optional/separate  

**Date:** 2026-07-24  
**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Reuses (do not redesign):**

- Cap 01 — `docs/product/p4_capability_01_customer_lookup.md`
- Cap 02 — `docs/product/p4_capability_02_claim_prefill.md`
- Cap 03 — `docs/product/p4_capability_03_smart_claim_start.md`

---

## 1. Objective

Wire Cap 01 Lookup → Cap 02 Prefill → Cap 03 Smart Claim Start into the **existing** WeChat Mini Program Start Claim flow so a matched customer feels:

> “The system already knows me. I only need to explain what happened today.”

**Out of scope:** CRM / Epic / EZLynx, identity redesign, Customer table, multi-claim UI, VIN/docs as Start Claim blockers, Workbench redesign.

---

## 2. Architecture

```text
Mini Program opens
  → existing identity (person_link_key / wx_* session)   [P29B]
  → Customer Context (One Active Case)                  [unchanged]
  → if START_NEW_CLAIM and smartClaimStartEnabled:
        POST /api/h5/customer/smart-claim-start
          → Cap 01 lookup (session or mock_scenario)
          → Cap 02 PrefillResult
          → Cap 03 SmartClaimStartPlan
  → Render: Continue gate | chips + confirms | accident form
  → Existing Review path via submit → Entry / Receipt
```

Server plan is SSOT for presentation. Claim case remains SoR after submit. Lookup stays READ ONLY.

---

## 3. Feature flags

| Flag | Where | Default | Purpose |
|------|--------|---------|---------|
| `P4_CUSTOMER_LOOKUP_MOCK` | Cloud Run / env | **OFF** | Cap 01 mock directory |
| `smartClaimStartEnabled` | Mini Program `config.defaults.ts` / `config.local.ts` | **OFF** | Call Smart Claim Start API and render plan |

### Enable (Cloud QA)

1. In `.env.cloudrun.qa`: `P4_CUSTOMER_LOOKUP_MOCK=1`
2. Deploy: `bash scripts/deploy_cloud_qa.sh` then promote traffic to latest
3. In gitignored `miniapp/config.local.ts`: `smartClaimStartEnabled: true`
4. Optional Founder scenario: launch `?entry=form&scs=S3` (S1–S6)

### Disable / rollback

1. Mini Program: `smartClaimStartEnabled: false` (or remove) → existing accident form
2. Backend: unset / `P4_CUSTOMER_LOOKUP_MOCK=0` → plan is `BLANK_DEGRADE` (no fake chips)
3. No schema rollback. No data repair.

---

## 4. Files changed

| Path | Role |
|------|------|
| `services/fiqa_api/inbox_triage/smart_claim_start/service.py` | Cap 01→02→03 response builder |
| `services/fiqa_api/routes/h5_task_intake.py` | `POST /api/h5/customer/smart-claim-start` |
| `miniapp/services/smartClaimStartApi.ts` | MP client |
| `miniapp/utils/smartClaimStartPlan.ts` | Pure UI state from plan |
| `miniapp/components/smart-claim-start-panel/*` | Chips / confirms / continue gate |
| `miniapp/pages/start-claim/*` | Wire plan into existing form |
| `miniapp/config.defaults.ts` / `config.qa.ts` | MP flag (default OFF) |
| `scripts/deploy_cloud_run_core.sh` | Pass `P4_CUSTOMER_LOOKUP_MOCK` |
| `tests/test_p4_integration_01_smart_claim_start_wiring.py` | Backend tests |
| `miniapp/tests/smartClaimStartPlan.test.ts` | MP tests |
| `scripts/simulate_p4_integration_01_smart_claim_start.py` | S1–S6 simulation |

---

## 5. Scenario behavior

| Scenario | Mode | Customer experience |
|----------|------|---------------------|
| S1 | `CONTINUE_ACTIVE` | Continue gate; no new claim |
| S2 | `MATCHED_CONFIRM_VEHICLE` | Chips + vehicle confirm → accident facts |
| S3 | `MATCHED_KNOWN` | Known chips → ~4 accident inputs |
| S4 | `MATCHED_CONFIRM_POLICY` | Stale policy confirm → accident facts |
| S5 | `BLANK_DEGRADE` | No fake identity; accident facts |
| S6 | `BLANK_DEGRADE` / fetch fail | Same; no dead end |

---

## 6. UI rules

- Show “我们已了解您” chips for safe AUTO values only
- Mask phone as 尾号; VIN last4 only if Cap 03 shows it
- Never show OpenID, `person_link_key`, `case_id`, mock policy refs
- Photos do not block Start Claim (“现在可以跳过，之后也可以补交”)
- Accident time helper: “用于帮助确认事故顺序。”

---

## 7. Tests

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 -m pytest \
  tests/test_p4_integration_01_smart_claim_start_wiring.py \
  tests/test_p4_capability_03_smart_claim_start.py -q

cd miniapp && npm test -- tests/smartClaimStartPlan.test.ts tests/startClaimPage.test.ts
cd miniapp && npm run build:gate
cd miniapp && npm run test:component-gates
```

---

## 8. Simulation

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
  scripts/simulate_p4_integration_01_smart_claim_start.py
```

Expect `RESULT: PASS` with S1–S6 + rollback check.

---

## 9. Deployment

```bash
# Enable mock on Cloud QA env, then:
bash scripts/deploy_cloud_qa.sh
gcloud run services update-traffic fiqa-api-qa --region us-west1 --to-latest

FRONTEND_ORIGIN='https://ui-waterwoods-andys-projects-1f411b73.vercel.app' \
  bash scripts/run_deployment_qa_gate.sh
# Must print: READY FOR FOUNDER QA
```

Founder QA Workbench bookmark: see `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md`.

---

## 10. Rollback

See §3. Verified by simulation `rollback_flag_off` and MP default `smartClaimStartEnabled: false`.

---

## 11. Known limitations

- Mock lookup only — no live AMS
- `scs=` scenario override only when `P4_CUSTOMER_LOOKUP_MOCK=1`
- AUTO values are presentation-only this loop (not stamped into case create)
- Real One Active Case still owned by Customer Context; mock S1 uses Cap 03 continue gate

---

## 12. Founder QA checklist

- [ ] Cap 01 / 02 / 03 reused, not rewritten
- [ ] Matched customer sees known chips naturally
- [ ] Uncertain info requires confirmation (S2/S4)
- [ ] Matched path ~4–5 accident inputs
- [ ] S1 continues without duplicate claim
- [ ] S5/S6 degrade without dead end
- [ ] No technical IDs exposed
- [ ] Flag rollback works
- [ ] Deployment QA Gate prints READY FOR FOUNDER QA
- [ ] WeChat clean-cache compile passes
