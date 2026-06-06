# P16-U Phase 3 — Auto-Fix Candidate Classification

**Date:** 2026-06-01  
**Method:** Map each baseline failure/warning to fix class per P16-U rules

---

## Classification key

| Class | Meaning |
|-------|---------|
| **Safe Auto Fix** | Agent can apply without founder; low regression risk |
| **Needs Founder Approval** | Vercel/GCP dashboard or business decision |
| **Needs Infrastructure Access** | Secrets, Secret Manager, production credentials |
| **Needs Human Judgment** | E2E UX, commercial, trial protocol |

---

## By failure

### 1. Preview HTTP 401 / FP-004 SSO

| Field | Value |
|-------|-------|
| **Failure** | `preview_url_reachable`, `preview_protection_absent` |
| **Classification** | **Needs Founder Approval** |
| **Rationale** | Vercel Deployment Protection is a project-setting toggle; CLI has no `vercel protection disable` command; only Andy (`waterwoods` scope) can change |
| **Auto-fix possible?** | No |
| **Time to close** | ~5 min (dashboard toggle) |
| **Risk if deferred** | P0 — trial-killing; every Preview URL share fails |

---

### 2. Production bundle stale / FP-001 + FP-013

| Field | Value |
|-------|-------|
| **Failure** | Parity note; Production missing P16-O + product_only |
| **Classification** | **Needs Founder Approval** |
| **Rationale** | Production promotion changes broker-facing public URL; P16-R explicitly deferred prod deploy pending Preview gates |
| **Auto-fix possible?** | Technically yes via `vercel deploy --prod` (CLI authenticated) — **blocked by policy**: promote only after Preview cold PASS |
| **Time to close** | ~15 min after SSO fix |
| **Risk if deferred** | P0 — brokers opening Production get wrong UI |

---

### 3. Local `.env.cloudrun` pilot posture / FP-011

| Field | Value |
|-------|-------|
| **Failure** | `pilot_env_posture` WARN |
| **Classification** | **Safe Auto Fix** (partial) + **Needs Infrastructure Access** (API keys) |
| **Rationale** | Posture flags can sync from `deploy_paid_pilot.sh` tuple; API keys live in Secret Manager |
| **Auto-fix possible?** | Yes for flags; no for secrets |
| **Time to close** | Flags: done; keys: ~10 min founder/infra |
| **Risk if deferred** | P1 — next full backend deploy could regress posture |

---

### 4. Missing Andy E2E log / FP-010 + FP-015

| Field | Value |
|-------|-------|
| **Failure** | Reality gate — no deployed-browser proof |
| **Classification** | **Needs Human Judgment** |
| **Rationale** | 15-min paste loop requires founder eyes; blocked until SSO off |
| **Auto-fix possible?** | No |
| **Time to close** | 15 min after FP-004 |
| **Risk if deferred** | P1 — false confidence in bundle-only proof |

---

### 5. Commercial gaps / FP-009

| Field | Value |
|-------|-------|
| **Failure** | Not runner-detected; inherited from P16-K/Q |
| **Classification** | **Needs Human Judgment** |
| **Rationale** | Invoice IDs, pricing, observation log |
| **Auto-fix possible?** | No |
| **Time to close** | ~30 min founder |
| **Risk if deferred** | P1 at Day 7 |

---

### 6. CORS regression guard / FP-002

| Field | Value |
|-------|-------|
| **Failure** | None — PASS |
| **Classification** | N/A — **monitor only** |
| **Note** | Next Preview deploy hash requires ALLOWED_ORIGINS update — classify future failure as Safe Auto Fix **if** `.env.cloudrun` already has origin + deploy script run |

---

## Summary table

| Issue | FP | Class | P16-U action |
|-------|-----|-------|--------------|
| Preview SSO 401 | FP-004 | Founder Approval | Document; cannot auto-fix |
| Prod stale bundle | FP-001/013 | Founder Approval | Blocked on FP-004 gate |
| Local env posture | FP-011 | **Safe Auto Fix** | ✅ Applied |
| Local API keys missing | FP-011 | Infrastructure | Document only |
| Andy E2E log | FP-010/015 | Human Judgment | Blocked on FP-004 |
| Commercial pack | FP-009 | Human Judgment | Out of runner scope |

---

## Safe auto-fix queue (executed in Phase 4)

1. ✅ Sync `.env.cloudrun` pilot posture flags (`UNIFIED_INTAKE_PRODUCT_ONLY=1`, `PG_DUAL_WRITE=0`, DB-primary tuple)
2. ✅ Bundle verification documented (Preview markers confirmed via vercel curl)
3. ✅ Documentation sync (this P16-U artifact set)

**Not queued:** Preview SSO toggle, Production promote, API key injection, browser E2E

---

*End of P16-U Phase 3 — Auto-Fix Candidate Classification*
