# BINDING + SESSION CONTINUITY PER OFFICE — Sprint SSOT

**Branch:** `sprint/binding-session-continuity-per-office`  
**Date:** 2026-05-09  
**Rule:** Honest office-aware continuity — not enterprise IAM, not fake tenancy.

---

## Phase 0 — Inventory (snapshot)

### Modified tracked files (workspace at sprint execution)

Included upstream edits beyond this sprint closure (broker/office/auth sprint lineage): `configs/demo.env.example`, `scripts/trial_readiness_check.sh`, `services/fiqa_api/app_main.py`, `services/fiqa_api/db/schema/stage1_service_record.sql`, `services/fiqa_api/db/service_record_repository.py`, multiple inbox triage modules, `routes/inbox_triage.py`, UI intake API/types, tests under `tests/`, etc.

### Untracked paths (not all sprint-owned)

Many `docs/sprints/*.md`, `results/*.json`, optional scripts — treat as local/editorial unless promoted.

### Sprint-owned implementation touch (this closure)

| Area | Files |
|------|--------|
| Office-scoped binding stubs (PG) | `services/fiqa_api/db/service_record_repository.py` — `list_binding_stub_rows_office_scoped` |
| Binding list facade | `services/fiqa_api/inbox_triage/case_truth_repository.py` — `list_recent_cases_for_binding(..., client_asserted_org_id=)` |
| Session trim + org hint | `services/fiqa_api/inbox_triage/session_store.py` — `save_session_binding_after_case_created(..., asserted_org_id=)` |
| Route continuity | `services/fiqa_api/routes/inbox_triage.py` — org-shift clear, wrong-office active_case clear, wired binding list + persist |
| Replay posture keys | `services/fiqa_api/security/case_office_access.py` — `office_ownership_posture_dict` additions |
| Tests | `tests/test_case_truth_repository.py`, `tests/test_intake_session_persistence.py` |

### Binding logic (locations)

- **`services/fiqa_api/inbox_triage/case_binding.py`** — `resolve_active_case`, `is_case_open_for_binding`
- **`services/fiqa_api/inbox_triage/case_truth_repository.py`** — stub reads + binding candidate list
- **`services/fiqa_api/routes/inbox_triage.py`** — ties session `active_case_id`, explicit `case_id`, `list_recent_cases_for_binding`, `assert_case_office_access_allowed`

### Session restore / persistence

- **`services/fiqa_api/inbox_triage/session_store.py`** — save/view/patch/get
- **`services/fiqa_api/inbox_triage/session_repository.py`** — Postgres/in-memory payload JSON

### Active-case selection

- Session `active_case_id` wins first in `resolve_active_case`
- Route validates stub open + **now** office hint vs `X-Org-Id` before trusting sticky binding
- Vehicle match / single-open-case scan uses **office-filtered** recent stub list when org asserted

### Append routing

- **`append_follow_up_message`** in `case_store.py`; guard **`assert_case_office_access_allowed`** on append route
- Append boundary clears session binding on hard new-issue paths (existing)

### Replay lineage / support

- **`_support_replay_lineage_dict`** / **`support/deployment-manifest`** / **`support/case-head`** in `routes/inbox_triage.py`
- **`office_ownership_posture_dict`** documents binding scope + session trim semantics

### Office enforcement flow

- **`services/fiqa_api/security/case_office_access.py`**
- List: **`list_cases_for_office_enforcement_read`** when enforcement env on

### Workbench list flow

- **`list_recent_cases_for_read`** vs **`list_cases_for_office_enforcement_read`**

### Analytics ownership continuity

- **`_schedule_route_analytics`** / **`track_event`** receive `org_id` from route when present

---

## Phase 2 — Discovery maps

### OFFICE_BINDING_FLOW_MAP

1. Client sends `X-Org-Id` → `IntakeClientAssertionMiddleware` → `request.state.client_asserted_org_id`
2. POST `/api/inbox/triage` passes `org_id` into `triage_inbox`
3. **Session org shift:** persisted session `asserted_org_id` ≠ request org → clear `active_case_id`
4. **Sticky active case:** load triage stub; if closed/archived **or** case `asserted_org_id` ≠ request org (both set) → clear binding
5. **Candidate pool:** `list_recent_cases_for_binding(..., client_asserted_org_id=org_id)` applies `case_visible_in_office_list` (JSON) or PG `_PG_OFFICE_LIST_FILTER` (scoped query)
6. **`resolve_active_case`** prioritizes session id → vehicle uniqueness → single open row (within filtered pool)
7. **`assert_case_office_access_allowed`** when loading `existing_case` (enforcement + stamped case)

