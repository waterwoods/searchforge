# Curated Corpus Revalidation Report

**Date**: 2026-03-06  
**Phase**: Curated Corpus Ingest + 5-Question Revalidation + Q4 Upgrade

---

## 1. Ingest Result

### Commands run
```bash
USE_LOCAL_QDRANT=1 python3 scripts/build_demo_core_collection.py \
  --url-list configs/broker_demo_urls.txt \
  --limit 25 \
  --recreate
```

### What was ingested
- **15 documents** successfully ingested into `auto_insurance_demo_core`
- **Domains**: dmv.ca.gov (2), insurance.ca.gov (7), geico.com (3), progressive.com (3)
- **Key Q4 sources**: geico.com/save/discounts/car-insurance-discounts/ (9620 chars), progressive.com/auto/discounts/ (6101 chars)

### What failed
| URL | Reason |
|-----|--------|
| https://www.dmv.ca.gov/portal/driver-education/insurance/sr-22/ | 404 Not Found |
| https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/proof-of-insurance/ | 404 Not Found |
| https://www.progressive.com/answers/auto-insurance/ | 404 Not Found |

### What remains blocked
- **insurance.ca.gov subpages** (rate-factors, discounts, claims, coverage-types, auto-basics): Return "Document Not Found" 404 pages. The corpus has 7 insurance.ca.gov points but most are the same 404 template; only the license-check page has useful content.
- **DMV SR-22 and proof-of-insurance**: URLs have moved or been removed.

---

## 2. 5-Question Revalidation

| Scenario | Usefulness | Specificity | Authority | Shareability | vs Before |
|----------|------------|-------------|------------|--------------|-----------|
| **Q1** (Minimum insurance / new car) | 9/10 | 8/10 | 9/10 | 9/10 | **Better** – now includes $75k alternatives, collision/comprehensive |
| **Q2** (Suspended registration) | 7/10 | 6/10 | 8/10 | 7/10 | **Same** – $14 fee not surfaced in answer (in corpus but LLM missed) |
| **Q3** (Compliance / license lookup) | 9/10 | 9/10 | 10/10 | 9/10 | **Same** – already strong |
| **Q4** (Discounts / saving money) | 8/10 | 8/10 | 8/10 | 8/10 | **Better** – discount categories, broker hint, Progressive/GEICO sources |
| **Q5** (Claims flow) | 3/10 | 2/10 | 6/10 | 2/10 | **Worse** – LLM returns "context does not contain" (retrieval OK, answer gen fails) |

### Q1
- **Answer**: Liability, $75k alternatives, collision/comprehensive. Solid.
- **Sources**: dmv.ca.gov, geico.com – correct.

### Q2
- **Answer**: VIN check, online submit, insurance proof. Missing explicit $14.
- **Sources**: dmv.ca.gov/suspended – correct; fee is in corpus but not in LLM context.

### Q3
- **Answer**: insurance.ca.gov, Check a License, browser requirements.
- **Sources**: insurance.ca.gov/check-license-status – correct.

### Q4
- **Answer**: 驾驶历史, 车辆设备, 驾驶员教育, 多保单, 切换折扣, 忠诚折扣. **Broker hint appended**: 经纪人可进一步询问：客户当前保单、多车情况、好学生、安全设备、续保年限等。
- **Sources**: progressive.com/discounts, geico.com/discounts – correct.

### Q5
- **Answer**: LLM returns "The context provided does not contain specific information" (English).
- **Sources**: geico.com/claims, progressive.com/claims, progressive.com/what-to-do – retrieval OK; answer generation fails.

---

## 3. Q4 Upgrade Assessment

### Did Q4 improve materially?
**Yes.** Before: generic "好司机、多车、学生". After: specific categories (驾驶历史, 车辆设备, 驾驶员教育, 多保单, 切换折扣), broker follow-up hint, and carrier variability note.

### What is still weak
- **insurance.ca.gov discount content**: Rate-factors and discounts pages are 404; no CA DOI discount list.
- **Carrier-specific rules**: Answer correctly notes "各公司折扣政策不同" but cannot list carrier-specific discounts.
- **Client info to collect**: Broker hint covers this; could be more structured.

### Smallest next improvement
1. **Fix insurance.ca.gov**: Find working CA DOI discount/rate-factors URLs or use archived content.
2. **Q5 fallback**: Add a minimal canned claims summary when LLM returns "does not contain" for 理赔/出险 questions.
3. **Q2 $14**: Add a post-process hint when suspension question + dmv.ca.gov/suspended in sources.

---

## 4. Smallest High-Value Changes Made

| File | Change | Why |
|------|--------|-----|
| `scripts/snapshot_demo_answers.py` | Added `generate_answer: true` | Ensures snapshot captures full answers for revalidation |
| `services/fiqa_api/services/search_core.py` | Snippet 400→800 chars for `auto_insurance_demo_core` | More context for Q4/Q5 answer generation |
| `services/fiqa_api/routes/query.py` | Broker hint for discount questions in demo mode | Adds "经纪人可进一步询问" and carrier variability note |
| `ui/src/pages/DemoPage.tsx` | Added `generate_answer: true` to live API calls | Live demo returns answers, not just sources |

---

## 5. Fallback/Support Updates

| Asset | Updated | Improves demo? |
|-------|---------|----------------|
| `ui/src/assets/demo_fallback.json` | Yes – re-snapshot with new corpus + improvements | Yes – Q4 has broker hint; Q1/Q2/Q3 improved |
| `docs/CURATED_CORPUS_REVALIDATION_REPORT.md` | New | Yes – documents revalidation and next steps |

---

## 6. Remaining Blockers

1. **insurance.ca.gov discount/rate-factors pages**: 404; need alternative URLs or archived content.
2. **Q5 claims**: LLM answer generation fails despite good retrieval; needs prompt or fallback fix.
3. **Q2 $14 fee**: In corpus but not reliably surfaced; consider explicit hint.

---

## 7. Work Split

| Role | Tasks |
|------|-------|
| **Cursor** | Ingest, revalidation, code changes, report |
| **OpenClaw** | (Not used this phase) |
| **Andy** | Verify demo with 陈魁; find working insurance.ca.gov URLs; decide on Q5 fallback |

---

## 8. Next 12 Actions (Priority Order)

1. **Find working insurance.ca.gov discount/rate-factors URLs** – or add CA DOI archived content for Q4.
2. **Add Q5 claims fallback** – when LLM returns "does not contain" for 理赔/出险, use minimal canned summary.
3. **Add Q2 $14 hint** – when suspension question + dmv suspended source, append "$14 复职费".
4. **Re-run snapshot** after Q5/Q2 fixes.
5. **Verify demo** with 陈魁 – confirm Q4 broker hint and discount flow.
6. **Update broker_demo_urls.txt** – remove 404 URLs; add any new working CA DOI URLs.
7. **Consider SR-22 alternative** – find current DMV SR-22 URL if needed for Q2.
8. **Document carrier variability** – add to broker runbook: "discounts vary by carrier".
9. **Test offline fallback** – ensure demo_fallback.json displays correctly when backend down.
10. **Run demo_quick_validate.sh** – confirm 3-question validation still passes.
11. **Update DEMO_CHECKLIST** – add "Q4 broker hint" and "curated corpus" items.
12. **Optional**: Add `broker_hint` as separate response field for UI to render distinctly.
