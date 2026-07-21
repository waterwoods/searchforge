# Customer Language Guide — Engineer → Broker

**Purpose:** Translate internal/platform terms into broker-safe language.  
**Use when:** Writing broker docs, support replies, demo scripts, or explaining manifest exports.

**Rule:** If Chen Kui would not understand the term, use the broker column.

---

## Deployment & infrastructure

| Engineer language | Broker language |
|-------------------|-----------------|
| deployment manifest | support configuration summary |
| deployment identity | your office setup ID |
| Cloud Run service | hosted backend |
| Vercel frontend | web app URL |
| Postgres / PG-primary | secure case database |
| JSON case files | local demo storage (not production) |
| platform_full | lab/research mode (not your product) |
| UNIFIED_INTAKE_PRODUCT_ONLY=1 | production product mode |
| intake_core_readiness | intake service ready check |
| ENV=prod | live paid environment |
| schema_epoch / intake_schema_epoch | database version (support only) |
| org continuity column | office record linking (support only) |

---

## API & security (support-facing)

| Engineer language | Broker language |
|-------------------|-----------------|
| token_scope_registry | access permission list (support) |
| UNIFIED_INTAKE_INTAKE_API_KEY | intake connection key (founder manages) |
| UNIFIED_INTAKE_SUPPORT_API_KEY | support export key (founder manages) |
| tenant_truth | your office identity record |
| replay_lineage | case history export metadata |
| office_ownership | which office owns this case |
| deployment_profile | environment settings bundle |
| anonymous intake | unsecured access (never on production) |

---

## Product & workbench

| Engineer language | Broker language |
|-------------------|-----------------|
| Unified Intake | Unified Intake (keep — product name) |
| inbox triage | message sorting into cases |
| triage_message / triage_conversation | analyze message (internal) |
| Case focus | what this case is about |
| broker_next_step | your next move |
| collected_fields | collected info chips |
| still_needed_fields | still needed chips |
| conversation_summary | case summary text |
| Simulation Assistant | practice scenarios |
| founder demo queue | sample cases for learning |
| Customer Entry | customer message input tab |
| Broker Workbench | your case management view |
| append / paste follow-up | update with new customer message |
| human confirmation recommended | please verify this info |
| Work now / Waiting or parked | urgent cases vs tracking |
| SIM1, SIM2, … | scenario names only (never say SIM IDs to broker) |

---

## Health & readiness (founder/support)

| Engineer language | Broker language |
|-------------------|-----------------|
| /readyz | system ready check |
| intake_path_ready | intake is working |
| /ready | legacy full-system check (ignore for intake) |
| embedding_warming | system starting up — try again in a minute |
| Qdrant | knowledge search database (optional) |
| 503 | temporary unavailable — retry |
| guardrail_inbox_triage.sh | quality check (founder runs) |
| demo_pre_checklist.sh | demo prep check (founder runs) |

---

## Scenarios (internal → broker)

| Internal category | Broker Case focus label |
|-------------------|-------------------------|
| payment_lapse_expiration | Payment / cancellation risk |
| missing_document | Missing document |
| add_car / new_vehicle | Add car on policy (保单加车) — not a claim |
| premium_review | Premium review |
| claim_intake | Claim intake |
| customer_question | Customer question |
| remove_vehicle | Remove car |

---

## Vehicle language (Policy vs Claim)

**SSOT:** `docs/product/CLAIM_VEHICLE_VS_ADD_CAR_TERMINOLOGY.md`

| Engineer / internal | Broker / customer language |
|---------------------|----------------------------|
| Add Car / `SERVICE_LANE_ADD_CAR` / legacy “Add Vehicle” | 保单加车 — add or replace a vehicle on the policy |
| Claim Vehicle / claim `vehicle_information` | 事故车辆 / 车辆信息 — which car is in this accident claim |
| Vehicle Identity / Claim Vehicle Identity | (do not say — internal storage object) |
| VIN on a claim Request More | VIN / 车架号 (claim follow-up, not 保单加车) |

Never tell a broker that collecting claim VIN/year-make-model is “加车.”

---

## Phrases to avoid with brokers

| Don't say | Say instead |
|-----------|-------------|
| "The triage pipeline returned…" | "The system analyzed your message and…" |
| "PG-primary writes failed" | "We couldn't save the case — contact support" |
| "platform_full leak" | (don't mention — founder fixes) |
| "schema migration epoch mismatch" | "Support is updating your office setup" |
| "token scope registry entry" | "Your access settings" |
| "Run guardrail" | "We're running a quick quality check" |
| "JSON read fallback" | (don't mention) |
| "dual-write disabled" | (don't mention) |

---

## Phrases that work with brokers

- "Paste the message as you received it."
- "Review the draft before you send."
- "Nothing is sent automatically."
- "Collected shows what we understood; Still needed shows what to ask next."
- "Same-day action means handle today."
- "Reopen the case to continue where you left off."

---

*End of customer language guide*
