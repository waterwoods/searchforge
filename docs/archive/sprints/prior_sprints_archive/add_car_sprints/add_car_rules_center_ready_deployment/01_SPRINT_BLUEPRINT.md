# Add-Car Rules Center Ready Deployment Sprint — Blueprint

**Sprint name:** Add-Car Rules Center Ready Deployment Sprint  
**Target budget:** 20–40 minutes  
**Execution mode:** Long-running structured execution for Cursor Composer / multi-agent workflow

---

## 1. Why Deployment Is Needed Now

The Rules Center now has:
- a business-friendly page
- editable Add-Car Quote fields
- preview/test capability
- safe publish mode design (`publishable` field, preview-only when read-only)

**But this only helps the founder if the latest frontend and backend are both live.**

The founder needs to know:
- Can I open the Rules Center on Vercel?
- Does it show the right online-ready behavior?
- Does it honestly indicate preview-only mode if publish is not safe?

---

## 2. What Must Be Live

| Component | Requirement |
|-----------|-------------|
| Frontend | AddCarRulesPage at `/workbench/add-car-rules` on Vercel production |
| Backend | GET `/api/inbox/add-car-rules` returns `publishable`; safe publish/preview logic |
| UI behavior | If `publishable=false` → "预览模式" badge, disabled publish, warning |
| UI behavior | If `publishable=true` → publish enabled, consistent with design |

---

## 3. What Counts as Success

- Backend deploy completes (Cloud Run)
- Frontend deploy completes (Vercel production alias updated)
- Production route `/workbench/add-car-rules` exists and loads
- Production backend returns `publishable` in GET response
- UI reacts correctly to `publishable` true/false
- Founder can inspect and demo the page without confusion

---

## 4. Non-Negotiable Rule

Do NOT stop at "deployment succeeded". Verify production truth by checking:
- production frontend route exists
- production backend returns the new `publishable` field
- production UI reacts correctly to publishable true/false
- the page is understandable and safe online

---

*See also: 02_EXECUTION_OUTLINE.md, 03_ACCEPTANCE_CRITERIA.md*
