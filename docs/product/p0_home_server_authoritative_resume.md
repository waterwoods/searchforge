# P0 — Home Resume is Server-Authoritative

**Status:** Implemented  
**Date:** 2026-07-22  
**Objective:** Mini Program Home Continue / Start Claim must follow `/api/h5/customer/session`, not a stale local resume token.  
**Out of scope:** Broker UI, History browsing, Timeline, Production deploy.

---

## Architecture path

```text
Service Home onShow
  → shell (Start Claim default; §J)
  → ensureCustomerSession()
       → wx.login / simulate code
       → POST /api/h5/customer/session
       → applyServerActiveCaseAuthority()
            ├─ has_active_case + resume_token → saveResumeToken (cache)
            └─ has_active_case false          → clearResumeToken
  → Home UI from session.hasActiveCase (not raw storage read alone)
  → local storage is cache only
```

---

## Failure strategy (session unavailable)

When `/customer/session` fails (network, `wechat_mp_not_configured`, etc.):

1. Do **not** leave Home on Continue forever from an unchecked cache.
2. If a local resume token exists, **reconcile** via `GET /api/h5/tasks/{token}/intake`.
   - `case_closed_read_only` / closed History / missing / invalid token → `clearResumeToken` → Start Claim.
   - Intake OK and not closed → keep resume (case still open; session identity path unavailable).
3. If no local resume → Start Claim.
4. Transient probe failure with existing resume: keep cache for this show only; next successful session or closed probe clears it.

**Rule:** Server case terminal state and session Active binding outrank `mp_prototype_resume_token`.