### SESSION_CONTINUITY_TRUTH_MAP

| Layer | Source of truth | Office field |
|-------|-----------------|--------------|
| HTTP request | `X-Org-Id` assertion | `client_asserted_org_id` |
| Persisted case | `asserted_org_id` / PG `office_owner_org_id` mirror | ownership hint |
| Session row | `asserted_org_id` in JSON payload | continuity hint |
| Enforcement | env `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP` | optional hard boundary |

**Gap closed this sprint:** post-`save_case` trim via `save_session_binding_after_case_created` **retains** `asserted_org_id` (param + prior row fallback).

### ACTIVE_CASE_SELECTION_MAP

| Input | Behavior |
|-------|----------|
| `request.case_id` | Explicit; stub load; office assert |
| `session.active_case_id` | Fast path if stub open **and** office hint compatible with request org |
| Vehicle match | Among **office-visible** open stubs |
| Exactly one open | Among **office-visible** open stubs |

### APPEND_ROUTING_TRUTH_MAP

- Route: `POST /cases/{case_id}/append-message` → `get_case_for_read` → **`assert_case_office_access_allowed`**
- Triage: `triage_for_append` + boundary responses; may `patch_session_case_binding(clear_active_case=True)`
- **Cross-office append** without enforcement: still blocked when case stamped and org header mismatched **if** enforcement on; otherwise relies on correct `case_id` + honest UI

### SUPPORT_REPLAY_CONTINUITY_MAP

- Deployment manifest includes `office_ownership` dict with **`binding_candidates_when_x_org_id_present`** and **`session_trim_preserves_asserted_org_id`**
- `support/case-head/{case_id}` exposes `asserted_org_id` on case metadata (no message bodies)
- **Honesty:** support export is not WORM/legal hold; org is client-asserted semantics

---

## TOP_30_CROSS_OFFICE_BINDING_FAILURES (risk catalog)

1. No `X-Org-Id` on triage while multi-office shared browser profile  
2. Legacy unstamped cases visible to all offices when strict legacy off  
3. Same VIN in two offices → ambiguous match (returns `None`)  
4. Session copied between environments with different org headers  
5. Mobile deep link omits org header  
6. Proxy strips `X-Org-Id`  
7. Typo org id → silent empty candidate pool  
8. Org id case sensitivity mismatch across clients  
9. Binding uses stub; full case read later fails hydration gap  
10. JSON fallback after PG error serves unstamped stale rows  
11. Dual-write drift between JSON and PG ownership columns  
12. `office_owner_org_id` not backfilled for old rows  
13. Founder SQL inspect without org filter misreads queue  
14. Single-open-case auto-bind picks legacy orphan in shared demo DB  
15. Vehicle key normalization differs (case, prefix)  
16. Archived flag flipped only in JSON overlay path  
17. Session `active_case_id` points to deleted case  
18. Enforcement disabled in prod by mis-env  
19. Enforcement enabled without UI sending header → 403 confusion  
20. Strict legacy hides all cases for office with only unstamped data  
21. Talk-to-agent path omits org on analytics (partial events)  
22. Append API uses wrong case_id from clipboard  
23. Support replay ticket lacks org context in narrative  
24. Replay imports case from wrong deployment epoch  
25. `client_id` shared across offices → weak secondary guard  
26. WeChat binding session without org stamp  
27. Founder clears env mid-pilot → behavior flip  
28. Load test mixes orgs in one client pool  
29. Cached FE case list stale vs binding list  
30. Third-party iframe cannot set custom headers  

*(Risk ≠ current bug; catalog for simulations and ops.)*

## TOP_30_SUPPORT_CONFUSION_PATTERNS

