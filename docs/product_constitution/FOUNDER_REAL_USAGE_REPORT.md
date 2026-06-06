# P16-H Phase 1 — Founder Real Usage Report

**Date:** 2026-05-31  
**Sprint:** P16-H — Founder Real Usage + UI Simplicity Review  
**Method:** Act as Andy — local demo (`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, API `:8001`, UI `:5173`), code walkthrough, API scenario validation, cross-check with P16-C/P16-G browser audits  
**Constraint:** Evaluation only — no features built

---

## Executive Summary

The **engine works**. Sprint A front-door fixes are **real** in product_only builds: broker tab default, wayfinding banner, inline practice scenarios, demo queue progress, engineer chrome hidden. Andy can reach cancellation value in under 5 minutes **if he knows to paste on 办公室工作台**.

Remaining friction is **not triage quality** — it is **story misalignment** (Add-Car copy everywhere), **visual density** (too many cards before the paste box), and **case-detail overload** (English "Case", nested collapses, buried follow-up paste). These would cause Andy to hesitate before sending the URL to Chen Kui unsupervised.

---

## Scenario A — Cancellation Notice

**Input:** `Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.`

### What feels good

| Signal | Evidence |
|--------|----------|
| Fast triage | API 200 in &lt;1s locally; `cancellation_warning`, `critical` |
| Actionable broker step | "Confirm whether cancellation is still active… call or text client today" |
| Editable draft | English draft matches English notice — copy-ready with minor edits |
| Practice shortcut | Inline「取消/付款风险」button pre-fills paste area |
| Demo queue path | 加载演示队列 → progress string → auto-open cancellation case (code + P16-C) |
| Trust | Wayfinding banner +「不自动对外发送」+ loading copy「首次分析约30秒」 |

### What feels confusing

| Issue | Impact |
|-------|--------|
| **Two tabs still visible** — 客户报送 vs 办公室工作台 | Andy might wonder which door is "real" for paste |
| **Tab suffix** still says「加车旗舰路径 · 与客户报送同一服务记录」 | Contradicts cancellation-first trial story |
| **Header tagline**「加车报价为当前旗舰流程」 | Chen Kui trial is cancellation wedge — cognitive dissonance |
| **Left queue + right paste** split | Unclear whether to paste first or load demo queue first on Day 0 |
| **「开始整理」→「已打开」** when case selected | Button disabled state not explained until you try |
| English **"Case 整理明细"** in case detail | Feels unfinished / engineer artifact to Chinese broker |

### What feels slow

| Step | Time | Notes |
|------|------|-------|
| Demo queue (13 seeds) | 15–30s | Progress shown — acceptable with copy |
| First cold paste (embedding warm) | up to 30s | Loading message helps; still feels long on phone |
| Scroll to draft after triage | 2–3 scrolls | Case detail card is long; draft not pinned above fold |

### What feels unnecessary

- **练习场景** card *and* **快速体验** demo queue card *and* pilot intro — three onboarding surfaces
- **服务记录编号** monospace block + hint about customer portal parity
- **Case 整理明细** nested collapses for tags already visible in glance summary
- **复制摘要** vs **复制客户草稿** — two copy buttons; broker only needs draft 90% of time
- Status radio group (新建/审核中/等客户/完成) on every case — CRM noise for Day 1

### What would make Andy stop using it

1. Opening **客户报送** tab first (by accident or shared link) and seeing Add-Car wall — "this isn't for my cancellation workflow"
2. **30s silent wait** on cold start without loading message (fixed in product_only — must stay deployed)
3. **Can't find follow-up paste** after first case — would revert to WeChat-only
4. **English draft on Chinese client thread** without obvious edit prompt — loses trust on real WeChat paste
5. Sending URL to assistant who hits **Vercel SSO** before product (deployment, not UI — but kills adoption)

---

## Scenario B — Missing Document

**Input:** `Underwriting requested driver's license copy. Client says I already sent it last week.`

### What feels good

| Signal | Evidence |
|--------|----------|
| Correct classification | `missing_document`, `medium` |
| Broker step | "Verify whether customer-resubmitted items were received" |
| Draft tone | "verify what is on file… you usually do not need to resend everything" — saves re-asking |
| Collected fields | `requested_driver_license`, `customer_says_sent_driver_license`, `already_sent_claimed` |
| Append flow | API PASS on append-message; UI has「追加客户补充」in case detail |
| Queue filter |「需今天处理」/「24小时内」broker-safe filters in product_only |

### What feels confusing

| Issue | Impact |
|-------|--------|
| **Follow-up paste buried** below case sheet, collapses, tags | Andy won't find「追加客户补充」without training |
| **「续接此处」** blue box + **「最近更新」** box — duplicate concepts | Which one is the action? |
| Re-open from queue vs paste new message | Two paths to same outcome; no single "add client reply" CTA above fold |
| `still_needed: verify_carrier_received` | Jargon — broker thinks in "check carrier portal" not field names |

### What feels slow

- Opening case from queue → full GET → render long detail card before append area visible
- No inline "client said they already sent" quick action on queue card

### What feels unnecessary

- Add-car-specific submission snapshot collapse on non-add-car cases (hidden — good)
- **waiting_on** dropdown + **next_contact_by** date field on Day 1 — assistant CRM features
- Multiple activity-type tags (`刚用客户新消息更新`, `续接此处`, `最近更新`)

### What would make Andy stop using it

1. Can't append client reply in &lt;10s — faster to re-type in WeChat
2. Draft says "verify on file" but UI doesn't show **where** broker should look (carrier name missing from glance on some messages)
3. Queue card preview truncates at 52 chars — hard to distinguish similar missing-doc cases

---

## Scenario C — Add-Car Request

**Input:** `我想加一辆2020 Honda Civic，主要给我儿子开，请问保费多少？`

### What feels good

| Signal | Evidence |
|--------|----------|
| Structured extraction | year, make_model, primary_driver collected |
| Chinese draft | Bullet list with 待补充 fields — matches WeChat style |
| Still-needed clarity | vin, zip, delivery_date surfaced |
| Practice button |「加车报价」loads seed text into paste area |
| Multi-turn engine | Guardrail PASS; conversation turns work on customer portal |

### What feels confusing

| Issue | Impact |
|-------|--------|
| **Customer portal** is Add-Car-first; **broker workbench** is paste-first | Two products in one URL — Andy demoing to Chen Kui sends mixed signal |
| Category `customer_question` not `add_car` | Label mismatch vs broker mental model |
| Add-car guidance in case detail references「旗舰路径」| Over-engineered for a simple quote paste |
| **客户报送** tab shows 6 category buttons + structured form + flow track | Completely different UX than broker paste path |

### What feels slow

- Add-car on **customer portal** = multi-turn collection (by design) — fine for end customer, slow for broker who just wants a draft
- Broker paste path is faster (single paste → draft) — but not obvious that's the intended broker workflow

### What feels unnecessary

- **IntakeFlowStepTrack** (3-step progress bar) on customer entry for broker-led trial
- **加车报价 · 结构化报送** collapse with 5 fields when paste works in one shot
- Add-car status strip, record summary rail, boundary hints — built for portal GTM, not Chen Kui wedge

### What would make Andy stop using it

1. Chen Kui opens **客户报送**, sees Add-Car form, ignores workbench entirely
2. Broker paste gives draft but **no quote number** — expected, but UI doesn't set expectation ("办公室仍需算价")
3. Andy spends demo time explaining two tabs instead of one paste loop

---

## Cross-Scenario Founder Journey (Andy as primary user)

| Stage | Works? | Friction |
|-------|--------|----------|
| Open trial URL | ✅ Broker tab default | Add-Car header/tagline |
| Find paste | ✅ &lt;10s with banner | 3 cards above paste |
| First paste → draft | ✅ Engine strong | Scroll to draft; English on EN notices |
| Demo queue Day 0 | ✅ Progress + auto-open | 15–30s wait |
| Copy draft to WeChat | ✅ Copy button | Two copy buttons compete |
| Second case same day | ⚠️ | Queue grows; filters only after cases exist |
| Follow-up append | ⚠️ | Buried; needs training |
| Send URL to assistant | ❌ Vercel SSO | Deployment blocker |

---

## Andy Verdict (Phase 1)

**Would Andy use this tomorrow for his own triage?** YES — supervised, on 办公室工作台, for cancellation + missing doc.

**Would Andy send unsupervised URL to Chen Kui today?** NO — Add-Car copy pollution and case-detail density still fail the "no founder translation" test for a non-technical broker owner.

**Highest friction to remove before Chen Kui Day 0:**
1. Align all visible copy to cancellation-first (ui_copy.json)
2. Hide or demote 客户报送 tab in trial mode
3. Pin「复制客户草稿」above fold; collapse Case 整理明细 by default
4. Promote「追加客户补充」to primary action when case open

---

*End of P16-H Phase 1 — Founder Real Usage Report*
