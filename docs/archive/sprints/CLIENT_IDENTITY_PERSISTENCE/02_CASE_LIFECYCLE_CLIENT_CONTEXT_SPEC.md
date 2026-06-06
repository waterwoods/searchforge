# Case Lifecycle Client Context Spec

**Purpose:** Define where client_id should live and how it moves through the case lifecycle.

---

## 1. Where client_id Should Live

| Location | Field | Purpose |
|----------|-------|---------|
| **Case** | `client_id: str` | Source of truth for persisted case; used for append/reopen |
| **TriageRequest** | `client_id: str \| None` | Entry: client selection |
| **AppendMessageRequest** | Optional `client_id` | Fallback when case has no client_id (legacy) |

---

## 2. How client_id Moves from Entry/Session into Case

**Flow:**
1. User opens UI with `?client=chen_kui` or `?client=demo_broker`
2. ClientConfigProvider fetches config; `clientId` = `chen_kui` or `demo_broker`
3. User triages message; `triageMessage(..., clientId)` → POST `/api/inbox/triage` with `client_id`
4. Route passes `client_id` to `triage_conversation`
5. When `persist_case=true`, route calls `save_case(..., client_id=client_id)`
6. `save_case` stores `client_id` on the case object

---

## 3. Default / Fallback Behavior

| Situation | Behavior |
|-----------|----------|
| Case has `client_id` | Use it for append |
| Case has no `client_id` (legacy) | Use `get_active_client_id()` (env or chen_kui) |
| AppendMessageRequest has `client_id` | Use it when case has no client_id |
| Request body empty, case empty | `get_active_client_id()` |

---

## 4. Case Fields / Structures to Update

- **case_store.save_case:** Add `client_id: str | None = None`; persist when provided
- **case_store._normalize_case:** Preserve `client_id` if present; no migration for legacy
- **case_store.append_follow_up_message:** Preserve case `client_id`; do not overwrite
- **API route persist_case:** Pass `client_id` to `save_case`
- **API route append_case_message:** Pass `case.get("client_id")` to `triage_for_append`
