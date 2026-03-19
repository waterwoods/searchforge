# Broker Long-Tail Question Expansion Report

**Sprint**: Broker Long-Tail Question Expansion Sprint  
**Date**: 2026-03-06  
**Focus**: California Auto Insurance Broker Assistant — realistic long-tail coverage

---

## 1. Long-tail question categories

### Identified categories

| Category | Description | Why it matters |
|----------|-------------|----------------|
| **Policy minimums / coverage** | 15/30/5, liability limits, collision vs comprehensive, lender requirements | Core broker work; clients constantly ask "what do I need?" |
| **Registration / suspension / reinstatement** | Why suspended, how to restore, fees, VIN/insurer mismatch | Q2 validated; extensions (why suspended, proof) are high-frequency |
| **Proof of insurance / SR-22** | Proof requirements, electronic cards, SR-22 for high-risk | High-risk clients (DUI, lapse) are common broker cases |
| **Discounts / savings** | Good driver, multi-car, defensive driving, rate factors | Q4 validated; carrier-specific details are long-tail |
| **Accident / claims** | Flow, timing, fault, own vs other party | Q5 validated; timing (24h?) and fault scenarios are follow-ups |
| **Compliance / complaints** | License lookup, CDI complaints | Q3 validated; complaints are adjacent |
| **Documentation / client prep** | What to bring for quote, NAIC, etc. | Reduces back-and-forth; broker efficiency |
| **Common misunderstandings** | "I drive little, why high?" "Why do quotes vary?" | Client objections; broker needs talking points |
| **Edge cases** | Out-of-state move, non-owner policy, DUI, gap insurance | Less frequent but high-stakes when they occur |

### Why these categories

- **Policy minimums / coverage**: Already strong (Q1). Extensions (15/30/5 explanation, collision vs comprehensive) are one-click answers.
- **SR-22 / proof**: DMV has pages; corpus includes them. High-value for brokers serving high-risk clients.
- **Discounts**: Q4 covers categories; carrier-specific percentages and acceptance are long-tail.
- **Claims timing**: Q5 covers flow; "report within 24h" and fault scenarios are common follow-ups.
- **Misunderstandings**: Brokers need quick, authoritative answers to deflect objections.
- **Edge cases**: Non-owner, out-of-state, DUI — lower frequency but high impact when asked.

---

## 2. Structured long-tail question set

**Artifact**: `configs/broker_longtail_questions.json`

20 realistic broker questions with metadata:

| ID | Category | Frequency | Current coverage | Validation tier | Carrier-dependent |
|----|----------|-----------|------------------|-----------------|-------------------|
| LT01 | policy_minimums | high | well | core | no |
| LT02 | policy_minimums | high | partial | secondary | yes |
| LT03 | proof_sr22 | high | partial | core | no |
| LT04 | proof_sr22 | high | partial | secondary | no |
| LT05 | registration | high | well | core | no |
| LT06 | proof_sr22 | medium | weak | future_corpus | yes |
| LT07 | discounts | high | partial | secondary | yes |
| LT08 | discounts | medium | partial | secondary | yes |
| LT09 | claims | high | weak | future_corpus | yes |
| LT10 | claims | high | partial | secondary | yes |
| LT11 | compliance | medium | partial | future_corpus | no |
| LT12 | documentation | high | partial | secondary | yes |
| LT13 | misunderstandings | high | partial | secondary | yes |
| LT14 | edge_cases | medium | weak | future_corpus | yes |
| LT15 | edge_cases | medium | weak | future_corpus | yes |
| LT16 | policy_minimums | high | well | core | no |
| LT17 | misunderstandings | high | partial | secondary | yes |
| LT18 | discounts | medium | weak | future_corpus | yes |
| LT19 | policy_minimums | high | partial | secondary | yes |
| LT20 | documentation | low | weak | future_corpus | no |

### Sample questions (Chinese)

- **LT01**: 15/30/5 具体是什么意思？客户问我要解释清楚。
- **LT03**: 什么是 SR-22？谁需要？怎么办理？
- **LT05**: 客户的车注册被暂停了，但他说已经买了保险，为什么还会被停？
- **LT09**: 出险后多久内必须报案？24 小时？
- **LT13**: 客户说：我开车很少，为什么保费还这么高？

---

## 3. Practical validation structure

### 3.1 Next broker value-validation meeting (陈魁)

**Use 5 core + 3 long-tail** — keep demo tight, add realism:

| # | Question | Source | Purpose |
|---|----------|--------|---------|
| 1–5 | Q1–Q5 (existing) | broker_regression_all5 | Validated baseline |
| 6 | LT03: SR-22 是什么？谁需要？ | longtail | High-value, general |
| 7 | LT05: 为什么买了保险还被停？ | longtail | Extends Q2 |
| 8 | LT16: 碰撞险和综合险区别？ | longtail | Extends Q1 |

**Do not** add all 20. Goal: prove product handles 8 realistic scenarios without overwhelming.

### 3.2 Future product testing

**Cursor / regression script** can run:

- **Core validation**: Q1–Q5 (existing) + LT01, LT03, LT05, LT16
- **Secondary validation**: LT02, LT04, LT07, LT10, LT12, LT13, LT17, LT19

**Suggested**: Extend `broker_regression_all5.py` with optional `--longtail` flag that adds LT01, LT03, LT05, LT16. No new checks initially — just run and log pass/fail.

### 3.3 Future corpus expansion

**Target for corpus work** (weak or missing today):