1. “403 case_office_mismatch” — user swapped office tab  
2. Empty workbench after strict legacy on  
3. Case exists in DB but not in office-filtered list  
4. Session “lost” after org header change (by design)  
5. Analytics event missing org — interpreted as cross-tenant leak  
6. `asserted_org_id` empty — assumed “global”  
7. PG `office_owner_org_id` null while `extra` has org  
8. Support manifest vs runtime env mismatch  
9. Replay without `intake_schema_epoch`  
10. JSON artifact on laptop vs Cloud SQL truth  
11. Founder mistakes stub for full transcript  
12. Customer sees broker A thread; case stamped org B  
13. Append blocked vs new case — broker UX  
14. `active_case_id` cleared — feels like “forgetting”  
15. Vehicle ambiguity — “why didn’t it attach?”  
16. Closed case still in mental model  
17. dual identifiers: `record_id` vs `case_id` wording  
18. English vs Chinese logs — search friction  
19. `handoff_ready` false — support thinks broken  
20. OCR attachment path — support assumes triage bug  
21. Rate limit vs auth failure conflation  
22. Session 404 — refresh expectations  
23. WeChat simulate flag in prod confusion  
24. `product_only` gates vs missing manifest secret  
25. case-head missing messages — “incomplete export”  
26. Migration partial — counts disagree  
27. Timezone skew on `updated_at` ordering  
28. Browser privacy mode drops session storage  
29. Multi-agent founder docs contradict runtime  
30. Customer phone reused across offices  

## TOP_30_FAKE_MULTI_OFFICE_PATTERNS_V4

1. Treating `X-Org-Id` as IAM  
2. Calling stub list “tenant isolation”  
3. Marketing “multi-tenant” on header assertion  
4. Hiding unstamped rows without migration story  
5. Guaranteeing no cross-office reads with enforcement off  
6. RBAC labels without roles  
7. SSO narrative on static demo  
8. Billing per office without metering  
9. “RLS” mention without Postgres RLS  
10. Implying crypto binding of org to case  
11. Customer portal tenancy fiction  
12. Single DB row “tenant key” absolutism  
13. Ignoring founder SQL superuser reality  
14. Audit trail completeness claims  
15. Support export as compliance artifact  
16. Conflating `client_id` with auth subject  
17. Session id as security boundary  
18. Org in URL query string as “secure scope”  
19. Fake per-office encryption story  
20. Enterprise reviewer checklist theater  
21. Auto-generated “data residency” claims  
22. Map `office_owner_org_id` to legal entity without contract  
23. Promising GDPR erase per office on JSON demos  
24. Concurrency “locks” without transactions  
25. Treating vehicle key as authentication  
26. Implying replay determinism across LLM versions  
27. Uniform SLA per office at 100 offices  
28. “Zero trust” wording on optional header  
29. Dashboard org drop-down without server truth  
30. Calling filtered binding “RLS-equivalent”  

## TOP_20_HIGH_ROI_MOVES

1. Keep sending `X-Org-Id` from all intake clients (discipline)  
2. Turn enforcement on per pilot cutover checklist  
3. Backfill `office_owner_org_id` after migrations  
4. Monitor logs: `active_case_cleared_wrong_office_hint`  
5. Monitor logs: `session_office_assertion_shift_cleared_active_case`  
6. Add FE banner when org header missing in pilot mode  
7. Document strict legacy migration path per broker  
8. Support playbook: 403 mismatch triage  
9. Expand simulations: org swap mid-session  
10. Optional triage response warning fragment on ambiguous bind  
11. Rate-limit cross-org case_id probing (abuse)  
12. Align analytics always-on `org_id` when header present  
13. Periodic audit: unstamped case share  
14. Founder dashboard: office counts  
15. PG-only reads in prod (already standard)  
16. Session TTL / cleanup ops  
17. Clipboard case_id guard in UI  
18. Explicit “office” label in workbench row  
19. Schema epoch in every support ticket template  
20. Next sprint: explicit **cross-office ambiguity** surfacing in triage result (soft, not blocking)  

## WHAT_BREAKS_AT_30_OFFICES

- Header discipline drift; typos fragment analytics  
- Shared unstamped legacy pool creates binding noise  
- Support confusion scales linearly without runbooks  
- Founder manual SQL without office predicate errors  

## WHAT_BREAKS_AT_100_OFFICES

- Org id namespace collisions / informal strings  
- Operational cost of unstamped backlog  
- Dashboard performance if listing unscoped queries reappear  
- Incident response without automated org-context traces  

## WHAT_BREAKS_AT_ENTERPRISE

- Contractual IAM, SSO, SCIM, real RLS, data residency  
- Per-tenant keys, audit, DPAs — **explicitly out of scope** for this layer  

---

## Phase 3 — Architecture convergence (smallest safe path)

**Chosen path:** reuse **`case_visible_in_office_list`** semantics for binding candidates whenever `client_asserted_org_id` is present; clear sticky session binding when session org stamp or case org hint disagrees with current request org; preserve session org hint across post-create trim writes.

**Rollback:** revert touched functions; unset new posture dict keys (cosmetic); no migration required.

---

## Phase 4 — Implementation summary

