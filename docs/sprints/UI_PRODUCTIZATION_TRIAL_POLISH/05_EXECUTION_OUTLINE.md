# Execution Outline

**Sprint:** UI Productization / Trial UI Polish

---

## 1. Workstreams

| # | Workstream | Scope |
|---|------------|-------|
| 1 | Entry Experience | Welcome area, buttons, trust copy, chat layout |
| 2 | Workbench UI | Case cards, next move, section naming, demo queue card |
| 3 | Demo/Trial Polish | Copy pass, visual hierarchy, empty states |

---

## 2. Implementation Order

1. **Loop 1:** Entry Experience — welcome, buttons, trust, first impression
2. **Loop 2:** Workbench — case cards, next move visibility, section grouping
3. **Loop 3:** Demo/Trial — copy pass, demo queue card, one more polish slice

---

## 3. Test Plan

- `cd ui && npm run build` — must pass after each loop
- Manual inspection: Entry screen, Workbench, case cards
- No regression to existing behavior

---

## 4. Loop Plan

- **Loop 1:** 3–5 high-value entry changes
- **Loop 2:** 3–5 high-value workbench changes
- **Loop 3:** 2–3 demo/trial polish changes
- **Loop 4:** Optional; only if one clearly valuable refinement remains

---

*End of Execution Outline*
