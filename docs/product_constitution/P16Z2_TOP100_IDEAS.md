# P16-Z2 Phase 6 — Top 100 Ideas Worth Copying

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Scoring:** Difficulty (S/M/L), ROI (★–★★★★★), Chen Kui Fit (0–10), Insurance Fit (0–10)

**Legend — Difficulty:** S = ≤1 day, M = 2–5 days, L = 1+ weeks  
**Legend — Expected impact:** Time saved per case, trial conversion lift, or retention

---

## Category A — Conversation → Record (1–15)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 1 | Message-first intake (no category pick) | Intercom | M | ★★★★★ | 10 | 10 | Eliminates #1 customer friction |
| 2 | Paste → structured case in one action | Salesforce Case Classification | S | ★★★★★ | 10 | 10 | Core wedge — already built |
| 3 | Conversation → ticket convert API | Intercom | M | ★★★★☆ | 8 | 9 | Maps to formal handoff moment |
| 4 | Typed ticket attributes per issue type | Intercom ticket_types | M | ★★★★☆ | 9 | 10 | Maps to category-specific fields |
| 5 | Context-first issue creation | Linear Agent | M | ★★★★☆ | 9 | 8 | Paste creates case, not form |
| 6 | Immutable message thread on record | Intercom ticket_parts | S | ★★★★☆ | 8 | 9 | case_messages[] — wire UI |
| 7 | Side conversation (internal notes) | Zendesk | M | ★★★☆☆ | 7 | 7 | Broker notes exist — expose |
| 8 | Requester auto-identify from paste | Salesforce Contact match | L | ★★★☆☆ | 6 | 8 | Defer — no CRM |
| 9 | Channel-agnostic case object | Zendesk omnichannel | S | ★★★★☆ | 9 | 9 | Already one case model |
| 10 | Snippet from conversation → summary | Salesforce Wrap-Up | S | ★★★★★ | 10 | 10 | P16-Y P0 append merge |
| 11 | Intent detection before structure | Intercom Fin | M | ★★★★★ | 10 | 10 | triage.py — maintain |
| 12 | Confidence score on classification | Salesforce Einstein | S | ★★★☆☆ | 7 | 8 | Surface v4/v5 risk |
| 13 | "Same issue?" boundary on append | Zendesk merge | S | ★★★★☆ | 9 | 9 | append boundary exists |
| 14 | Rolling entity ledger not raw history | Context engineering | M | ★★★★★ | 9 | 10 | collected_fields pattern |
| 15 | Compress old turns, keep recent verbatim | Zendesk Copilot | M | ★★★★☆ | 8 | 9 | Summary merge architecture |

---

## Category B — Multi-Turn & Continuity (16–30)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 16 | Append to existing case, not new ticket | Zendesk | S | ★★★★★ | 10 | 10 | Backend done — UX broken |
| 17 | Post-copy "customer replied?" CTA | Intercom handoff | S | ★★★★★ | 10 | 10 | Fixes 38/100 next-step |
| 18 | waiting_on: customer after send | HubSpot | S | ★★★★☆ | 9 | 9 | State clarity |
| 19 | Session restore mid-flow | Intercom | S | ★★★★☆ | 8 | 8 | session_store exists |
| 20 | Correction keyword detection | Salesforce field history | S | ★★★★☆ | 9 | 9 | Fixes Y44 |
| 21 | Last-write-wins on conflicting fields | Stripe merge | S | ★★★★☆ | 8 | 9 | Simple rules |
| 22 | Customer portal for case status | HubSpot portal | M | ★★★★☆ | 8 | 8 | 我的办理 — hidden |
| 23 | "Continue this case" deep link | Intercom | S | ★★★★☆ | 9 | 8 | Resume hint exists |
| 24 | Follow-up snooze date | Intercom snooze | S | ★★★☆☆ | 8 | 7 | follow-up editor hidden |
| 25 | Activity timeline on case | Salesforce Case Feed | S | ★★★☆☆ | 7 | 8 | Backend exists — hidden |
| 26 | Multi-turn message count in glance | P16-Y rubric | S | ★★★☆☆ | 7 | 8 | Trust signal |
| 27 | Don't re-triage full thread each turn | Context patterns | S | ★★★★☆ | 9 | 9 | triage_for_append pattern |
| 28 | Escalation after 2 failed gap-fills | ClaudeGuide support | S | ★★★☆☆ | 7 | 7 | Reduce loop |
| 29 | Structured handoff summary on escalate | Intercom Fin | S | ★★★★☆ | 9 | 9 | conversation_summary |
| 30 | Cross-device case ID for customer | HubSpot portal | M | ★★★☆☆ | 6 | 7 | Week 3+ |

---