| ID | Question | Gap type |
|----|----------|----------|
| LT06 | DUI 后需要什么保险 | SR-22 + carrier who writes |
| LT09 | 出险后多久报案 | Timing; carrier-specific |
| LT11 | 怎么投诉保险公司 | CDI complaints page |
| LT14 | 外州搬来加州 | CA requirements for new residents |
| LT15 | 没车但需要保险 | Non-owner policy |
| LT18 | 有事故记录还能好司机折扣吗 | CA good driver definition |
| LT20 | NAIC 号是什么 | DMV reinstatement |

### 3.4 How to use without overwhelming demo

| Use case | Questions | How |
|----------|-----------|-----|
| **Pre-demo validate** | Q1–Q5 only | `demo_quick_validate.sh` (unchanged) |
| **Broker meeting** | Q1–Q5 + 3 long-tail | Manually pick LT03, LT05, LT16; click in demo |
| **Extended regression** | Q1–Q5 + LT01, LT03, LT05, LT16 | Optional `--longtail` in broker_regression |
| **Corpus planning** | LT06, LT09, LT11, LT14, LT15, LT18, LT20 | Add URLs to broker_demo_urls or discover scripts |

---

## 4. Product gap analysis

### Strongest areas

| Area | Evidence |
|------|----------|
| **Policy minimums (15/30/5, collision/comprehensive)** | Q1, LT01, LT16 — DMV + GEICO/Progressive coverage pages |
| **Registration suspension / reinstatement** | Q2, LT05 — DMV suspended page, $14 fee fix |
| **Compliance / license lookup** | Q3 — CDI Check a License |
| **Claims flow (general)** | Q5 — safety → report → insurer → materials |

### Weakest areas

| Area | Evidence |
|------|----------|
| **Claims timing** | LT09 — "24h" or "as soon as possible" not explicit |
| **SR-22 details** | LT03, LT06 — DMV has page; retrieval may be thin |
| **Carrier-specific discounts** | LT07, LT08, LT18 — Q4 has categories; percentages/acceptance vary |
| **Edge cases** | LT14, LT15 — out-of-state, non-owner; corpus likely thin |
| **Complaints** | LT11 — CDI complaints; may need corpus add |

### Single highest-value next improvement

**SR-22 + proof of insurance (LT03, LT04, LT06)**

**Why:**

1. **High broker value**: High-risk clients (DUI, lapse, suspension) are common; brokers need clear SR-22 guidance.
2. **Corpus exists**: `broker_demo_urls.json` already includes `dmv.ca.gov/.../sr-22/` and `proof-of-insurance/`.
3. **General, not carrier-dependent**: SR-22 definition and who needs it are CA/DMV facts.
4. **Extends validated Q2**: Same suspension/reinstatement domain; natural expansion.

**Concrete next step**: Verify SR-22 and proof-of-insurance pages are in corpus and retrievable. If retrieval is weak, add targeted chunks or ensure URLs are in `broker_demo_urls` and re-ingest. No new answer-fix logic needed initially — retrieval improvement may suffice.

---

## 5. Manual-work reduction

### What Andy no longer has to manually brainstorm

- **20 realistic long-tail questions** — in `configs/broker_longtail_questions.json`
- **Categories and frequency** — tagged; no need to re-derive
- **Which are core vs future** — validation_tier field
- **Carrier-dependent vs general** — carrier_dependent field

### What Cursor can now help test repeatedly

- Run `broker_regression_all5.py` for Q1–Q5 (existing)
- Optionally extend with `--longtail LT01,LT03,LT05,LT16` for 9-question regression
- Use `broker_longtail_questions.json` as input to any validation script

### What OpenClaw can repeatedly simulate or validate

- Snapshot answers for long-tail questions (same pattern as `snapshot_demo_answers.py`)
- Ingest/refresh corpus using `broker_demo_urls.json` + any new URLs for LT06, LT09, LT11, etc.

### Reusable asset created

| Asset | Path | Purpose |
|-------|------|---------|
| **Long-tail question set** | `configs/broker_longtail_questions.json` | Structured questions for validation, corpus planning, broker meetings |
| **This report** | `docs/BROKER_LONGTAIL_QUESTION_EXPANSION_REPORT.md` | Sprint record, gap analysis, next steps |

---

## 6. Future extraction note

### What looks reusable

| Item | Reusable as |
|------|-------------|
| **Question set structure** | Scenario pack (questions + metadata) |
| **Validation tiers** | Validation pack (core / secondary / future_corpus) |
| **Category taxonomy** | Broker vertical template |
| **broker_regression pattern** | Validation script template |

### What is California-specific

- 15/30/5, DMV, insurance.ca.gov, SR-22, $14 fee, Check a License
- Question phrasing (Chinese) — same scenarios can be translated

### What may later become region-specific question-pack material

- **Region config**: `configs/regions/ca_auto_insurance.json` — questions, fallbacks, scenario tags
- **Question pack**: Swap `broker_longtail_questions.json` per region; same structure
- **Validation pack**: Same checks (sources, key phrases); different expected values per region

**No heavy architecture changes.** Documentation only.

---

## 7. Recommended next sprint

**Target**: SR-22 + proof of insurance retrieval and answer quality (LT03, LT04, LT06)

**Why:**

1. High broker value for high-risk clients
2. Corpus URLs already in `broker_demo_urls.json`
3. General guidance (not carrier-dependent)
4. Extends validated Q2 domain

**Concrete steps:**

1. Run LT03, LT04 against live backend; inspect retrieval (sources, domains)
2. If SR-22/proof pages are missing from retrieval: verify corpus ingestion, add URLs if needed
3. If retrieval is good but answer is thin: consider lightweight broker hint for SR-22 (similar to Q2 $14)
4. Add LT03 to optional long-tail regression; track pass/fail

**Out of scope for next sprint**: Carrier-specific discounts, complaints, edge cases (out-of-state, non-owner). Those are future corpus targets.

---

*End of report*
