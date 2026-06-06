# P16-Z18 30-Day Execution Plan

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Single goal:** Customer Builder **76 → 90+**  
**Constraint:** No new architecture. Wire + validate + deploy + prove.

**Excluded from this plan:** CRM, Stripe, P17, voice, GraphRAG, platform rebuild, second office, new microservices, greenfield Customer Builder.

---

## Success definition (Day 30)

| Metric | Now | Target |
|--------|-----|--------|
| Customer Builder score (Z17 A–G avg) | **76** | **≥90** |
| Post-submit return → append (browser) | ❌ | ✅ |
| My Requests → Customer Entry handoff | ❌ | ✅ |
| 3-day Tesla walkthrough (UI) | API only | Browser PASS |
| Deployed cold URL | Blocked (Z12) | trial_launch_check PASS |
| Chen Kui supervised demo | NO-GO | GO |
| Observation log real cases | Partial | ≥3 multi-turn |

---

## Week 1 (Days 1–5): Close customer return loop

**Theme:** Same `case_id` after refresh — no new product code.

### Engineer (3.0–3.5 days total)

| Day | Task | File(s) | Done when |
|-----|------|---------|-----------|
| 1 | **Hydrate active `case_id` on Customer Entry mount** | `CustomerEntryTab.tsx`, `sessionStorage` key `unified_intake_active_case_id` | Refresh after submit shows append panel + case ref |
| 1–2 | **My Requests → pass `case_id` on continue** | `UserCaseListProgressPanel.tsx`, `UnifiedIntakePage.tsx`, `MyRequestsTab.tsx` | 去客户报送继续 loads case in Customer Entry |
| 2 | **Resume hint includes submitted Add-Car cases** | `CustomerEntryTab.tsx`, `caseLifecycleDisplay.ts` | Empty state offers continue for submitted cases |
| 2 | **Persist `lastCaseId` across refresh** | `CustomerEntryTab.tsx` | Append works after F5 |
| 3 | **Session DB ops verification** | `session_store.py`, deploy checklist | Pre-submit restore survives server restart on demo env |
| 3–4 | **3-day Tesla browser walkthrough** | — | Day1 submit → Day2 VIN append → Day3 driver append — all in UI |
| 4–5 | **Fix walkthrough blockers only** | Minimal diff | No scope creep |

**Week 1 exit:** Customer Builder Cap 1 ≥88 · Cap 4 ≥85 · scorecard avg ≥85.

---

## Week 2 (Days 6–10): Deploy + validation

**Theme:** Prod path matches local proof.

### Engineer + Founder

| Day | Task | Owner | Done when |
|-----|------|-------|-----------|
| 6 | Cloud Run secrets + deploy | Founder + Dev | `deploy_paid_pilot.sh` succeeds |
| 6–7 | CORS + Preview origin alignment | Dev | UI calls API without CORS fail |
| 7 | Re-run Z12 acceptance cases on prod | Dev | Payment · remove · claim routes pass |
| 7–8 | `guardrail_inbox_triage.sh` + P16-Y ≥88 | Dev | Green |
| 8 | Role D battery on deployed path | Dev | reread ≥80, need_wechat ≤2/10 |
| 9 | `trial_launch_check.sh` PASS | Dev | Single pre-trial green |
| 10 | Buffer / regression fixes only | Dev | Batteries stay green |

**Week 2 exit:** Cap 7 ≥85 · cold URL loads · engine parity prod = local.

---

## Week 3 (Days 11–15): Founder testing

**Theme:** Reality test — no narration.

### Andy (founder)

| Day | Task | Done when |
|-----|------|-----------|
| 11 | Cold URL Turn 1: customer Add-Car message → submit | case_id in My Requests |
| 12 | Day 2 simulation: return via My Requests → append VIN | Broker sees update without customer chat |
| 13 | Day 3: append driver info · verify timeline | 11+ messages, formal_submitted_at unchanged |
| 14 | Broker path: paste cancel notice → copy → append correction | Two-turn without WeChat re-read |
| 15 | Log 3 cases in observation log | case_ids + timestamps recorded |

**Week 3 exit:** Cap 7 ≥90 · Customer Builder avg ≥88 · founder sign-off.

---

## Week 4 (Days 16–20): Chen Kui testing

**Theme:** Supervised pilot → payment conversation.

| Day | Task | Owner | Done when |
|-----|------|-------|-----------|
| 16 | Prep: send cold URL + 5-min SOP (customer link OR broker paste) | Andy | Chen Kui can open without SSO |
| 17 | **Supervised demo** — customer Case Builder loop | Andy + Chen Kui | Chen Kui sees draft → confirm → timeline |
| 18 | Chen Kui runs one real case (Andy on standby) | Chen Kui | Client reply positive or neutral |
| 19 | Debrief + top 3 friction notes (log only) | Andy | No new features — wire list if blocking |
| 20 | Invoice sent ($49–99 pilot) | Andy | Invoice ID in observation log |

**Week 4 exit:** Customer Builder ≥90 · commercial gate G4 in progress.

---

## Days 21–30: Buffer + scorecard re-baseline

| Only if needed | Trigger |
|----------------|---------|
| Copy rename (Case Builder / My Cases) | After functional GO |
| TOP5 copy fixes blocking trust | Log-driven |
| Battery regression fix | CI red only |

**Do NOT start:** Stripe, CRM, P17, voice, GraphRAG, second office, customer auth, full timeline UI polish.

---

## Daily commands

```bash
bash scripts/run_demo_local.sh
bash scripts/operator/guardrail_inbox_triage.sh
bash scripts/trial_launch_check.sh
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16y_case_battery.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py
```

---

## Development OS (unchanged from Z9)

```
SSOT (P16Z18_*) → Wire only → Validate (guardrail → p16y → role_d) → Reality test → Update SSOT
```

Sprint types allowed: **Ship** · **Validate** · **Archive** — nothing else.

---

## Must / Should / Never (30 days)

### Must (pilot blocked without)

1. Hydrate `case_id` in Customer Entry  
2. My Requests handoff  
3. Resume submitted cases  
4. 3-day browser walkthrough PASS  
5. Deploy + trial_launch_check PASS  
6. Founder 3× observation log  
7. Chen Kui supervised demo  

### Should (payment odds)

1. Customer-facing tab rename copy  
2. Post-copy append hint on broker path (if not deployed)  
3. Invoice + testimonial ask  

### Never (30 days)

See `P16Z18_NEVER_BUILD.md` — full list.

---

## One-line 30-day plan

> **Wire return-later (3–4 days) → deploy → founder 3-day proof → Chen Kui supervised → invoice. Nothing else.**

---

*End of P16-Z18 Phase 9 — 30-Day Execution Plan*
