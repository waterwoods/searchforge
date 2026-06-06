# Demo vs Production Boundary Spec

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. What Counts as Demo-Only Behavior

| Behavior | Demo | Production |
|----------|------|------------|
| JSON file storage | Yes | Yes (for pilot) |
| Single broker, no auth | Yes | Yes (for pilot) |
| Config writable (Rules Center) | Local only | Cloud Run read-only |
| Session/case path | Default data/ | Env override for isolation |
| Offline fallback | Yes | No (or separate) |

---

## 2. What Must Be Safe for Paid Pilot

- Case persistence (no data loss)
- Session persistence (refresh recovery)
- Status/notes/follow-up updates
- Append follow-up message
- Same triage logic
- Same API contract

---

## 3. What Should Be Isolated Between Demo and Production

| Aspect | Isolation |
|--------|-----------|
| **Storage path** | UNIFIED_INTAKE_CASES_PATH, UNIFIED_INTAKE_SESSIONS_PATH |
| **Config** | Cloud Run: configs read-only; local: writable |
| **CORS** | ALLOWED_ORIGINS for production |

---

## 4. Acceptable Temporary Shortcuts

- Same JSON format for demo and pilot (no separate demo DB)
- No per-broker isolation (single-tenant pilot)
- No backup/restore automation
- No audit log beyond case_activity

---

## 5. Demo/Prod Flag (Optional This Sprint)

If time permits: `MODE=demo` or `UNIFIED_INTAKE_MODE=demo` to:

- Use separate data paths (e.g. data/demo_*)
- Disable config publish
- Add "Demo" badge in UI

**Deferred:** Full demo/prod mode split. Current env-based path override is sufficient.

---

*See also: `docs/DEPLOYMENT_READINESS.md`*
