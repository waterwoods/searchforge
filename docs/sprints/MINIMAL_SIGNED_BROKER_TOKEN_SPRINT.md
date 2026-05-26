# Minimal Signed Broker Token Sprint — SSOT

**Authority:** This file is the single source of truth for this sprint.  
**Not building:** enterprise IAM, SSO, OAuth platform, Cognito/Auth0 migration, RBAC UI, fake multi-tenant theater.  
**Building:** minimal **system-issued** HMAC broker token — honest, versioned, observable — layered on existing Unified Intake posture.

---

## Phase 0 — Git + inventory + coexistence

### 0.1 Git snapshot (recorded at sprint execution)

| Item | Value |
|------|--------|
| **Branch** | `sprint/scoped-broker-identity-office-operational-safety` |
| **Dirty tree** | Yes — many modified tracked files + numerous untracked `docs/sprints/*`, `results/*`, and other paths coexist on the working tree; **merge isolation risk** until staged intentionally. |
| **Stashes** | Multiple (`stash@{0}` … `stash@{15}+`) — recovery confusion if wrong stash popped during pilot ops. |
| **Coexistence risks** | Parallel sprint docs + WIP on inbox routes/tests/UI can collide with token middleware ordering; support manifest version bump (`support_export_v4`) affects external parsers; schema epoch string changed — replay tooling must tolerate drift. |

### 0.2 Inventory — current reality (honest)

| Area | Reality |
|------|---------|
| **Intake perimeter** | Optional `UNIFIED_INTAKE_INTAKE_API_KEY`; when unset, `/api/inbox/*` (except `/support/*`, WeChat callback) is **anonymous**. |
| **Support perimeter** | Optional `UNIFIED_INTAKE_SUPPORT_API_KEY`; when unset, `/api/inbox/support/*` is **anonymous** — reconnaissance risk on public URLs. |
| **Office ownership** | Hint from `X-Org-Id` → `client_asserted_org_id`; optional `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP` compares header to persisted `asserted_org_id` — **not** cryptography. |
| **Token scope registry** | `token_scope_posture.py` — env-listed expected office slugs + deploy broker label; **operator checklist**, not caller proof. |
| **Analytics scope** | Dashboard filters funnel metadata by client-asserted org — **spoofable** if intake URL is reachable without perimeter. |
| **Replay lineage** | `replay_lineage` + manifest embed schema epoch, manifest version, office posture — **operational handoff**, not legal WORM. |
| **Deployment truth** | `deployment_identity_truth()` — best-effort env labels (`K_*`, `GIT_SHA`, …) — **not tamper-evident**. |
| **Request lineage** | `request_trace_id` from middleware — correlation only. |
| **Support export posture** | Manifest exposes auth + intake perimeter JSON + tenant truth (`tenant_id_authoritative` **always null** today). |
| **Org continuity** | Persisted org hints on cases/sessions; **no** authoritative tenant issuance layer before this sprint’s token sketch. |
| **Rate limit** | `TriagePostRateLimitMiddleware` — per-IP sliding window on `POST /api/inbox/triage` only; **NAT collapse**, spoofable `X-Forwarded-For` if proxy misconfigured. |

---

## Phase 1 — Deep discovery — TOP_30 lists

### TOP_30_BROKER_IDENTITY_ILLUSIONS