| Item | Status |
|------|--------|
| A. Office-aware binding candidate filtering | **Done** — optional org on binding list + PG scoped query |
| B. Office-aware active-case selection | **Done** — mismatch clears sticky `active_case_id`; session org shift clears |
| C. Append continuity | **Existing** assert + boundary clears; binding pool reduces wrong-office picks upstream |
| D. Session continuity office validation | **Done** — session/org/case org checks on triage entry |
| E. Replay lineage office continuity | **Done** — posture dict keys |
| F. Support replay office context | **Partial** — case-head already had `asserted_org_id`; manifest keys extended |
| G. Ownership continuity warnings | **Logs** — info-level clears |
| H. Legacy unstamped handling | **Unchanged** — still visible when strict legacy off |
| I. Cross-office ambiguity detection | **Partial** — vehicle ambiguity returns none; no new user-visible copilot string |

---

## Phase 5 — Validation outputs

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api tests` | PASS |
| `PYTHONPATH=. pytest tests/` | PASS |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS |
| `cd ui && npm run build` | **FAIL** — see Node note below |
| `cd ui && npx madge --circular --extensions ts,tsx src` | PASS (no cycles) |

### Node / Vite build failure (exact)

- **Runtime:** Node.js **20.18.2**
- **Vite requirement:** **20.19+** or **22.12+** (message from `vite build`)
- **Failure:** `failed to load config` → `ERR_REQUIRE_ESM` loading Vite from `vite.config.ts` under incompatible Node/toolchain combo  
- **Remediation:** upgrade Node to **≥20.19** (or **22.12+**) per Vite, then re-run `npm run build`

---

## Phase 6 — SELF_CRITIQUE_REPORT_V7

| Persona | Attack |
|---------|--------|
| Skeptical broker | “You still trust my browser header — an angry CSR could paste another office’s case id.” **True** — enforcement optional; we reduced accidental auto-bind, not clipboard attacks. |
| Angry office manager | “Two unstamped cases still collide.” **True** if strict legacy off — operational policy must drive stamping. |
| Support lead | “Logs help; tickets still need human org story.” **Accepted** — replay honest but not automatic narrative. |
| Exhausted founder | “I can still misconfigure env and blame code.” **True** — posture dict aids diff, not discipline. |
| Deployment operator | “PG scoped query wrong filter?” **Mitigated** — reuses proven `_PG_OFFICE_LIST_FILTER`. |
| Enterprise reviewer | “Not RBAC.” **Correct** — we refuse fake tenancy theater. |

---

## Phase 7 — Convergence answers

1. **What became REAL?** Office-scoped binding candidate retrieval when org asserted; sticky binding cleared on org mismatch; session org preserved after case-create trim; documented posture keys.  
2. **What is still fake SaaS?** Per-office billing, IAM, SSO, “tenant platform” guarantees.  
3. **What is still fake tenancy?** Cryptographic isolation — **none**; header assertion only.  
4. **What continuity is now reliable?** Same org + stamped cases: fewer wrong-office auto-binds; session org survives trim; enforcement path unchanged but better upstream alignment.  
5. **What continuity still breaks?** No header; unstamped legacy pool; explicit malicious case_id; clipboard errors.  
6. **Operationally survivable?** Yes — logs + scoped queries + rollback-safe diff size.  
7. **Support-survivable?** Improved honesty strings in manifest; still needs human playbook for 403/lost binding.  
8. **Deployment-honest?** Manifest records binding scope semantics; schema epoch unchanged this sprint.  
9. **Replay-honest?** Partial — org hints surfaced; not full transcript export.  
10. **Next smallest 10x move?** **Require `X-Org-Id` in pilot UI builds** (fail loud in staging) + migrate unstamped backlog policy per broker.  

---

## Operator warnings

- Turning **`UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY`** on without stamping legacy data **hides** cases from both list **and** binding pool for that org.
- Clearing `active_case_id` on org header change can surprise users who **legitimately** switched offices on the same device — **prefer per-office browser profile** in pilot docs.

---

## Migration notes

- None required for this sprint’s code path; PG index/filter column promotion remains as prior sprint DDL.

---

## Simulations recommended (Loops B–C)

- Org A session → switch header to Org B mid-thread → expect cleared sticky bind  
- Two stamped cases same VIN different orgs → expect no vehicle auto-bind without session  
- Enforcement on + wrong org explicit `case_id` → 403  
- Legacy unstamped + strict off → appears in binding pool for every asserted org  

---

*End SSOT — add future discoveries only to this file per sprint rule.*
