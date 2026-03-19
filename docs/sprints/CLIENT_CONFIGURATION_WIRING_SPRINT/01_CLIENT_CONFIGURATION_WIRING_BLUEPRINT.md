# Client Configuration Wiring Blueprint

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why Runtime/Client Wiring Matters Now

The configuration layer foundation (common → industry → client) is in place. Config files exist:
- `configs/clients/chen_kui/handoff_phrases.json` — wired to triage
- `configs/clients/chen_kui/reply_overrides.json` — wired to triage
- `configs/clients/chen_kui/ui_copy.json` — **not wired**; UI still hardcoded

The founder's practical question: **Can we move from Client A to Client B without too much pain?**

Right now: easier than before (handoff/reply config), but not yet easy enough. The UI still screams "Chen Kui custom project" because every label is hardcoded.

---

## 2. Why This Is the Right Move After Configuration Foundation

- Config structure is correct; files exist.
- Backend already loads client config (handoff, reply).
- **Gap:** UI copy is never loaded. `ui_copy.json` is documentation-only.
- **Next:** Wire UI to load client config so visible differences appear.

---

## 3. What This Sprint Will Strengthen

| Area | Before | After |
|------|--------|-------|
| UI copy | Hardcoded in React | Loaded from client config |
| App title | "保险经纪人智能助手" | From `ui_copy.app_title` |
| Office label | "办公室" | From `ui_copy.office_label` |
| Quick-start buttons | Hardcoded | From `ui_copy.quick_start_buttons` |
| Handoff success message | "办公室会尽快处理..." | From `ui_copy.handoff_default` |
| Client selection | None | Env or query param |

---

## 4. What This Sprint Will NOT Do

- **No** full admin portal
- **No** multi-tenant auth/database
- **No** full frontend rewrite
- **No** complex database tenancy
- **No** visual config builder

---

## 5. Success Criteria

- At least one visible runtime/UI difference driven by client config
- Founder can explain: "one base, one industry template, multiple client configs"
- Moving from Client A to Client B looks lighter and more credible

---

*See also: docs/CONFIG_EXTRACTION_GUIDE.md, docs/CLIENT_PACK_FOUNDATION.md*
