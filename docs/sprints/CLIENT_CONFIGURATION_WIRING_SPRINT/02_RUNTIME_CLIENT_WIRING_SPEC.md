# Runtime Client Wiring Spec

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## 1. How Client Config Is Selected

| Mechanism | Priority | Use |
|-----------|----------|-----|
| Query param `?client=` | 1 | Demo override; URL-based switching |
| Env `CLIENT_ID` | 2 | Production deployment; default per env |
| Fallback | 3 | `chen_kui` |

**Order:** `client` query param (if present) → `CLIENT_ID` env → `chen_kui`

---

## 2. How Runtime Knows Which Client

| Component | How it knows |
|-----------|--------------|
| Backend API | `GET /api/inbox/client-config?client=chen_kui` — client from query or env |
| Backend triage | `config_loader` loads `configs/clients/<client_id>/` — today fixed to `chen_kui`; future: pass client_id |
| Frontend | Fetches `/api/inbox/client-config` on mount; uses `client` from URL search params |

---

## 3. Minimal Client-Switching Mechanism

- **API:** `GET /api/inbox/client-config?client=<id>` — optional; when omitted, backend uses env or default.
- **Frontend:** `?client=demo_broker` in URL — optional; when present, passed to API.
- **Response:** `{ client_id, ui_copy }` — full client UI copy for rendering.

---

## 4. What This Affects

| Backend | Frontend |
|---------|----------|
| New config_loader: `get_ui_copy(client_id)` | New API: `getClientConfig(client?)` |
| New route: `GET /api/inbox/client-config` | New hook: `useClientConfig()` |
| Env: `CLIENT_ID` (optional) | URL: `?client=` (optional) |

---

## 5. Fallback Behavior

If client config missing or invalid:
- Backend returns empty dict or minimal defaults
- Frontend uses hardcoded fallbacks (current behavior) so UI never breaks