1. “`X-Org-Id` is the tenant.”  
2. “Intake API key = broker login.”  
3. “One intake key implies one broker.”  
4. “Office enforcement = crypto boundary.”  
5. “Persisted `asserted_org_id` proves the HTTP caller.”  
6. “Support key + case_id = authorized human.”  
7. “Bearer header means OAuth.”  
8. “Anonymous demo mode is ‘safe enough’ on the public internet.”  
9. “JWT mention in roadmap implies JWT exists today.”  
10. “Multi-office UI tabs cannot cross-contaminate cases.”  
11. “Session stickiness replaces IAM.”  
12. “Email/thread id is a tenant root.”  
13. “LLM output is broker-branded therefore broker-bound.”  
14. “Analytics office slice is billing-grade.”  
15. “Workbench URL secrecy equals authz.”  
16. “Cloud Run IAM replaces app tenancy.”  
17. “HTTPS prevents confused deputy.”  
18. “Long random case_ids are unguessable forever.”  
19. “Operator scripts always send `X-Org-Id`.”  
20. “Staging data cannot leak into pilot narratives.”  
21. “Customer-visible copy proves office isolation.”  
22. “Redis/Qdrant boundaries imply PG isolation.”  
23. “Feature flags are security boundaries.”  
24. “‘Product-only mode’ removes all abuse surfaces.”  
25. “Embed iframe origin lock fixes forged headers.”  
26. “Mobile browser profiles cannot reuse intake keys.”  
27. “Broker employees share one identity anyway.”  
28. “Pen-test someday equals posture today.”  
29. “SOC2 language in slides equals controls in code.”  
30. “This sprint’s HMAC token **is** tenant authority.” (**Still false** — shared deployment secret; see Phase 2.)

### TOP_30_SUPPORT_CONFUSIONS

1. Intake vs support key purpose swap.  
2. Assuming manifest `git.commit` matches running revision without cross-check.  
3. Treating `tenant_truth.client_asserted_org_id` as proof in tickets.  
4. Interpreting `office_ownership.enabled` as “hack-proof.”  
5. Confusing schema epoch with Alembic migration id.  
6. Expecting case-head to redact operator mistakes.  
7. Believing replay lineage is admissible evidence.  
8. Pasting support key into Zendesk.  
9. Using deployment-manifest as customer-facing SLA proof.  
10. Thinking `429` means ‘blocked attacker’ vs shared NAT.  
11. Confusing `X-Unified-Intake-Office-Expectation` with enforcement.  
12. Assuming anonymous support routes mean “internal only.”  
13. Expecting token registry slugs to match broker billing IDs.  
14. Reading `demo_mode=true` as non-production when DNS is public.  
15. Treating funnel analytics as finance-grade revenue attribution.  
16. Mixing pilot broker labels with legal entity names.  
17. Opening case_id from screenshot without office header context.  
18. Assuming English-only operator docs match broker staff literacy.  
19. Thinking founder-held secrets scale to L2 team.  
20. Confusing LLM latency with outage.  
21. Expecting case lifecycle JSON to explain human workflow.  
22. Treating health `phase` as incident verdict.  
23. Using `/ready` semantics for intake-only pilots incorrectly.  
24. Assuming gzip logs contain redacted secrets (they might not).  
25. Believing “role C replay” is customer replay.  
26. Export scripts skipping `X-Org-Id` then blaming product.  
27. Thinking office mismatch hint is automatic escalation.  
28. Parsing manifest without tolerating new keys.  
29. Expecting token trace ids to exist without header configured.  
30. Confusing **verified broker token** with **user authentication**.

### TOP_30_DEPLOYMENT_DRIFT_RISKS

1. Forgetting to set intake key in prod-shaped env.  
2. Support key committed to `.env` in screenshots.  
3. Duplicate intake/support identical secret.  
4. `ENV=prod` + `DEMO_MODE=1` contradiction silent until health read.  
5. Rolling Cloud Run revision without bumping deploy binding labels.  
6. Multiple replicas + in-memory sessions enabled.  
7. Office enforcement on without durable DB URL.  
8. Proxy stripping `X-Org-Id`.  
9. Proxy forging `X-Forwarded-For`.  
10. Stale frontend bundle hitting new API epoch.  
11. Cached deployment-manifest JSON in Notion.  
12. Operator runs local script against prod URL.  
13. Wrong Qdrant collection env on non-intake path in full profile.  
14. Feature branches deploying without `GIT_SHA` injection.  
15. Trial readiness PASS with Node mismatch hiding UI build failures on dev laptops.  
16. `.env.cloudrun` partial load vs `.env` precedence confusion.  
17. Secret Manager binding drift between regions.  
18. Autoscaling cold start + rate limit surprises.  
19. Logging sink retention shorter than incident window.  
20. Blue/green traffic split reading different PG migration states.  
21. Manual SQL patching without epoch bump discipline.  
22. Forked demo data paths on NFS-ish mounts.  
23. Time skew across VMs breaks token TTL intuition.  
24. Locale/timezone skew in analytics dashboards.  
25. CDN caching GET routes that should be dynamic (if ever exposed).  
26. Accidentally mounting debug routers in product-only=false chaos.  
27. CI green while production `.env` missing new vars.  
28. Helm chart defaults diverging from demo.env.example.  
29. Windows/WSL path issues breaking smoke scripts.  
30. **New:** broker HMAC secret rotated without rotating issued embed tokens → legitimate offices hard-down until re-issue.

