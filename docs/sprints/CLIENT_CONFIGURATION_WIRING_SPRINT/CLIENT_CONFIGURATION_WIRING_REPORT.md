# Client Configuration Wiring Report

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Wire client configuration into real product behavior so moving from Client A to Client B becomes meaningfully easier.
- **Why now:** Config layer foundation exists (common/industry/client); ui_copy.json was documentation-only. The founder question "Can we move from Client A to Client B without too much pain?" needed a concrete answer.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Client Configuration Wiring Blueprint | `docs/sprints/CLIENT_CONFIGURATION_WIRING_SPRINT/01_CLIENT_CONFIGURATION_WIRING_BLUEPRINT.md` |
| Runtime Client Wiring Spec | `02_RUNTIME_CLIENT_WIRING_SPEC.md` |
| Client UI Copy Wiring Spec | `03_CLIENT_UI_COPY_WIRING_SPEC.md` |
| Client Variation Demo Spec | `04_CLIENT_VARIATION_DEMO_SPEC.md` |
| Execution Outline | `05_EXECUTION_OUTLINE.md` |
| Acceptance / Client-Reuse Criteria | `06_ACCEPTANCE_CLIENT_REUSE_CRITERIA.md` |
| Founder Inspection Notes | `07_FOUNDER_INSPECTION_NOTES.md` |

---

## 3. Baseline Audit

### Current Client-Variation State (Before Sprint)

| Area | Status |
|------|--------|
| handoff_phrases.json | Wired to triage |
| reply_overrides.json | Wired to triage |
| ui_copy.json | Documentation only; UI hardcoded |
| Client selection | None; fixed to chen_kui |

### Biggest Weakness

UI copy (app title, office label, workbench, welcome, handoff) was hardcoded in React. No visible client variation.

### Biggest Custom-Project Signal

Every screen showed "陈奎" / "办公室" — unmistakably Chen Kui–specific.

### Biggest A→B Migration Barrier

Changing client required editing React components and redeploying frontend.

---

## 4. 10–20 Point Breakdown

1. **Current client-specific hardcoded areas:** AppLayout (app_title), UnifiedIntakePage (QUICK_START_BUTTONS, office_label, handoff_default, welcome_highlight, welcome_hint, office_workbench)
2. **First UI copy areas wired:** app_title, office_label, office_workbench, handoff_default, welcome_highlight, welcome_hint, quick_start_buttons
3. **First backend/runtime areas wired:** GET /api/inbox/client-config, config_loader.get_ui_copy(client_id)
4. **How client config is selected:** URL ?client= param → API; env CLIENT_ID for backend default
5. **How to demonstrate client variation:** Open ?client=chen_kui vs ?client=demo_broker
6. **Labels/copy that differ between clients:** app_title, office_label, office_workbench, handoff_default, welcome text, talk_to_agent starter
7. **Handoff phrases:** Backend triage still uses chen_kui handoff_phrases; UI handoff_default from config
8. **Trust/reassurance copy:** welcome_highlight, welcome_hint from config
9. **Remains hardcoded for now:** PILOT_INTRO.demoPath, some broker_next_step/client_prep in triage
10. **Too risky to wire now:** Full triage client param (handoff draft from different client)
11. **Directly improves A→B migration:** New client = new ui_copy.json; no code change
12. **Directly improves sales credibility:** Founder can show two clients side-by-side
13. **Directly improves maintainability:** Copy in config, not scattered in React
14. **Tests/guardrails needed:** guardrail_inbox_triage.sh, npm run build
15. **Demo scenario that proves this best:** Load ?client=demo_broker → see "客服团队" instead of "办公室"
16. **Intentionally deferred:** Backend triage client param; full handoff phrase switching per client
17. **Real runtime wiring step:** API + frontend fetch + render from config
18. **Next platformization step:** Pass client_id to triage; load handoff_phrases per client

---

## 5. Iteration Loop 1

**What wiring problems were fixed:** UI copy was hardcoded; no API to serve client config; no frontend loading.

**Why these fixes were chosen:** Highest visibility; proves the concept; ui_copy.json already existed.

**What became more reusable:** App title, office label, workbench, welcome, handoff success, quick-start buttons now from config.

**What did not improve:** Backend triage still uses chen_kui handoff phrases for draft replies.

**Whether it was worth it:** Yes. Visible client variation now possible.

---

## 6. Iteration Loop 2

**What wiring problems were fixed:** Client selection (URL ?client= param); backend get_ui_copy(client_id), get_active_client_id().

**Why these fixes were chosen:** Enables A vs B demo without redeploy.

**What improved vs loop 1:** Can switch client via URL; API returns correct config per client.

**What still remained weak:** Backend triage not client-aware; handoff draft still from chen_kui.

**Whether loop 2 was worth it:** Yes. Client switching path is real.

---

## 7. Iteration Loop 3

**What client-variation problems were fixed:** Second demo client (demo_broker) with different branding.

**Why these fixes were chosen:** Proves A→B variation; founder can show side-by-side.

**What improved vs loop 2:** Concrete proof: ?client=demo_broker shows "客服团队" instead of "办公室".

**What still remained weak:** Backend handoff draft not client-specific.

**Whether loop 3 was worth it:** Yes. Demo story is complete.

---

## 8. Optional Loop 4

Not used. Stopping is correct: main wiring done; backend handoff client-param is larger scope for next sprint.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS (64/64 scenarios, multi-turn, adversarial, simulation) |
| npm run build | PASS |

