# Configuration Foundation Blueprint

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why Reusable Configuration Matters Now

The product has reached trial readiness. Chen Kui can use it. The demo path works. But if the founder wants to sell to multiple brokers or SMB clients, the current system still feels like a **Chen Kui custom project** rather than a **reusable vertical product with configurable templates**.

**The next most valuable move:** Establish the first real reusable template/configuration layer so that:
- Adding a second broker client does not require code changes
- Industry-specific logic (insurance scenarios, markers) is clearly separated from client-specific copy (Chen Kui wording)
- The product story becomes: "We have a configurable broker assistant; Chen Kui is our first client"

---

## 2. Why This Is the Right Move After Trial/Readiness Work

| Prior work | What it delivered |
|------------|-------------------|
| Trial package | Real broker scenarios, value validation, pilot offer |
| Trial launch / fix-now | Last-mile hardening, runbook, handoff spec |
| Stronger scenario logic | Multi-turn continuity, handoff clarity, broker_next_step |
| Config extraction (earlier sprints) | markers.json, reply_templates.json, handoff_phrases.json, add_car_rules.json |

**Gap:** The config layer is partial. broker_next_step, client_prep, and many UI strings remain hardcoded. The common layer is empty. Client-specific copy is mixed with industry logic in several places.

**This sprint:** Tighten boundaries, extract the next highest-value hardcoded clusters, and make the reuse story credible.

---

## 3. What This Sprint Will Strengthen

1. **Clearer base / industry / client boundaries** — Documented and partially implemented
2. **broker_next_step and client_prep** — Moved from triage.py to industry config where practical
3. **Common layer** — First real config (workflow defaults, fallback labels)
4. **Client-specific UI copy** — Centralized so another broker can swap without touching React
5. **Reusability narrative** — Founder can explain: "This is a template; Chen Kui is one configuration"

---

## 4. What This Sprint Intentionally Will NOT Do

- **No full no-code builder** — No admin UI for editing all config
- **No multi-tenant architecture** — No runtime client switch; config paths remain fixed
- **No broad refactor** — No rewrite of triage or UI; incremental extraction only
- **No new features** — Focus on configurability, not new flows

---

## 5. Success Criteria (High Level)

- At least one major hardcoded cluster (broker_next_step/client_prep) extracted to config
- Common layer has at least one real config file (not just README)
- Config inventory and boundary spec are accurate and actionable
- Guardrail and build pass
- Founder can inspect and explain the layering

---

*See also: 02_BASE_VS_INDUSTRY_VS_CLIENT_BOUNDARY_SPEC.md*
