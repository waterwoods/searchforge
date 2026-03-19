# Append / Follow-Up Client-Aware Spec

**Purpose:** Define how append/follow-up discovers client context and stays client-aware.

---

## 1. How Append/Follow-Up Should Discover Client Context

**Primary:** Read `client_id` from the persisted case.

**Fallback order:**
1. `case.get("client_id")` — if case was saved with client_id
2. `AppendMessageRequest.client_id` — if frontend passes it (e.g. from URL context)
3. `get_active_client_id()` — env or chen_kui

---

## 2. How Handoff/Draft Wording Should Stay Client-Aware

- `triage_for_append` must accept `client_id: str | None = None`
- When called from append route: `triage_for_append(..., client_id=case.get("client_id"))`
- `triage_for_append` passes `client_id` to `triage_conversation`
- `triage_conversation` uses `_get_handoff_phrases(client_id)` → same as initial triage

---

## 3. How Reopened Cases Should Remain Client-Aware

- When user opens case from Workbench (case list or detail), the case has `client_id`
- Append flow uses `case.client_id` → no dependency on current URL ?client=
- If case has no client_id (legacy), frontend can pass `clientId` from `useClientConfig()` as fallback

---

## 4. What Should Happen If Client Config Missing

- Same as initial triage: fallback to chen_kui, then generic
- `triage_for_append` uses `triage_conversation(..., client_id=...)` which already handles this
