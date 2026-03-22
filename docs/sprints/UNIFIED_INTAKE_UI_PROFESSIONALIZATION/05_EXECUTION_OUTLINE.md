# Execution Outline — Unified Intake UI Professionalization

**Sprint**: Unified Intake UI Professionalization

---

## Workstreams

1. **Structure**: 3-layer layout (Trust → Actions → Free Input)
2. **Visual**: Card/container professionalization, color fix, spacing
3. **CTA**: Action modules, hierarchy, guidance copy

---

## Implementation Order

1. **Loop 1**: Page structure / hierarchy
   - Add explicit Trust/Hero section
   - Restructure: Hero → Actions card → Free input card
   - Reduce "big textarea as page" feeling
   - De-emphasize or relocate "模拟演示"

2. **Loop 2**: Visual language / containers
   - Fix dark-theme remnants (rgba white on light bg)
   - White cards, light gray page background
   - Card boundaries, spacing consistency
   - Typography hierarchy

3. **Loop 3**: CTA / guidance / polish
   - Action modules as deliberate service entry points
   - Free input clearly secondary
   - Trust copy improvement
   - Final spacing/padding

---

## Verification Plan

- `cd ui && npm run build` after each loop
- Local preview: http://localhost:5173/workbench/unified-intake
- Check: Trust visible, actions prominent, free input secondary
- Check: No dark-theme remnants on light background

---

## Deployment Approach

- Frontend only: `cd ui && vercel --prod`
- No backend changes

---

*End of outline*
