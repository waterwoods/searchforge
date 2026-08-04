# Pilot-Ready Release Gates V1

**Status:** Authoritative release labeling for Case Builder Sunday V1  
**Date:** 2026-08-03  
**Applies to:** Cloud QA demonstrable release / soft pilot conversation readiness  
**Does not authorize:** Production deploy, waterwoods retarget, or `PRODUCTION READY` without additional gates below  
**North Star:** `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md`  
**Execution plan:** `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md`

---

## Purpose

Define the hard P0 gates and final labels for the six-day window.  
Every public or customer-facing claim must be backed by **code, automated test, or Founder evidence**. Aspiration is not evidence.

---

## Required P0 gates

| # | Gate | How to prove | Blocking if fail? |
|---|------|--------------|-------------------|
| 1 | No regression in Stage 1 deterministic workflow | Stage 1 critical automated tests + evidence pack still valid; Request More → supplement → ack → office accept path works on QA | Yes |
| 2 | Known-customer confirmation remains correct | Stage 2 path: CONFIRM_EXISTING → Cap2/Brief `已有保单资料，客户已确认`; no forced insurance-card fabrication | Yes |
| 3 | LangGraph never mutates Claim lifecycle | Propose/confirm APIs and tests assert `lifecycle_mutated=false`; no submit/close/status transition from graph | Yes |
| 4 | Invalid model output and timeout preserve manual continuation | Fixture tests for invalid JSON / timeout / hallucinated fields → deterministic fallback; customer can still complete intake | Yes |
| 5 | Unconfirmed AI proposals never become authoritative facts | Confirm with `confirm=false` persists nothing authoritative; Brief shows AI-proposed vs customer-confirmed | Yes |
| 6 | Broker and customer projections show consistent truth | Same case: customer task / Cap2 vs Workbench Brief authority labels and known facts align after confirm | Yes |
| 7 | No cross-tenant or cross-customer evidence access | Invite isolation + tenant/client boundary tests; audit note from Day 4 | Yes |
| 8 | No secrets or raw sensitive data in traces or Git | `.env*` not committed; LangSmith/trace redaction policy; git hygiene check before tag | Yes |
| 9 | Metrics and exporter reads do not mutate business state | Timing V1 integrity evidence; exporter `X-Case-Activity-Record: 0` / GET never stamps; AI feedback reads same rule | Yes |
| 10 | QA/demo reset is safe and repeatable | Prepare Demo / Fast Lane / documented reset; does not touch Production | Yes |
| 11 | Production remains untouched until explicit release decision | Deploy logs target `fiqa-api-qa` only; waterwoods/Production unchanged in week evidence | Yes |
| 12 | Every release claim is backed by code, test or evidence | Evidence index links each claim; unsupported metrics explicitly labeled | Yes |

---

## Supporting P1 gates (do not alone create PILOT READY)

| Gate | Notes |
|------|-------|
| LangSmith offline regression gate green | Required for strong FDE portfolio; advisory for customer demo if PR A frozen |
| AI Accept/Edit/Reject events exporting | Required before any AI quality % claim |
| MCP read-only tools documented | Delivery layer; not customer-facing |
| Consent/retention draft reviewed by Founder | Soft pilot conversation aid; not legal certification |
| Cost-saving QA scale restored after demos | Ops hygiene |

---

## Final labels

### `DEMO READY`

All of the following are true:

- Gates 1–6, 9–12 PASS on Cloud QA
- Founder can run one-click (or single script) Chen Camry demo for the complete + missing-info paths
- AI assist path either frozen with evidence **or** feature-flagged off with fallback demo still smooth
- No Production/waterwoods mutation

Allowed language: “Founder-demonstrable on QA,” “truthful V1 demo.”  
Forbidden language: paid-pilot validated, production-ready, proven customer ROI.

### `PILOT READY WITH RESTRICTIONS`

All `DEMO READY` conditions plus:

- Gates 7–8 PASS with written Day-4 safety audit
- Model fallback + feature flag/rollback verified
- Consent/retention **draft** exists and Founder accepts restrictions list
- Metrics honesty: no unsupported ROI claims in customer materials
- Explicit restrictions recorded (examples): QA-only hosting; single office; demo personas; AI assist optional; no carrier filing; n small for metrics

Allowed language: “Ready for a supervised soft pilot conversation with restrictions.”  
Still forbidden: Production certification; multi-office GA; legal compliance complete.

### `NOT PILOT READY`

Any P0 gate fail, or Founder walkthrough blocked, or evidence missing for a claim the release wants to make.

### `PRODUCTION READY` (not used this week by default)

Do **not** apply unless **all** of the following are independently proven:

- Paid-pilot env profile (`CURRENT_PRODUCT_SHAPE.md`) validated on the target service
- Security, privacy, retention, and operational on-call gates signed
- Real-user (not only Founder) journey evidence
- Explicit Founder production release decision

Absence of any item → cannot use this label.

---

## Claim → evidence mapping (minimum)

| Claim | Minimum evidence |
|-------|------------------|
| Stage 1 works | Tag `stage1-founder-validated-demo-2026-08-03` + closeout |
| Stage 2 known-customer confirm | Stage 2 closeout + phone evidence folder |
| Timing metrics trustworthy | `REAL_USAGE_TIMING_V1_CLOSEOUT.md` + integrity pack |
| Bounded AI assist safe | LangGraph tests + freeze tag + Brief label proof |
| AI quality measured | Accept/Edit/Reject events + QA report (after Day 3) |
| Observability | LangSmith/local eval gate evidence (after Day 2) |
| Safe for soft pilot talk | Day 4 audit + consent draft + this gates checklist |

---

## Sunday checklist (operator)

- [ ] Critical automated tests PASS  
- [ ] One Founder E2E walkthrough PASS (or FAIL → `NOT PILOT READY`)  
- [ ] Only P0 fixes landed after freeze candidate  
- [ ] Short demo recorded  
- [ ] QA cost-saving scale restored  
- [ ] Evidence index updated  
- [ ] Final label chosen and written in release status note  
- [ ] Production / waterwoods confirmed untouched  

**Release status note path (create on Sunday):** `docs/release/SUNDAY_V1_RELEASE_STATUS_2026-08-09.md`
