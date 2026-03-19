# Acceptance / Lifecycle Client-Aware Criteria

---

## Practical Criteria

| Criterion | Status | How to Verify |
|-----------|--------|---------------|
| **client_id persisted on case** | Required | save_case stores client_id; GET /cases returns it |
| **Append uses case client_id** | Required | Append to chen_kui case with ?client=demo_broker open → draft uses chen_kui |
| **Reopen preserves client context** | Required | Case opened from list → append uses case.client_id |
| **Reduced hardcoding** | Required | No client_id in URL when append; case is source of truth |
| **A→B migration story** | Required | Founder can explain: "case remembers client through lifecycle" |
| **Deferred acceptable** | OK | add-car-rules client param; full tenancy |

---

## What Remains Acceptable to Defer

- add-car-rules API client param
- Full multi-tenant isolation
- Client config editor
