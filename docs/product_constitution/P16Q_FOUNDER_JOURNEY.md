# P16-Q Phase 2 — Founder Journey Simulation

**Date:** 2026-06-01  
**Persona:** Andy (founder)  
**Method:** Local API + code-path walkthrough (`product_only` on :5173, full dev on :5174 for customer); Production browser snapshot; synthesis with P16-J walkthrough  
**Path:** Customer Entry → Submit → Broker Queue → Draft → Follow-up → Reopen  
**Constraint:** Cursor browser cannot reach `127.0.0.1`; deployed URLs used where local UI blocked

---

## Journey Map

```
Customer Entry (full dev, local P16-O uncommitted)
    → Submit / handoff
        → Broker Queue (product_only local OR Preview after SSO)
            → Draft + copy
                → Follow-up append
                    → Reopen from queue
```

---

## Step 1 — Customer Entry

**Surface:** `CustomerEntryTab` on `:5174` (full dev, P16-O local diff)

| Observation | Type |
|-------------|------|
| Empty landing: one headline, one textarea, one send button, trust line | ✅ Delight (P16-O) |
| Footer links only for 人工 / 更多类型 / 逐项填写 | ✅ Progressive disclosure |
| Still 4 tabs in chrome (客户报送, 我的办理, 办公室工作台, 场景仿真) | ⚠️ Confusion — customer sees broker/simulation |
| Dark app header + Chen Kui branding | ⚠️ Confusion — "is this a login?" |
| **Production URL** still shows 3-button grid + 办理加车报价 hero | ❌ **Deployed reality ≠ local P16-O** |

**Friction:** Andy must know to test customer on `:5174` without `product_only`, not the URL he would send a broker.

**Delay:** None locally once correct port/env chosen.

**Unexpected:** P16-O improvements exist only in working tree — not in Preview or Production bundles.

---

## Step 2 — Submit

**Action:** Type cancellation notice → triage → optional handoff confirm

| Observation | Type |
|-------------|------|
| Message-first: no category pick required (P16-O) | ✅ |
| Flow track appears **after** first send | ✅ |
| Add-car path still exposes record rail + handoff confirm step | ⚠️ Medium friction |
| Contact-only gap: chat phone **then** 正式提交办公室 — two steps | ⚠️ Confusion |
| API triage (cancellation) | ✅ PASS in `demo_quick_validate.sh` |
| OpenAI quota 429 → rules fallback | ⚠️ Delay risk on edge phrasing |

**Friction:** Dual handoff path when only name/phone missing.

**Delay:** ~2–5s rules triage locally; up to ~30s if embedding path hit (not on intake_core).

---

## Step 3 — Broker Queue

**Surface:** `BrokerWorkbenchTab` product_only (`:5173` or Preview post-SSO)

| Observation | Type |
|-------------|------|
| Default single surface — no customer tab | ✅ |
| Queue title 待处理; filters 全部 / 需今天处理 / 24小时内 | ✅ |
| Empty queue until paste or 加载演示队列 | ⚠️ "Is it broken?" moment |
| 快速体验 card + paste card compete on narrow viewport | ⚠️ Confusion |
| Production: cannot reach broker tab via URL param | ❌ Deploy bug for wrong URL |

**Friction:** Demo queue vs real paste — two onboarding paths.

**Delay:** Demo queue load ~10–20s for 13 seeds (progress shown).

---

## Step 4 — Draft

**Action:** Open cancellation case → read glance → 复制客户草稿

| Observation | Type |
|-------------|------|
| Draft expanded by default | ✅ Delight |
| Cancellation category + urgency + broker_next_step | ✅ North Star moment |
| English paste → English draft | ⚠️ Friction for WeChat-first office |
| Long cases: scroll to draft | ⚠️ Delay |
| 不自动对外发送 trust visible | ✅ |

**Friction:** Draft language mismatch on mixed Chinese threads.

---

## Step 5 — Follow-up

**Action:** 追加客户补充 near glance → append API

| Observation | Type |
|-------------|------|
| Append promoted (P16-I) | ✅ |
| Guardrail append/boundary copy PASS | ✅ |
| Separate "new paste" vs "append on open case" mental models | ⚠️ Confusion |
| Follow-up **plan** (waiting_on, next_contact_by) still lower in detail | ⚠️ Delay finding field |

**Friction:** Assistant/broker must learn append vs new intake.

---

## Step 6 — Reopen

**Action:** Close browser → reopen queue → select same case

| Observation | Type |
|-------------|------|
| Local persistence works | ✅ |
| Case ID monospace — engineer signal | Minor |
| Preview URL reopen | ❌ **Not tested** — SSO + Andy gate open |
| Production reopen | ❌ Wrong UI; not validated |
| Customer 我的办理 resume | ✅ Works in full dev (P16-O lighter detail) |

**Unexpected:** Founder can complete loop locally; **cannot prove same loop on URL sent to Chen Kui**.

---

## Confusion / Friction / Delay Summary

| Category | Count | Top items |
|----------|-------|-----------|
| **Confusion** | 9 | Deploy ≠ local P16-O; 4 tabs on customer dev; demo vs paste; append vs new paste; contact-only dual submit |
| **Friction** | 7 | English drafts; empty queue; mobile card order; broker chrome on customer URL |
| **Delay** | 4 | Demo queue seed; 30s triage copy; scroll on long cases; SSO before any Preview step |
| **Unexpected** | 5 | P16-O not deployed; Production ignores `?tab=broker`; rules fallback only (429); browser can't hit localhost |

---

## Founder Reality Check

| Question | Answer |
|----------|--------|
| Can Andy complete the loop today? | **Yes — locally**, with env/port knowledge |
| Can Andy complete on Preview URL? | **Unknown — not logged; blocked at 401 without auth** |
| Can Andy send customer the same UX he tested? | **No — customer P16-O not deployed; no customer-only public URL** |
| Would Andy ship this URL tomorrow? | **No** — same blockers as P16-J/L |

---

*End of P16-Q Phase 2 — Founder Journey Simulation*
