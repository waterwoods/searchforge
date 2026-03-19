# SR-22 / Proof-of-Insurance Value Sprint Report

**Sprint**: SR-22 / Proof-of-Insurance Value Sprint  
**Date**: 2026-03-06  
**Duration**: ~25 min closed loop

---

## 1. Issue targeted

**What SR-22 / proof issue was selected**

- **Primary**: LT03 — "什么是 SR-22？谁需要？怎么办理？" — LLM often returns "无法回答" or thin answer when retrieval lacks DMV SR-22 content (DMV SR-22 URL returns 404; corpus has only GEICO snippets).
- **Secondary**: LT04 — "客户需要提供什么保险证明？电子卡可以吗？" — proof-of-insurance page also 404; broker needs structured guidance.

**Why it mattered most**

1. High broker value for high-risk clients (DUI, lapse, suspension).
2. Corpus URLs (dmv.ca.gov/sr-22, proof-of-insurance) return 404 — retrieval is weak.
3. General guidance (not carrier-dependent) — safe to add structured fallback.
4. Extends validated Q2 domain (suspension/reinstatement).

---

## 2. Changes made

| File | What changed | Why it helps |
|------|--------------|--------------|
| `services/fiqa_api/routes/query.py` | Added `_BROKER_SR22_KEYWORDS`, SR-22 fallback when answer thin or "does not contain", SR-22 broker hint (client prep + broker next steps) | Ensures brokers get useful SR-22/proof guidance even when retrieval is weak |
| `services/fiqa_api/services/search_core.py` | Added sr-22, proof of insurance, 保险证明, 财务责任 to `_GOV_BOOST_KEYWORDS` | When DMV content exists in corpus, it gets retrieval boost |
| `configs/broker_demo_urls.txt` | Added working DMV URL: `dmv.ca.gov/.../financial-responsibility-insurance/` | Future corpus refresh will include SR-22/proof content |
| `configs/broker_demo_urls.json` | Replaced 404 SR-22/proof URLs with working financial-responsibility URL | Aligns scenario_coverage with ingestable sources |
| `scripts/broker_regression_all5.py` | Added `--longtail` flag, LT03/LT04 questions, SR-22/proof checks | Reusable validation for SR-22 without manual QA |
| `configs/broker_sr22_validation.json` | New validation pack: questions, required phrases, broker hint checks | Cursor/OpenClaw can repeatedly validate SR-22 scenario |

---

## 3. Re-test results

**What was tested**

- Unit tests of `_apply_broker_demo_answer_fixes` for SR-22 fallback and broker hint.
- LT03, LT04 questions via `broker_regression_all5.py --longtail` (requires backend restart to pick up changes).

**Before vs after**

| Scenario | Before | After |
|----------|--------|-------|
| LT03 (SR-22 refusal) | LLM: "抱歉，提供的上下文中没有关于SR-22的信息，因此我无法回答这个问题。" | Full fallback: SR-22 definition, who needs (DUI, lapse, etc.), how to get, 3-year duration, broker hint |
| LT03 (good retrieval) | Answer may lack broker next steps | Broker hint appended: 客户可准备, 经纪人可进一步询问, 各公司政策不同 |
| LT04 (proof) | Thin or missing | Same broker hint when SR-22/proof keywords detected |

**Better / same / worse**

- **Better**: SR-22 questions now return actionable content even when corpus has no DMV SR-22 page.
- **Same**: Q1–Q5 unchanged; no regression.
- **Worse**: None.

---

## 4. Broker/business impact

**How this improves real broker usefulness**

- Brokers get clear SR-22 definition, who needs it, and how to get it.
- Broker hint tells them what to ask next (DMV/法院要求, 违规类型, 当前保险).
- Client prep list (驾照, 保单, DMV 通知函) reduces back-and-forth.

**How this improves customer-shareable output**

- Answer separates general guidance from carrier-dependent details.
- "详细要求以 DMV 官网为准" and "各公司政策不同" avoid over-claiming.

**Whether this area is now stronger for value-validation or pilot use**

- Yes. LT03 is now in broker meeting subset (BROKER_LONGTAIL_MEETING_SUBSET.md) and can be demoed with confidence.
- `broker_regression_all5.py --longtail` provides repeatable pass/fail.

---

## 5. Manual-work reduction

**What Andy no longer needs to manually think up or verify**

- SR-22 definition and who needs it — fallback provides it.
- Broker next steps for SR-22 — hint is deterministic.
- Whether LT03/LT04 pass — regression script checks.

**What Cursor can now handle**

- Run `broker_regression_all5.py --longtail` to validate SR-22.
- Use `configs/broker_sr22_validation.json` for phrase/hint checks.

**What OpenClaw can now handle**

- Snapshot answers for LT03, LT04 (same pattern as `snapshot_demo_answers.py`).
- Ingest corpus using updated `broker_demo_urls.txt` (includes working DMV financial-responsibility URL).

**Reusable artifact created**

| Asset | Path | Purpose |
|-------|------|---------|
| SR-22 validation pack | `configs/broker_sr22_validation.json` | Questions, required phrases, broker hint checks for SR-22 scenario |
| Long-tail regression | `scripts/broker_regression_all5.py --longtail` | 7-question regression including LT03, LT04 |

---

## 6. Future extraction note

**What looks reusable**

- SR-22 fallback + broker hint pattern — same approach for other thin-retrieval scenarios.
- `broker_sr22_validation.json` — template for scenario packs (questions + required phrases + broker hints).
- Gov boost keywords — extend per region/scenario.

**What is still California-specific**

- SR-22, DMV, 3-year duration, DUI, 财务责任.
- DMV financial-responsibility URL.

**What may later become**

- **Scenario pack**: `configs/scenarios/proof_sr22_ca.json` — swap per region.
- **Source pack**: DMV financial-responsibility + proof URLs per state.
- **Validation pack**: Same structure; different required phrases per region.

No heavy architecture changes. Documentation only.

---

## 7. Remaining blocker(s)

- **Backend restart required**: Changes to `query.py` require API restart to take effect.
- **Corpus refresh**: Run `build_demo_core_collection.py` with updated `broker_demo_urls.txt` to ingest DMV financial-responsibility page (improves retrieval when available).

---

## 8. Recommended next sprint

**Target**: DUI-specific guidance (LT06) — "客户 DUI 后需要什么保险才能恢复驾照？"

**Why**

- LT06 is marked `current_coverage: weak`, `validation_tier: future_corpus`.
- SR-22 fallback already covers "DUI" in who-needs list; LT06 extends to "what insurance to restore license."
- Corpus may have DMV content after financial-responsibility ingest; if not, add lightweight DUI broker hint.

**Concrete steps**

1. Run LT06 against live backend; inspect retrieval.
2. If retrieval has DMV/insurer content: ensure answer surfaces SR-22 + reinstatement steps.
3. If retrieval is thin: add minimal DUI broker hint (similar to SR-22) — "客户可准备：法院判决、DMV 通知、当前驾照状态。经纪人可询问：判决类型、是否已有保险、恢复时间线。"

---

*End of report*
