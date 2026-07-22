# P0 — One Active Case Identity Foundation

**Status:** Implemented (this commit)  
**Date:** 2026-07-22  
**Objective:** Make One Active Case a **server-enforced** invariant for customer create.  
**Out of scope:** Broker Close, History, Workbench/UI redesign, Request More redesign.

---

## 1. Old vs new architecture

### Before (broken for Constitution Rule 1)

```text
Mini Program
  → getPrototypeSessionId() → anon-{timestamp}
  → POST /api/h5/customer/start-claim { session_id: anon-* }
  → Cap2 create_claim (no Active Case index lookup)
  → local resume token only guards duplicates
```

Server could not prevent a second Active Case after storage clear / new device.

### After (production path)

```text
Mini Program
  → wx.login (code)
  → POST /api/h5/customer/session
  → jscode2session OpenID (ephemeral; never returned)
  → person_link_key (HMAC → wx_…)
  → resolve mp_customer_active_case
       ├─ Active exists → resume_token (outcome=resumed; no create)
       └─ none → create_claim → bind Active Case
```

Prototype `anon-*` create is **isolated** to non-Production (local / Cloud QA / harness) and, when allowed, still binds to the Active Case index so repeat creates resume.

---

## 2. Identity types

| Identity | Form | Owner of One Active Case? | Notes |
|----------|------|---------------------------|-------|
| **OpenID** | WeChat technical id | No — never stored/returned | Ephemeral exchange only |
| **person_link / session_id `wx_*`** | HMAC opaque key | **Yes — SSOT for MP** | `mp_customer_active_case.person_link_key` |
| **Prototype `anon-*`** | Device-local storage | QA/local only (index-bound when allowed) | Rejected on Production deployment |
| **Harness `p26h-*` / QA fixtures** | Synthetic session | QA fixture surface only | Not Production customer path |
| **WeCom `external_userid`** | Channel bind | Separate WeCom Rule 7 path | Not Mini Program claim create |
| **Phone (add-car resolver)** | Normalized digits | Add-car Customer First path | Out of this commit’s MP claim create |

**Single source of truth for MP Active Case:** table / index `mp_customer_active_case` (`person_link_key` → `case_id`).  
Case stamp `person_link_key` on the case row is additive evidence, not a second index.  
History / closed cases are out of scope here; `case_is_resumable_active` already drops closed/archived/done from Continue.

**Duplicate indexes (report only):**

| Index | Role | Conflict? |
|-------|------|-----------|
| `mp_customer_active_case` | MP Active Case pointer | **Authoritative for this constitution** |
| `intake_sessions.active_case_id` | Web/Unified Intake session continuity | Parallel; not used for MP start-claim |
| WeCom `external_userid` open-case scan | WeCom draft attach | Parallel channel |

No redesign in this commit.

---

## 3. Endpoints audited (customer create / continue)

| Endpoint / entry | Can create Active Case? | One Active Case enforced? |
|------------------|-------------------------|---------------------------|
| `POST /api/h5/customer/session` | No (resolve only) | N/A — returns resume if bound |
| `POST /api/h5/customer/start-claim` | Yes | **Yes** — resolve→resume; Production requires `wx_*`; `force_new` ignored |
| `GET/PATCH/POST /api/h5/tasks/{token}/…` | No (mutate existing) | Token-bound case; not a create fork |
| Slice1 request-item submit | No | Same case via token |
| Evidence upload | No | Same case via token |
| Cap2 `create_claim` via Workbench/broker | Broker-originated | Out of customer Rule 1; not customer fork |
| WeCom `create_or_attach_draft_case_for_start_click` | Add-car draft | Channel Rule 7 (external_userid); separate from MP |
| `POST /customer/start-add-car` | Add-car | Phone resolver; out of MP claim create |
| P26H / P35 harness seed | QA create | Uses `start_customer_claim`; non-Production |

---

## 4. Acceptance (Rule 1)

After this foundation: a **Production** customer using the Mini Program create path **cannot** create two Active Cases for the same durable `wx_*` identity. Repeat create resumes. Anon create is rejected on Production deployment.

**H — Can any Production customer still create two Active Cases?**  
**NO** (same durable `wx_*` identity on `POST /api/h5/customer/start-claim`).

**Simulations (2026-07-22):** S1 Phone A→B resume, S2 cleared storage resume, S3×10 create, S4 independent users, S5 Production anon reject + QA anon resume — all PASS.