### TOP_30_ABUSE_PATHS

1. Drive-by `POST /triage` when intake key unset.  
2. LLM cost pumping via anonymous triage.  
3. Case id enumeration on open support routes.  
4. Manifest scraping for stack fingerprinting.  
5. Spoofed `X-Org-Id` polluting analytics.  
6. Shared NAT IP hitting rate limit → denial for benign offices.  
7. Replay of captured intake key from Slack.  
8. Replay of captured support key from Slack.  
9. Browser devtools copying embed config with secrets.  
10. Contractor laptop theft with `.env`.  
11. Customer forwarding workbench link with session-ish params.  
12. Automated fuzz on append endpoints.  
13. Image-heavy payloads if surfaces allow uploads adjacent.  
14. Webhook endpoints mistaken as secret URLs.  
15. Logging middleware leaking querystrings with tokens (discipline issue).  
16. Third-party analytics scripts in embed parent page.  
17. Misconfigured CORS + credentialed misuse attempts.  
18. Ops runs `curl` tutorials with real keys in shell history.  
19. Zombie cron jobs hammering triage.  
20. Competitor benchmarking latency anonymously.  
21. Prompt injection influencing broker-visible outcomes (orthogonal but real).  
22. Email gateways scanning URLs triggering GET side effects (if any).  
23. SSRF via misconstructed callbacks (future surfaces).  
24. Dependency confusion installing fake wheels on ops laptops.  
25. Fake “support” social engineering with manifest jargon.  
26. Multi-tab office mismatch confusing staff into pasting wrong data — **human abuse of trust**.  
27. Shared intake key across franchise brokers — cross-brand data bleed.  
28. Token stolen from proxy logs.  
29. **Forged org** still works wherever enforcement off or legacy rows.  
30. **Leaked HMAC broker token** behaves like leaked intake key for token TTL window — still **not** user-level revocation.

### TOP_30_FAKE_TENANCY_PATTERNS

1. Header-only org separation.  
2. “Office slug expectation” labeled as security.  
3. Calling PG rows “tenant-isolated” without RLS.  
4. Branding switch == tenancy switch.  
5. Analytics filters presented as entitlements.  
6. Case list filtered ⇒ cryptographically isolated.  
7. Session id as tenant root.  
8. Marketing “multi-tenant SaaS” language vs deployment reality.  
9. Single Cloud Run service pretending per-broker isolation.  
10. Slack channel per broker mistaken for IAM partition.  
11. Dashboard hostname per broker without separate secrets.  
12. ENV files per broker stored in same password manager folder.  
13. DEMO_MODE semantics treated as legal isolation.  
14. Manifest `tenant_id_authoritative: null` explained away as bug.  
15. Operator assertions in tickets treated as ground truth.  
16. “We’ll add SSO later” handwave on current data plane.  
17. Spreadsheet roster == ACL.  
18. Naming collision on office slugs across pilots.  
19. Forklift JSON cases between pilots “temporarily.”  
20. Using broker logos as access control.  
21. Thinking UUIDs partition data models.  
22. Assuming append routes inherit office enforcement uniformly everywhere.  
23. Treating founder manual processes as durable guardrails.  
24. Presenting role-C simulation as customer truth.  
25. Hidden admin URLs as security through obscurity.  
26. Docs referencing future JWT as if shipped.  
27. Mixing Chinese/English operator docs without access tiers (communication fake hierarchy).  
28. Calling embed iframe same-origin policy “tenant boundary.”  
29. PG JSON blobs interpreted as authoritative policy stores.  
30. **Signed broker token** without per-broker secret rotation strategy — still **one HMAC key per deployment**.

