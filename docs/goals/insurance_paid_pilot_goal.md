# Insurance Paid Pilot — Mission & Goal

**Created**: 2026-03-06  
**Scope**: SearchForge → California Auto Insurance Broker Assistant  
**Phase**: Commercialization Sprint — First Paid Pilot

---

## 1. Mission

Turn the existing insurance demo into a broker-specific paid pilot as fast as possible, with minimal manual work from Andy.

---

## 2. Target Customer

- **Primary**: California auto insurance brokers (e.g., 陈奎)
- **Profile**: Serves Chinese-speaking clients; needs quick answers with official citations (DMV, CDI, insurers)
- **Pain**: Manual lookup of DMV/CDI/insurer pages; copy-paste to WeChat; compliance verification

---

## 3. Business Goal

- **First paid pilot** within 2–3 weeks
- **Manual payment** (Zelle/Venmo/WeChat) acceptable for v1
- **Single broker** pilot; no multi-tenant auth required
- **Testimonial** as success metric for next phase

---

## 4. Scope (In Scope)

| Area | What |
|------|------|
| **Demo** | Live demo to broker; 15-min script; 5 validated questions |
| **UI** | Broker-specific feel (header, sample questions, copy-to-client) |
| **Backend** | `mode=demo` → `auto_insurance_demo_core`; translation; gov+insurer diversity |
| **Data** | `auto_insurance_demo_core` ≥20 docs; one-click ingest |
| **Validation** | `demo_quick_validate.sh` PASS before every demo |
| **Deploy** | Backend on Cloud Run; frontend shareable (Vercel/ngrok/local) |
| **Payment** | Manual invoice; Zelle/Venmo/WeChat |
| **Onboarding** | Manual email with URL + 3 steps |

---

## 5. Non-Goals (Out of Scope)

| Area | What |
|------|------|
| **Stripe** | No billing integration |
| **Multi-tenant** | No auth, no per-broker isolation |
| **LLM generation** | Retrieval + snippets + bullets suffice |
| **JobHunter / Mortgage / Vitals** | Not in scope |
| **China / Europe** | US/California only |
| **Repo cleanup** | No broad refactor |

---

## 6. Constraints

- **Document first, then code**
- **Guardrails first, then release**
- **Failures → scripts, reports, reusable assets**
- **Human only does final acceptance and business decisions**
- **Optimize for first paid pilot, not technical perfection**

---

## 7. Deliverables

| Deliverable | Owner | Acceptance |
|-------------|-------|------------|
| Goal doc | Cursor | This document |
| Business rules | Cursor | `docs/business_rules/insurance_broker_pilot_rules.md` |
| Release gate | Cursor | `docs/release/insurance_demo_gate_v1.md` |
| Status report | Cursor | `reports/openclaw/insurance_paid_pilot_report_v1.md` |
| Demo runnable | Cursor | `run_demo_local.sh` → PASS |
| Validation pass | Cursor | `demo_quick_validate.sh` → PASS |
| Broker demo | Andy | 15-min live demo to broker |
| First payment | Andy | Manual invoice sent and paid |

---

## 8. Acceptance Criteria

### Demo Gate (Must Pass Before Live Demo)

1. `bash scripts/run_demo_local.sh` → Demo URL printed; backend healthy or Offline fallback works
2. `bash scripts/demo_quick_validate.sh` → Overall: PASS
3. `auto_insurance_demo_core` has ≥20 points
4. `ui/src/assets/demo_fallback.json` has 3+ items (or DEFAULT_FALLBACK_ITEMS used)
5. `.env.cloudrun` has `QDRANT_URL`, `QDRANT_API_KEY` (for Cloud Run deploy)
6. 5 sample questions visible in UI; 3+ validated in quick_validate
7. Broker-specific header visible (e.g., "保险经纪人智能助手")
8. "复制给客户（可直接发微信）" button works

### First Payment Criteria

1. Broker has used demo; feedback captured
2. Invoice sent (PDF or table)
3. Payment received (Zelle/Venmo/WeChat)

---

*End of goal document*
