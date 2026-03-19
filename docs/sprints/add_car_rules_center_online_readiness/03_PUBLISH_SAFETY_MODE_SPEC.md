# Add-Car Rules Center — Publish Safety / Mode Spec

**Sprint:** Add-Car Rules Center Online Readiness  
**Purpose:** Explicitly decide publish behavior for online vs local environments.

---

## 1. Production Persistence Reality

| Environment | Config path | Writable? |
|-------------|-------------|-----------|
| Local dev | `configs/industries/insurance/add_car_rules.json` | Yes |
| Cloud Run | Same path (baked into image) | **No** (read-only filesystem) |

**Conclusion:** Production (Cloud Run) cannot persist config. Publish will fail with 503.

---

## 2. Chosen Mode: Option B — Draft / Preview Mode When Unsafe

**Rule:** Do NOT leave a misleading "发布" button online if production persistence is unreliable.

**Implementation:**
- Backend exposes **publish capability** (e.g. `publishable: true/false` in GET /api/inbox/add-car-rules response).
- Capability is determined by attempting a minimal write test to the config directory.
- When `publishable: false`:
  - Publish button is **disabled**
  - Explanatory label: "此环境为预览模式，无法保存到配置"
  - Alert: "可编辑和预览，但无法在此发布。如需正式发布，请在本地环境操作。"

---

## 3. What Online Users Are Allowed to Do

| Action | Allowed? | Notes |
|--------|----------|-------|
| View rules | Yes | GET loads from config (read-only) |
| Edit draft | Yes | UI state only |
| Preview | Yes | Uses draft override; no write |
| Restore | Yes | Reloads from backend; no write |
| Publish | **Only when publishable** | Disabled when backend reports read-only |

---

## 4. How the UI Should Label This

| Scenario | Badge / Label | Publish button |
|----------|---------------|----------------|
| Publishable (local) | (none or "可发布") | Enabled |
| Not publishable (Cloud Run) | "预览模式" | Disabled + tooltip |

---

## 5. Restore Behavior

- **Restore** = reload from GET /api/inbox/add-car-rules, clear draft.
- No write required. Always available.

---

## 6. Summary

| Decision | Choice |
|----------|--------|
| Online publish | Disabled when config dir is read-only |
| UI honesty | Must not promise publish when it will fail |
| Fallback | Draft + preview only; "copy config locally" not in scope for this sprint |
| Restore | Always available |

---

*See also: 02_ONLINE_READINESS_UX_SPEC.md*