### TOP_30_OPERATIONAL_FAILURES

1. On-call cannot tell which revision answered a ticket.  
2. Cannot correlate LLM spike to a single office.  
3. Cannot revoke a leaked intake key without downtime feels.  
4. Founder-only secret distribution on WhatsApp.  
5. No runbook for office slug rename.  
6. Case visibly wrong office — support cannot explain mechanism.  
7. Manifest pasted partially — missing epoch context.  
8. Two brokers share browser — cases bind wrong.  
9. Enforcement flip mid-pilot without comms.  
10. DB restored from backup — epoch mismatch unexplained.  
11. Rate limit storms during carrier promo day.  
12. Observability shows 200s while UX broken due to client bugs.  
13. Support mistakes triage latency for coverage outage.  
14. Ops assumes health green means LLM healthy when OPENAI degraded.  
15. Missing `X-Org-Id` script creates invisible legacy cases.  
16. Pilot ends — keys rot — nobody owns rotation calendar.  
17. Documentation sprawl — nobody finds SSOT.  
18. CI PASS psychology suppresses manual smoke on prod.  
19. Trial readiness UI build OK hides broken laptop vite path (Node pin drift).  
20. Multi-agent edits overwrite `.env.example` guidance.  
21. Escalation to engineer for every office mismatch.  
22. Customer success promises analytics slice execs cannot reproduce.  
23. Embeds in email clients strip headers.  
24. Mobile Safari tab discard loses context staff blame on API.  
25. Language barrier turns enforcement errors into “racism toward our office.”  
26. Night deployment without dual-control.  
27. Rollback plan undocumented for new middleware.  
28. Metrics cardinality explosion from high-cardinality org labels in logs.  
29. **New:** Issued broker tokens living in sticky notes — same class failure as API keys.  
30. **New:** Token/office/header mismatch tickets without playbooks.

### TOP_30_SCALING_FAILURES

1. Single shared intake key across 30 offices.  
2. Per-IP rate limit unfair at carrier-sized NAT.  
3. Support queue linear with case volume — no triage bot boundaries.  
4. Founder approval bottleneck on every new office slug.  
5. Manifest size grows — parsers snap.  
6. PG hot rows for global case counters.  
7. Analytics in-memory buffers lose events across replicas.  
8. Session stores inconsistent across instances without sticky sessions.  
9. Operator training cannot keep pace with feature velocity.  
10. Translation/cultural variants multiply copy-testing cost.  
11. Secrets rotation N× offices without automation ⇒ fatigue ⇒ shortcuts.  
12. Increasing LLM spend without per-broker budgets.  
13. Compliance questionnaires expose architecture lies — deals stall.  
14. Enterprise procurement expects SSO — timeline collision.  
15. Data residency questions unanswered.  
16. Multi-region latency without edge strategy.  
17. Backup/restore drills never practiced.  
18. Feature flags proliferate — matrix untestable.  
19. Debt from “temporary” JSON paths becomes permanent.  
20. Incident retros skipped due to pilot chaos.  
21. Vendor lock-in on LLM without failover storytelling fails sales.  
22. Observability bills spike before revenue.  
23. Ticket systems don’t map `request_trace_id` automatically.  
24. Too many honesty warnings operators mute them all.  
25. Role ambiguity between AE vs CS vs engineer on intake bugs.  
26. Org chart churn breaks escalation paths.  
27. Knowledge leaves when contractor exits — docs stale immediately.  
28. Automated tests green while prod configuration diverges (classic).  
29. **At 100 offices:** forged/fumbled `X-Org-Id` dominates support minutes unless enforced + disciplined clients **and** stronger issuance story.  
30. **At enterprise sales:** legal asks “who authenticated?” — answer still awkward without IdP,mTLS, or per-broker credentials beyond shared secrets.

### TOP_30_FOUNDER_DEPENDENCIES

