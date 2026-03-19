# Client-Aware Handoff Blueprint

**Sprint:** Client-Aware Handoff / Triage Wiring  
**Purpose:** Extend client configuration wiring into backend triage and handoff behavior.  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why Backend Client-Aware Handoff Matters Now

The product already has:
- Common / industry / client configuration foundation
- Client UI copy wiring (GET /api/inbox/client-config?client=)
- Visible Client A vs Client B variation in frontend/runtime
- Stronger scenario package, trial package, workbench

**But a major remaining weakness:** Backend triage and handoff still use Chen-Kui-specific wording or behavior. The founder can say "the UI changes by client" but cannot yet fully say "the handoff and backend-facing product behavior also change by client."

**The next most valuable move:** Wire client-aware handoff/triage so the product becomes more truly reusable.

---

## 2. Why This Is the Right Move After Client UI Wiring

1. **UI wiring proved the pattern** — client config fetch, URL param, merge with defaults. Backend wiring follows the same pattern.
2. **Handoff is the highest-value backend surface** — it's what the broker sees and sends to customers. Client-specific phrasing here has the strongest reuse impact.
3. **Minimal scope** — no tenancy, no auth, no DB changes. Just pass client_id and load the right config file.

---

## 3. What This Sprint Will Strengthen

| Area | Before | After |
|------|--------|-------|
| Client ID in triage path | Not passed | Passed from request → triage_conversation |
| Handoff phrases | Hardcoded chen_kui path | Loaded by client_id |
| Fallback wording | "陈奎办公室" | Generic "office/team" or client-specific |
| A/B demo | UI only | API-level handoff variation |
| Founder story | "UI changes" | "handoff and backend behavior change" |

---

## 4. What This Sprint Intentionally Will NOT Do

- Full tenant platform
- Multi-tenant auth or DB isolation
- Redesign of whole backend
- Giant admin tooling
- Client-specific business logic branching beyond handoff phrases
- Persisting client_id on cases (deferred for append-message)

---

*End of Blueprint*