## Category C — Next Action & Office Workflow (31–45)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 31 | One operational broker_next_step sentence | Salesforce NBA | S | ★★★★★ | 10 | 10 | Rubric ceiling fix |
| 32 | Copy-to-WeChat as primary action | Intercom saved reply | S | ★★★★★ | 10 | 10 | Killer feature — exists |
| 33 | Category-specific action templates | Zendesk macros | S | ★★★★★ | 10 | 10 | ui_copy.json |
| 34 | Deadline countdown in glance | Zendesk SLA | S | ★★★★☆ | 10 | 10 | Cancel wedge |
| 35 | Urgent-today queue filter | Zendesk views | M | ★★★★☆ | 10 | 10 | 50 unread WeChat |
| 36 | waiting_on pill (office/customer/carrier) | Salesforce Case | S | ★★★★☆ | 9 | 9 | Field exists |
| 37 | Risk badge "需核实" | Salesforce confidence | S | ★★★☆☆ | 8 | 9 | v4 score hidden |
| 38 | client_prep as customer macro | Zendesk macro | S | ★★★★★ | 10 | 10 | Exists — improve ZH |
| 39 | Post-handoff single CTA | Linear minimal UI | S | ★★★★☆ | 9 | 8 | P16-N confirmation |
| 40 | "Mark sent to client" state | HubSpot | S | ★★★★☆ | 9 | 8 | Missing today |
| 41 | Office action type enum | Salesforce Flow | S | ★★★☆☆ | 7 | 8 | call/email/quote |
| 42 | Still-needed as numbered ask list | Intercom Fin | S | ★★★★☆ | 9 | 10 | still_needed_fields |
| 43 | Generic wording blocklist | P16-Y rubric | S | ★★★★★ | 10 | 10 | Enforce in engine |
| 44 | Wrap-up on case close | Salesforce Einstein | M | ★★★☆☆ | 7 | 7 | Defer |
| 45 | Next contact by from deadline | Zendesk SLA | S | ★★★★☆ | 9 | 10 | deadline → follow_up |

---

## Category D — Document & Evidence (46–58)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 46 | Evidence packet assembly | Stripe Smart Disputes | M | ★★★★★ | 10 | 10 | Cancel notice pattern |
| 47 | recommended_evidence → still_needed | Stripe | S | ★★★★★ | 10 | 10 | Exists as still_needed |
| 48 | OCR → collected_fields with [OCR] tag | IDP industry | S | ★★★★☆ | 9 | 10 | Wire existing pipeline |
| 49 | notice_image when screenshot claimed | P16-Y | S | ★★★★☆ | 9 | 10 | Y38 — done |
| 50 | Confidence-gated auto-fill | Salesforce 85% gate | M | ★★★☆☆ | 7 | 8 | Week 3 |
| 51 | Doc type classification | IDP Scry AI | L | ★★★☆☆ | 6 | 8 | Defer |
| 52 | Broker upload before customer upload | Stripe manual first | S | ★★★★☆ | 10 | 10 | Correct wedge order |
| 53 | Merge paste text + OCR fields | Stripe prefer_smart | S | ★★★★☆ | 9 | 10 | ocr_case_fusion exists |
| 54 | Deadline from notice OCR | IDP | M | ★★★★☆ | 10 | 10 | Cancel wedge |
| 55 | VIN validation (17 char) | IDP rules | S | ★★★☆☆ | 7 | 9 | Simple rule |
| 56 | Human-in-loop before client copy | All IDP | S | ★★★★★ | 10 | 10 | Broker always reviews |
| 57 | PDF → screenshot fallback UX | Pragmatic | S | ★★★☆☆ | 9 | 8 | No PDF build needed |
| 58 | Attachment on case record | Salesforce Files | S | ★★★☆☆ | 8 | 8 | Exists — promote |

---

## Category E — Customer Experience (59–72)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 59 | Single primary button on landing | Intercom messenger | M | ★★★★★ | 9 | 9 | P16-N critical |
| 60 | Free-text hero, not 3 equal buttons | Intercom | M | ★★★★★ | 9 | 9 | P16-N |
| 61 | Example in placeholder not toggle | Best SaaS | S | ★★★☆☆ | 8 | 8 | P16-N |
| 62 | Progress in plain Chinese | HubSpot portal | S | ★★★★☆ | 9 | 8 | Not engineer labels |
| 63 | "What happens next" after submit | HubSpot portal | S | ★★★★☆ | 9 | 8 | One sentence |
| 64 | Customer status tab | HubSpot portal | M | ★★★★☆ | 8 | 8 | 我的办理 hidden |
| 65 | Separate customer URL route | Intercom | M | ★★★☆☆ | 7 | 7 | P16-M #23 |
| 66 | No file upload label without upload | UX honesty | S | ★★★★☆ | 8 | 8 | P16-N mismatch |
| 67 | Mobile-first customer flow | Intercom | M | ★★★☆☆ | 8 | 7 | WeChat users |
| 68 | Minimal objects on screen (8–10) | Linear | M | ★★★★☆ | 8 | 7 | P16-N score 50 |
| 69 | Intent inferred from message | Intercom Fin | M | ★★★★★ | 10 | 10 | Engine exists |
| 70 | Confirmation without essay | Linear | S | ★★★★☆ | 8 | 7 | P16-N post-handoff |
| 71 | Share link from broker to customer | Intercom | S | ★★★★☆ | 9 | 8 | Trial onboarding |
| 72 | Customer never sees broker jargon | All | S | ★★★★★ | 10 | 9 | lifecycle tags hidden |