1. Holds prod secrets in personal vaults.  
2. Only one who reads deployment-manifest correctly.  
3. Only one who interprets schema epoch changes.  
4. Final word on enforcement flags.  
5. Executes manual SQL when PG diverges.  
6. Personally DM’d when rate limits strike.  
7. Codes middle-of-night hotfixes without PR discipline under pressure.  
8. Owns Cloud Run console access lacking least-privilege teammates.  
9. Translates broker complaints into engineering tasks personally.  
10. Runs demo scripts from laptop env inconsistent with prod.  
11. Cognitive load carrying fake-vs-real narrative alone.  
12. Bridges LLM vendor billing anomalies.  
13. Approves marketing claims touching security posture.  
14. Single approver for `.env.cloudrun` edits.  
15. Knows which pilots actually enabled keys vs lying “we’re secure.”  
16. Personally rotates keys because calendar lacks owner.  
17. Owns relationship with first pilot champion — bus factor on trust.  
18. Explains why tenant authoritative null is intentional — repeatedly.  
19. Without him, support defaults to blaming product engineering blindly.  
20. Holds historical memory why legacy rows lack org stamps.  
21. Only one monitoring cost dashboards weekly.  
22. Performs incident comms because no comms owner hired.  
23. Negotiates pilot contracts referencing features not frozen.  
24. Temporary toggles become permanent because only they remember rollback steps.  
25. Acts as human firewall against scope creep into SSO/IAM too early.  
26. Reviews sprint docs others generate — bottleneck.  
27. Personally verifies regression latency thresholds.  
28. Knows which brokers actually pay vs tire-kickers — skews prioritization quietly.  
29. Decides when honesty docs scare vs help sales — tension unresolved structurally.  
30. **New:** Issues first-generation broker tokens manually until automation exists.

---

## Phase 2 — Design convergence (minimal signed broker token)

### Answers

1. **What is a broker token?** Short-lived HMAC-signed payload (`minimal_signed_broker_token_v1`) proving possession of deployment **shared** `UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET` at issuance time — **not** a user login.  
2. **What office is it tied to?** Optional claim `office_slug`; compared honestly to `X-Org-Id` → labeled match/mismatch — **does not** authorize PG rows alone.  
3. **What deployment is it tied to?** `deploy_binding` claim verified against `UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING` or derived commit/env label — prevents casual token reuse across accidental deploy mixes (**best-effort**).  
4. **Rotation?** Rotate HMAC secret + re-issue tokens; bump binding label when infra meaningfully changes.  
5. **Revocation?** No CRL — wait `exp` or rotate secret (honest).  
6. **Tracing?** Payload `jti` exposed as `token_trace_id` in `minimal_broker_token_request` JSON + `request_trace_id` separately.  
7. **Honest vs fake?** Honest: signature valid, binding matches, not expired. Fake: forged header org; spoofed IP; stolen shared secret; “verified token” still **not** `tenant_id_authoritative`.  
8. **Support infers?** Whether a request carried a verifiable token; mismatch between token office vs header; manifest includes static posture.  
9. **Replay infers?** `replay_lineage.minimal_broker_token_posture` documents model + binding semantics alongside epoch/manifest version.  
10. **Abuse protection improves?** Slightly raises cost of **pure header forgery** when pilots adopt tokens **and** keep secrets out of browsers — marginal vs leaked HMAC.

---

## Phase 3 — Implementation (small foundations)

| Item | Location |
|------|----------|
| Token issue/verify + posture + request truth | `services/fiqa_api/security/minimal_signed_broker_token.py` |
| Middleware (optional header; after `X-Org-Id` capture) | `MinimalBrokerTokenMiddleware` registered in `services/fiqa_api/app_main.py` |
| Manifest + case-head request fields | `services/fiqa_api/routes/inbox_triage.py` — `minimal_broker_token_posture`, `minimal_broker_token_request`; `replay_lineage` extended; `SUPPORT_EXPORT_MANIFEST_VERSION = support_export_v4` |
| Intake perimeter JSON | `services/fiqa_api/security/intake_api_gate.py` → `minimal_signed_broker_token` |
| Health deployment profile | `services/fiqa_api/app_main.py` → `minimal_broker_token` |
| Operator warnings | `services/fiqa_api/deployment_profile.py` — short secret + prod-like unbound binding |
| Schema epoch label | `deployment_profile.INTAKE_SCHEMA_EPOCH` → `2026-05-11_minimal_signed_broker_token_v1` |
| Issuer CLI | `scripts/issue_minimal_broker_token.py` |
| Tests | `tests/test_minimal_signed_broker_token.py` (+ manifest/health assertions updated) |
| Env documentation | `configs/demo.env.example` |

