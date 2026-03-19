# Acceptance / Client-Reuse Criteria

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## Practical Criteria

| Criterion | Pass |
|-----------|------|
| Clearer client-specific variation | Visible difference between chen_kui and demo_broker |
| Reduced hardcoding | UI copy from config, not hardcoded in React |
| Stronger reuse story | Founder can explain "new broker = new folder" |
| Easier migration path | Change client via URL or env, no code change |
| What remains acceptable to defer | Full multi-tenant; admin UI; backend config_loader client param |

---

## Must Have

- [ ] At least one visible runtime/UI difference driven by client config
- [ ] UI loads app_title, office_label, office_workbench from config
- [ ] Second demo client (demo_broker) exists and shows different copy
- [ ] guardrail_inbox_triage.sh PASS
- [ ] npm run build PASS

---

## Nice to Have

- [ ] Client from URL ?client= works
- [ ] Handoff success message from config
- [ ] Quick-start buttons from config
