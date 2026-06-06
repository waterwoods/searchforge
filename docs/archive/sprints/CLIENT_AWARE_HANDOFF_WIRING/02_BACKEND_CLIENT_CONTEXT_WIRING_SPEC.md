# Backend Client Context Wiring Spec

**Purpose:** Define how client_id enters the backend and how triage/handoff can access it.

---

## 1. How client_id Enters the Backend

| Source | Priority | When | Fallback |
|--------|----------|------|----------|
| Request body `client_id` | 1 | POST /api/inbox/triage | — |
| Query param `client` | 2 | POST /api/inbox/triage?client= | — |
| Request body | 3 | (same as 1) | — |
| CLIENT_ID env | 4 | When neither above | chen_kui |

**TriageRequest:** Add optional `client_id: str | None = None`.  
**Route:** Read `client_id` from body or `client` from query; use `get_active_client_id()` when empty.

---

## 2. How Triage/Handoff Access client_id

| Component | Access | Mechanism |
|-----------|--------|-----------|
| `triage_conversation` | `client_id` param | Passed from route |
| `config_loader.get_handoff_phrases(client_id)` | Load by client | `configs/clients/{client_id}/handoff_phrases.json` |
| `config_loader.get_reply_templates(client_id)` | Load by client | Industry + `configs/clients/{client_id}/reply_overrides.json` |
| `triage_for_append` | `get_active_client_id()` | No client on case yet; use env default |

---

## 3. Default / Fallback Behavior

| Situation | Behavior |
|-----------|----------|
| `client_id` missing | Use `get_active_client_id()` (env or chen_kui) |
| Client config file missing | Fall back to `configs/clients/chen_kui/handoff_phrases.json` |
| Chen Kui config missing | Use hardcoded generic fallbacks (no "陈奎") |

---

## 4. Minimal Runtime Mechanism

- **No per-request context/thread-local** — pass client_id explicitly through function signatures.
- **Cache per client_id** — `_HANDOFF_CACHE: dict[str, dict]` keyed by client_id to avoid repeated file reads.
- **Config load path** — `configs/clients/{client_id}/handoff_phrases.json`; if missing, try chen_kui; if still missing, return {} and use hardcoded fallbacks in triage.

---

*End of Spec*