**Explicit non-goals shipped:** No users table; no login UI; no OAuth; no RBAC; `tenant_id_authoritative` remains **`None`**.

---

## Phase 4 — Multi-round testing + tabletop

### Automated (executed)

| Check | Result |
|-------|--------|
| `python3 -m compileall` (targets) | PASS |
| Full `pytest` | PASS (1 skipped overall suite) |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `bash scripts/trial_readiness_check.sh` | PASS |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS (`http_p95_ms` ≈ 4014 < 6000) |
| `cd ui && npx --yes madge --circular --extensions ts,tsx src` | PASS (no cycles) |
| `cd ui && npm run build` | **FAIL on this runner** — Node `20.18.2`; Vite requires `20.19+` or `22.12+` (`ERR_REQUIRE_ESM` loading vite config). **Environmental truth:** use Node 22.12+ on PATH (trial readiness previously masked dev variance). |
| `PYTHONPATH=. python3 scripts/support_deployment_manifest_smoke.py` | Not re-run against live server in this session (no server); script remains valid for optional smoke. |

### Tabletop simulations (expected outcomes)

| Scenario | What improves | What stays fake / breaks |
|----------|---------------|---------------------------|
| Leaked token | Trace via `jti`; TTL bounds exposure window | Shared secret compromise ⇒ forge until rotation |
| Wrong office token | `office_claim_vs_x_org_id=mismatch_v1` surfaces | Enforcing fix requires product policy (still not auto-403 here) |
| Revoked token | After secret rotation, signature fails | No instant per-token revoke |
| Stale token | Expired rejected | Ops confusion if clocks skew — mitigated by skew env |
| Copied token | Replays until expiry | Same as any bearer secret |
| Support confusion | Manifest explains semantics | Humans still mis-read headers vs tokens |
| Replay ambiguity | Epoch + manifest version + posture carried | Not legal-grade replay |
| Wrong deployment | Binding mismatch → invalid | Binding derived `unbound_v1` warns in prod-like |
| Missing org | Token may carry office; header absent flagged | Legacy unstamped cases unchanged |
| Forged org | Header still spoofable without perimeter | Token optional — doesn’t cure open intake |
| NAT abuse | Rate limit still blind to actors | Same as before |
| Support escalation | Clearer fields for tickets | Founder still needed for judgment |
| Noisy broker | Analytics still noisy if keys leak | Financial caps still absent |
| Token rotation failure | Operators see verification failures | Needs comms playbook |

### Scale honesty

- **30 offices:** shared secrets + header discipline stress; support volume from mismatch tickets rises without L1 runbooks.  
- **100 offices:** shared HMAC per deployment without per-office secrets becomes **credibility** and **blast-radius** problem — not solved here.  
- **Enterprise sales:** procurement will ask for SSO/MFA/audit — **this sprint explicitly does not answer**.

---

## Phase 5 — `SELF_CRITIQUE_REPORT_V11`

1. **Fake security feeling:** “Signed token” language invites mental JWT/IAM equivalence — mitigated only by docs + `tenant_id_authoritative_remains_null`, easily ignored under stress.  
2. **Weak assumption:** Pilots will keep HMAC out of browser bundles — marketing may still embed dangerously.  
3. **Hidden replay gap:** Token does not bind `case_id` or `session_id` — replay across contexts still meaningless cryptographically.  
4. **Support illusion:** Operators may treat `verified: true` as “customer authenticated.”  
5. **Operational lie by omission:** No issuance audit log table — only ephemeral observability if logs chosen.  
6. **Token weakness:** Single symmetric key ⇒ insider = god.  
7. **Scaling cliff:** Rotation without orchestration bricks embeds until humans update.  
8. **Founder bottleneck:** Manual `issue_minimal_broker_token.py` usage doesn’t scale.  
9. **Deployment confusion:** `unbound_v1` binding still verifies tokens — honesty warning only.  
10. **Office confusion:** Mismatch flag without automated remediation ⇒ ticket noise.  
11. **Abuse:** Open intake perimeter defeats token benefits entirely.  
12. **NAT / rate limit:** Unchanged structural blindness.  
13. **Compliance:** No claims; nonetheless outsiders may misquote sprint language.  
14. **Middleware ordering:** Future edits could break “after `X-Org-Id`” invariant.  
15. **Algorithm agility:** v1 hard-codes HMAC-SHA256 payload format — future versions need migration discipline.  
16. **Clock skew:** Large skew env could widen abuse window.  
17. **Manifest drift:** Parsers ignoring new keys lose observability wins.  
18. **Git hygiene:** Dirty tree + many untracked sprint docs ⇒ merge/review risk unrelated to token code.  
19. **Node pin drift:** UI build failure on older Node — operational hazard for demos.  
20. **No binding to analytics sink:** Token trace id not automatically propagated to funnel rows in this sprint — correlation gap remains unless wired later.

