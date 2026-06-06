# Add-Car Identity + Contact Lite Report

**Sprint:** Add-Car Identity + Contact Lite  
**Completed:** 2026-03-19

---

## 1. Sprint theme

- **What was chosen:** Add lightweight customer identity/contact (name, phone) to the add-car flow so the case feels like a real lead, not an anonymous chat.
- **Why now:** Add-Car Real Intake Lite V1 delivered quote-ready visibility but deferred name/phone. Founder judgment: add-car still lacks enough "real customer" feel for Chen Kui trial.

---

## 2. Document set created

1. 01_ADD_CAR_IDENTITY_CONTACT_LITE_BLUEPRINT.md
2. 02_MINIMAL_CONTACT_FIELD_SPEC.md
3. 03_QUOTE_READY_CONTACT_READINESS_SPEC.md
4. 04_BROKER_CONTACT_VISIBILITY_SPEC.md
5. 05_EXECUTION_OUTLINE.md
6. 06_ACCEPTANCE_IDENTITY_CONTACT_CRITERIA.md
7. 07_FOUNDER_INSPECTION_NOTES.md

---

## 3. Baseline audit

**Strongest current parts:**
- Quote-ready status, collected/still_needed for vehicle fields
- Case store already has customer_name, customer_phone; PATCH /customer exists
- Add-car flow and broker handoff logic solid

**Biggest anonymous/fake-feeling weakness:** No name/phone collection; broker gets vehicle data but not who to call.

**Biggest broker follow-up gap:** Broker must re-ask "who are you?" and "how do I call you?" after handoff.

**Biggest customer-trust gap:** Customer doesn't see that identity is being captured; feels like generic chat.

---

## 4. 10–20 point breakdown

1. **Why current add-car still feels anonymous:** No name/phone; case is vehicle-only.
2. **Minimum useful contact info:** Name + phone.
3. **Required fields:** Name, phone (for follow-up).
4. **Optional fields:** Email (deferred to V2).
5. **Why email can be optional:** Chen Kui uses WeChat/phone first; email is secondary.
6. **How chat populates contact fields:** Regex extraction from customer messages (我是X, 我姓X, call me X, phone patterns).
7. **How contact fields appear in UI:** Contact block in Workbench (Name: X / Phone: Y or "Name needed" / "Phone needed").
8. **How quote-ready interacts with missing contact:** Case can be quote_ready with still_needed: name, phone.
9. **When case is actionable without full contact:** Broker can run quote; broker_next_step says "Confirm name and phone for follow-up."
10. **What broker sees:** Contact block, collected/still_needed including name/phone.
11. **What still-needed shows:** name, phone as orange tags when missing (for add-car quote-ready/almost-ready).
12. **What most reduces broker rework:** Extracted contact when customer volunteers it; clear still-needed when not.
13. **What most improves customer trust:** Visible contact capture; feels like real intake.
14. **What most improves realism:** Name/phone in case; broker knows who to call.
15. **What remains deferred:** Email, verification, full CRM.
16. **What V2 can add:** Email extraction, contact prompt in handoff reply, inline edit in Workbench.
17. **What simulations are needed:** MT46–MT50 (name/phone in chat, missing, partial).
18. **What founder should manually test:** 4–6 Vercel flows (see Founder test list).

---

## 5. Iteration loop 1

**What was fixed:** Minimal contact structure — extraction, collected/still_needed, case persistence.

**Why:** Highest-value slice; name/phone are minimum for real lead feel.

**What now feels more real:** When customer says "我是张三 电话 626-555-1234," case has name and phone; broker sees who to call.

**What did not improve:** Contact block was not yet in UI (added in Loop 2).

**Whether it was worth it:** Yes.

---

## 6. Iteration loop 2

**What was fixed:** Broker contact visibility — Contact block in Workbench; broker_next_step contact hint when quote-ready but contact missing.

**Why:** Broker needs to see contact at a glance; broker_next_step must guide when contact is thin.

**What improved vs loop 1:** Broker sees Name/Phone or "needed"; broker_next_step includes "Confirm name and phone for follow-up."