---

## Category F — Trial, Trust & Commercial (73–85)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 73 | Day 0 supervised trial | HubSpot onboarding | S | ★★★★★ | 10 | 10 | Process not code |
| 74 | Observation log per case | Zendesk QA | S | ★★★★★ | 10 | 10 | Cap 6 broken |
| 75 | Time-saved counter (manual log) | Business case | S | ★★★★☆ | 9 | 9 | Testimonial fuel |
| 76 | 5 scenario validation gate | Stripe testing | S | ★★★★★ | 10 | 10 | guardrail exists |
| 77 | Single trial URL no SSO | All | S | ★★★★★ | 10 | 10 | FP-004 |
| 78 | Manual invoice + Zelle | Pilot scope | S | ★★★★★ | 10 | 10 | No Stripe |
| 79 | Testimonial at Day 7 | HubSpot | S | ★★★★☆ | 10 | 10 | Success metric |
| 80 | "Copy to WeChat" as demo moment | Intercom | S | ★★★★★ | 10 | 10 | 15-min script |
| 81 | Chinese-only trial surface | Localization | S | ★★★★★ | 10 | 10 | F-005 fix |
| 82 | Founder E2E log before broker | QA | S | ★★★★☆ | 9 | 9 | P16-W |
| 83 | P16-Y battery ≥88 in CI | Salesforce QA | S | ★★★★☆ | 8 | 10 | Quality gate |
| 84 | One-pager broker PDF | HubSpot | S | ★★★★☆ | 9 | 9 | Commercial pack exists |
| 85 | Kill switch / product_only discipline | Enterprise | S | ★★★★☆ | 8 | 8 | Scope guard |

---

## Category G — Quality, Automation & Founder Control (86–100)

| # | Idea | Source | Diff | ROI | Chen Kui | Insurance | Impact |
|---|------|--------|------|-----|----------|-----------|--------|
| 86 | guardrail_inbox_triage.sh as release gate | Stripe CI | S | ★★★★★ | 8 | 10 | Exists |
| 87 | trial_launch_check.sh single entry | Linear ops | S | ★★★★★ | 9 | 10 | Exists |
| 88 | Failure pattern library | SRE | S | ★★★★☆ | 8 | 9 | FP-004 etc |
| 89 | Scenario replay for rehearsal | Linear Agent test | S | ★★★☆☆ | 7 | 8 | ScenarioReplayTab |
| 90 | Role simulation before live | Salesforce sandbox | S | ★★★☆☆ | 7 | 8 | Exists |
| 91 | Health check runner | Datadog | S | ★★★★☆ | 8 | 9 | P16-T |
| 92 | Deploy parity local = Cloud Run | Stripe | S | ★★★★☆ | 8 | 9 | pilot profile |
| 93 | Postgres-only prod truth | Salesforce | S | ★★★★☆ | 7 | 8 | CURRENT_PRODUCT_SHAPE |
| 94 | Rubric-scored case quality | QA frameworks | S | ★★★★★ | 8 | 10 | P16-Y |
| 95 | Blocklist generic broker_next_step | Content QA | S | ★★★★★ | 10 | 10 | Template fix |
| 96 | Constitution enforcement | Governance | S | ★★★★☆ | 8 | 8 | No P17 |
| 97 | Operator ignore list | Cognitive load | S | ★★★☆☆ | 7 | 7 | 197 scripts |
| 98 | Preview protection audit | Security | S | ★★★★☆ | 8 | 8 | FP-004 |
| 99 | Andy 2-min simulation gate | UX research | S | ★★★★☆ | 10 | 10 | P16-X Chen Kui |
| 100 | Sell outcomes not seats | Zendesk 2026 | S | ★★★★★ | 10 | 10 | "Cases ready to act" |

---

## Top 10 by composite score (ROI × Chen Kui × Insurance / effort)

| Rank | # | Idea | Why |
|------|---|------|-----|
| 1 | 2 | Paste → structured case | Already built; deploy it |
| 2 | 32 | Copy-to-WeChat primary | Only feature that beats「直接回微信」 |
| 3 | 16 | Append to existing case | Backend done; teach UX |
| 4 | 17 | Post-copy append CTA | Fixes continuity 41→70+ |
| 5 | 31 | One-sentence broker_next_step | Unlocks Office Actionability |
| 6 | 10 | Append summary merge | P16-Y P0 engine fix |
| 7 | 77 | Trial URL no SSO | FP-004 blocks everything |
| 8 | 46 | Evidence packet (cancel notice) | Stripe pattern for insurance |
| 9 | 1 | Message-first intake | Customer friction killer |
| 10 | 100 | Sell outcomes not seats | Positioning for invoice |

---

*End of P16-Z2 Phase 6 — Top 100 Ideas Worth Copying*