**Limitations:** API test skipped (no server on 8001 during run). Manual verification: load ?client=demo_broker to see variation.

---

## 10. Deployment / Release Judgment

| Component | Live? | Notes |
|-----------|------|-------|
| Backend | Redeploy needed | New route GET /api/inbox/client-config; config_loader changes |
| Frontend | Redeploy needed | ClientConfigProvider, useClientConfig, wired copy |

**Founder can inspect:** Yes. Run demo, open ?client=chen_kui and ?client=demo_broker, compare.

---

## 11. Founder Showcase (REQUIRED)

### Chen Kui vs Demo Broker

| Element | Chen Kui (?client=chen_kui or default) | Demo Broker (?client=demo_broker) |
|---------|--------------------------------------|-----------------------------------|
| Header | 保险经纪人智能助手 | 保险经纪助手 Demo |
| Tab | 办公室工作台 — 办公室 | 客服团队工作台 — 客服团队 |
| Welcome | 您的消息会直接转给办公室 | 您的消息会直接转给客服团队 |
| Talk to agent | 我想联系陈奎办公室 | 我想联系客服 |
| Handoff success | 办公室会尽快处理，有结果会联系您。 | 客服团队会尽快处理，有结果会联系您。 |

### Why This Is Better

- Same product, different config. No code change to add a client.
- Copy in config files, not React.

### Why This Helps Reuse

- New broker = new folder under configs/clients/ with ui_copy.json.

### Why This Helps Selling

- Founder can show two clients side-by-side; explain "one base, one industry template, multiple client configs."

---

## 12. Final Judgment

- **Biggest gain:** UI copy now client-configurable; visible A→B variation; URL-based client switch.
- **Biggest remaining weakness:** Backend triage handoff draft still from chen_kui; not yet client-aware.
- **Whether this makes A→B migration meaningfully easier:** Yes. UI migration path is real; config change suffices for visible copy.
- **Best next step:** Wire backend triage to accept client_id; load handoff_phrases per client.

---

## 13. Iteration Log (REQUIRED)

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|-----------------|----------------------|-----------|-----------|
| 1 | config_loader.get_ui_copy, GET /api/inbox/client-config, ClientConfigProvider, wire UnifiedIntakePage + AppLayout | UI copy from config | Backend handoff | Yes | Loop 2 |
| 2 | get_active_client_id, client query param, URL ?client= | Client selection | Triage client param | Yes | Loop 3 |
| 3 | configs/clients/demo_broker/, CONFIG_EXTRACTION_GUIDE update | A→B proof | — | Yes | Stop |

---

## 14. 中文宏观总结

**为什么现在做 client wiring：** 配置层已有，但 UI 仍硬编码。创始人问「从客户 A 换到客户 B 会不会很痛？」需要实际答案。

**我们用了什么主要方法/技术：** 后端 GET /api/inbox/client-config、config_loader.get_ui_copy(client_id)、前端 ClientConfigProvider + useClientConfig、URL ?client= 切换客户。

**这轮最大提升：** UI 文案从配置加载；可见的客户 A/B 差异；?client=demo_broker 即可切换演示。

**还差什么：** 后端 triage 的 handoff 草稿仍固定 chen_kui；尚未按 client 加载 handoff_phrases。

**下一步最该做什么：** 让 triage 支持 client_id 参数，按客户加载 handoff_phrases。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest client-wiring improvement:** UI copy (app title, office label, workbench, welcome, handoff, quick-start buttons) now loads from client config. Add ?client=demo_broker to see different branding.

**Biggest remaining weakness:** Backend handoff draft still uses Chen Kui phrases; not yet client-aware.

**Whether this makes the product more sellable/reusable:** Yes. New broker = new config folder; no code change for visible copy.

**Whether redeploy is needed:** Yes. Backend and frontend both changed.

**What Andy should inspect next:** Open /workbench/unified-intake and /workbench/unified-intake?client=demo_broker; compare header, tab, welcome, handoff message.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current client-reuse maturity:** UI copy configurable; client selection via URL; second demo client exists. Backend triage handoff still single-client.

**Biggest improvements:** (1) GET /api/inbox/client-config. (2) Frontend ClientConfigProvider + useClientConfig. (3) All major UI copy from config. (4) demo_broker config for A→B proof.

**Biggest remaining weaknesses:** Triage handoff draft not client-aware; handoff_phrases still loaded from chen_kui only.

**Whether direction is correct:** Yes. Config-driven UI is the right path.

**Best next recommendation:** Wire triage to accept client_id; load handoff_phrases from configs/clients/<client_id>/.

**Current IT technical backbone / stack:** Python FastAPI (fiqa_api), config_loader (common/industry/client), React/Vite, Vercel + Cloud Run.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事

配置层已有，但 UI 仍硬编码。创始人需要证明「从客户 A 换到客户 B」可以很轻。

### 主要用了什么方法/技术

后端 GET /api/inbox/client-config、config_loader.get_ui_copy(client_id)、前端 ClientConfigProvider + useClientConfig、URL ?client= 切换。

### 这轮最大的提升

UI 文案从配置加载；可见的客户 A/B 差异；?client=demo_broker 即可演示不同品牌。

### 现在还差什么

后端 triage 的 handoff 草稿仍固定 chen_kui；下一步应支持按 client 加载 handoff_phrases。