**What still remained weak:** No inline edit for contact (PATCH exists; UI edit deferred).

**Whether it was worth it:** Yes.

---

## 7. Iteration loop 3

**What was hardened:** Add-car contact simulations MT46–MT50 (name/phone in same turn, quote-ready no contact, name only, phone only, vehicle first then contact).

**Why:** Regression coverage for identity/contact-lite behavior.

**What improved vs loop 2:** 50/50 multi-turn sims pass; contact scenarios validated.

**What still remained weak:** Extraction is heuristic; edge cases (e.g. "我电话是 626" without full number) may miss.

**Whether it was worth it:** Yes.

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_multi_turn_simulations.py | 50/50 pass |
| ui build | Success |

**Limitations:** API append test fails when server not running (pre-existing). Extraction is regex-based; complex name/phone phrasing may not match.

---

## 9. Deployment / release judgment

- **Backend:** Changed (triage, case_store). Redeploy needed.
- **Frontend:** Changed (UnifiedIntakePage, inboxTriage API). Redeploy needed.
- **Founder can inspect:** After redeploy, run founder tests on Vercel.

---

## 10. Founder manual test list

1. **Add-car + name/phone in chat:** "我想加车" → "2024 Tesla Model Y 90210 下周提车 我是李四 电话 310-123-4567" — expect name, phone in case, Contact block shows values.
2. **Add-car quote-ready, no contact:** "我想加车" → "2024 BMW X5 90210 下周提车" — expect Quote-ready, Contact block shows "Name needed", "Phone needed", broker_next_step mentions contact.
3. **Add-car name only:** "我想加车 2024 Honda Accord 90210 下周提车 我姓王" — expect name in collected, phone in still_needed.
4. **Workbench contact block:** Create add-car case, open in Workbench — expect Contact section with name/phone or "needed".
5. **Manual edit:** PATCH /api/inbox/cases/{id}/customer with name/phone — expect case shows updated values (or use future UI edit).
6. **Simulations:** Run `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — expect 50/50 pass.

---

## 11. Final judgment

- **Biggest gain:** Name/phone extraction and visibility; add-car feels like real lead capture.
- **Biggest remaining weakness:** Extraction is heuristic; no inline edit in Workbench yet.
- **Real enough to show Chen Kui:** Yes.
- **Best next step:** Deploy; run founder tests on Vercel; consider inline contact edit in V2.

---

## 12. 中文宏观总结

**为什么现在做这一轮：** 加车已有报价状态，但缺姓名/电话，经纪人无法直接联系客户，仍偏演示感。

**主要修了什么：** 姓名/电话提取、collected/still_needed 含 name/phone、case 持久化、Workbench 联系块、broker_next_step 联系提示、5 个加车联系模拟。

**最大提升是什么：** 客户说姓名/电话时自动填入；经纪人可见联系信息或「待确认」。

**还差什么：** 提取为规则式，复杂表述可能漏；Workbench 暂无内联编辑。

**下一步最该做什么：** 部署后 Vercel 测试；V2 可加联系编辑、邮件、更智能提取。

---

## 13. COPY/PASTE FOUNDER BLOCK

Add-Car Identity + Contact Lite Complete. Biggest improvement: Name/phone extracted from chat and visible in Workbench. Biggest weakness: Extraction heuristic; no inline edit yet. Redeploy: Yes (backend + frontend). Test: 我想加车 → 2024 Tesla Model Y 90210 下周提车 我是李四 电话 310-123-4567 — expect Contact block with name/phone.

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事

加车已有报价状态，但缺姓名/电话，经纪人无法直接联系客户，陈奎试跑前需要更真实接单体验。

### 主要用了什么方法/技术

姓名/电话正则提取、collected/still_needed 含 name/phone、case 持久化、Workbench 联系块、broker_next_step 联系提示、5 个加车联系模拟。

### 这轮最大的提升

客户说姓名/电话时自动填入 case；经纪人可见联系信息或「待确认」，减少二次询问。

### 现在还差什么

提取为规则式，复杂表述可能漏；Workbench 暂无内联编辑；V2 可加邮件、更智能提取。