---

## Phase 6 — Convergence

- **More real:** Optional verifiable broker envelope; deploy binding pin; support manifest + replay lineage carry token posture; operator warnings for weak/unbound secrets; explicit request truth JSON; issuer script; tests.  
- **Still fake:** True multi-tenant isolation; user authentication; authoritative tenant id; per-broker crypto credentials at scale; CRL; enterprise IAM promises.  
- **Biggest broker truths:** Today’s broker identity is mostly **asserted labels + shared secrets**; enforcement is **opt-in** and **hint-based**.  
- **Biggest office truths:** Office is a **slug discipline problem** before it is a crypto problem.  
- **Biggest support truths:** Keys differ; manifest versions drift; headers lie; tokens **reduce** some ambiguity **if** adopted.  
- **Biggest replay truths:** Operational metadata only — not legal chains of custody.  
- **Biggest deployment truths:** Labels are best-effort; Node/toolchain drift breaks builds silently on some laptops.  
- **Biggest abuse truths:** Anonymous intake is the largest hole; tokens are patch, not seal.  
- **Biggest remaining risks:** Secret leakage; shared blast radius; founder operational dependence; enterprise expectation mismatch.  
- **What breaks at 30 offices:** Secret rotation comms; header/token mismatch tickets; NAT rate limits.  
- **What breaks at 100 offices:** Symmetric per-deploy keys without automation; support parsing entropy; analytics trust.  
- **What breaks at enterprise sales:** IAM / audit / data residency expectations vs actual posture.  
- **Best next 10x leverage:** Per-office **asymmetric** or **per-office issued secrets** + automated rotation **without** full SSO — still “minimal,” bigger lift.  
- **Best next sprint:** Wire **optional** propagation of `token_trace_id` / verified office into analytics metadata + structured logs only (still honest ABOut spoofability).  
- **Best next 3-month roadmap:** (1) Issuance service + audit log sink, (2) per-pilot key separation, (3) prod intake/support keys mandatory checklist, (4) IdP only if revenue forces — **not** before operational discipline wins.  
- **What should NOT be built yet:** Full OAuth/OIDC, users table RBAC UI, enterprise billing isolation theater, JWT platform, Cognito migration.

---

## Phase 7 — Validation record (commands)

```
python3 -m compileall -q services/fiqa_api/security/minimal_signed_broker_token.py …
PYTHONPATH=. python3 -m pytest -q   # PASS
bash scripts/guardrail_inbox_triage.sh   # PASS
bash scripts/trial_readiness_check.sh   # PASS
PYTHONPATH=. python3 scripts/run_full_regression.py   # PASS
cd ui && npx --yes madge --circular --extensions ts,tsx src   # PASS
cd ui && npm run build   # FAIL — Node 20.18.2 below Vite requirement; upgrade to Node 20.19+ or 22.12+
```

---

## Phase 8 — Sprint completion snapshot (see chat “FINAL OUTPUT” for duplicate summary)

**FINAL_ONE_LINE:** *Shipped honest HMAC broker-token plumbing (optional header, binding, manifest/replay truth, issuer script, tests) while keeping `tenant_id_authoritative` null and refusing enterprise IAM theater.*
