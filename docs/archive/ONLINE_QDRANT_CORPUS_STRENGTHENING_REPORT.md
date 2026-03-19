# Online Qdrant Corpus Strengthening Report

**Phase**: High-Value Online Qdrant Corpus Strengthening  
**Date**: 2026-03-06  
**Goal**: Strengthen the online Qdrant knowledge base so the California auto insurance broker assistant answers more real broker questions with higher usefulness, better specificity, and stronger authority.

---

## 1. Current corpus gaps

### Scenario-by-scenario gap analysis

| Scenario | Current state | Gap | Severity |
|----------|---------------|-----|----------|
| **Q1: New car / minimum insurance** | ✅ Strong. 15/30/5, collision/comprehensive, broker steps. | Minor: DMV minimum-requirements URL sometimes missing in fallback. | Low |
| **Q2: Registration suspended** | ✅ Strong. $14 fee, DMV online submit, steps. | Fee may vary by case; broker can copy/share. | Low |
| **Q3: Compliance / license lookup** | ✅ Strong. Direct Check a License URL. | Broker must still navigate CDI site; search tips not in answer. | Low |
| **Q4: Save money / discounts** | ⚠️ **Weak**. Generic factors + discount list; no insurer-specific URLs. | **Major**: No carrier-specific discount programs; broker does manual lookup. Answers too generic. | **High** |
| **Q5: Claims process** | ✅ Strong. Clear flow: safety → report → insurer → materials. | Minor: No "report within 24h" explicit; no SR-22 mention for high-risk. | Medium |

### Where current answers are too generic

1. **Q4 (discounts/savings)**  
   - Current: "保费受驾驶记录、车型、里程、居住地等影响。常见折扣：好司机、多车、学生、安全设备、续保忠诚度。"  
   - Gap: No concrete discount categories with eligibility criteria; no "what to ask the client"; no "what varies by carrier" vs "generally true"; no direct links to insurer discount pages.  
   - Sources in demo_fallback: DMV homepage, insurance.ca.gov homepage — not discount-specific.

2. **Q5 (claims)**  
   - Minor: No explicit "report within 24–48 hours" guidance; no SR-22 mention for DUI/suspension cases.

3. **New car process**  
   - Minor: No explicit "what documents to prepare" for first-time registration.

4. **Registration suspension**  
   - Minor: No explicit "what if VIN mismatch" or "commercial policy" edge cases.

5. **Compliance**  
   - Minor: No "search tips" for Check a License (e.g., use NAIC number vs company name).

---

## 2. High-value target corpus plan

### Source categories (prioritized)

| Category | Why it matters | Scenarios | Priority | Authority | Ingestion suitability |
|----------|----------------|-----------|----------|-----------|------------------------|
| **California DMV official pages** | 15/30/5, SR-22, registration, proof of insurance, reinstatement | Q1, Q2, Q5 | **High** | Official | ✅ Already in data_sources; add suspended-registration, proof-of-insurance, SR-22 |
| **California Department of Insurance (CDI)** | Regulations, consumer guides, rate factors, **discounts**, claims, licensing | Q1, Q3, Q4, Q5 | **High** | Official | ✅ Already in data_sources; ensure `/help/auto/discounts/`, `/help/auto/rate-factors/` |
| **Insurer discount/FAQ pages** | Carrier-specific discount programs, eligibility, savings levers | Q4 | **High** | Semi-official | ✅ GEICO, Progressive have discount URLs; add Allstate, Nationwide, Farmers |
| **SR-22 / proof-of-insurance guidance** | Who needs SR-22, how to get it, DMV requirements | Q2, Q5 (high-risk) | **High** | Official | ✅ DMV SR-22 URL in data_sources |
| **Claims / accident steps pages** | Post-accident flow, 24h guidance, materials to gather | Q5 | **High** | Official + insurer | ✅ CDI claims, insurer claims URLs |
| **Reinstatement / suspension guidance** | $14 fee, online submit, materials, edge cases | Q2 | **High** | Official | ✅ DMV suspended-registration URL |
| **Compliance / license lookup** | Check a License, NAIC lookup | Q3 | **Medium** | Official | ✅ CDI licensing URLs |
| **New car insurance process** | Documents, timing, first registration | Q1 | **Medium** | Official + insurer | Partial; add DMV new-vehicle registration |
| **Underwriting / documentation requirements** | What brokers need to collect | Q1, Q4 | **Medium** | Insurer | Partial; FAQ pages |
| **Broker/client communication templates** | Internal; not crawlable | All | **Low** | Internal | ❌ Generate internally or manual |
| **Carrier-specific practical guidance** | Discount programs, claims contacts | Q4, Q5 | **High** | Semi-official | ⚠️ Only public FAQ/help; no ToS violation |

### Ingestion suitability notes

- **Official (dmv.ca.gov, insurance.ca.gov)**: Always suitable; robots.txt compliant; high authority.
- **Insurer public help/FAQ**: Suitable if robots.txt allows; avoid account/login pages.
- **State Farm**: Removed from discovery seeds (robots.txt blocks per prior review).
- **Carrier-specific rules**: Do not hallucinate. In answers, phrase as "varies by carrier" or "check with your insurer."

---

## 3. Existing repo asset reuse

### What can be reused

| Asset | Path | Reuse |
|-------|------|-------|
| **Discovery script** | `scripts/discover_auto_insurance_sources.py` | ✅ Reuse. Seeds from DMV, CDI, GEICO, Progressive, Allstate, Farmers, Nationwide, Liberty Mutual, Travelers, AAA, USAA. Domain tiers (T0/T1/T2), scoring, robots.txt, checkpointing. |
| **Ingest pipeline** | `pipelines/auto_insurance_ingest.py` | ✅ Reuse. Config-driven; reads `data_sources.json` or `--config` with `target_urls`. |
| **Demo collection builder** | `scripts/build_demo_core_collection.py` | ✅ Reuse. Fetches URLs, extracts text, embeds, upserts to `auto_insurance_demo_core`. |
| **One-click ingest** | `scripts/run_demo_ingest_oneclick.sh` | ✅ Reuse. Uses passing.json or RUN_REVIEW.md; limit 30 URLs. |
| **Quality gate** | `pipelines/quality_gate_auto_insurance.py` | ✅ Reuse. Domain allowlist, keyword filter, min chars. |
| **Daily pipeline** | `scripts/run_auto_insurance_daily.sh` | ✅ Reuse for `auto_insurance_v2_clean`; uses `daily_targets.json`. |
| **Data sources** | `docs/prompt2_input/data_sources.json` | ✅ Reuse. Has DMV, CDI, GEICO, Progressive, Allstate, Farmers, Nationwide; includes discount URLs (GEICO, Progressive, CDI). |
| **Daily targets** | `results/auto_insurance/daily_targets.json` | ⚠️ Update. Currently 13 URLs; no discount-specific; no CDI discounts. |

### What needs small updates

| Asset | Change |
|-------|--------|
| **daily_targets.json** | Add CDI `/help/auto/discounts/`, `/help/auto/rate-factors/`; add GEICO `/save/discounts/`, Progressive `/auto/discounts/`; add DMV SR-22, proof-of-insurance. |
| **discover_auto_insurance_sources.py** | Add discount-focused seed URLs (optional): GEICO discounts, Progressive discounts, CDI rate factors. |
| **data_sources.json** | Ensure ds_002 (CDI) has `/help/auto/discounts/`, `/help/auto/rate-factors/`; verify Allstate, Nationwide, Farmers have discount URLs. |
| **build_demo_core_collection.py** | No change; uses URL list. |
| **quality_gate_auto_insurance.py** | Expand `DEFAULT_ALLOWLIST_DOMAINS` if adding Allstate, Nationwide, Farmers to daily. |

### What to avoid

- **Broad crawling**: Do not increase `max_pages_per_source` or add many low-value domains.
- **Noisy sources**: NerdWallet, ValuePenguin, The Zebra — useful for comparison but lower authority; keep for P2, not demo core.
- **State Farm**: Blocked by robots.txt; do not add to seeds.
- **Carrier-specific rules**: Do not ingest or generate carrier-specific underwriting rules; only public FAQ/help.

---

## 4. Recommended immediate source additions

### Ordered by expected broker value

| Rank | Source | URL | Scenario | Why |
|------|--------|-----|----------|-----|
| 1 | CDI Auto Discounts | `https://www.insurance.ca.gov/01-consumers/help/auto/discounts/` | Q4 | Official list of common discounts; broker-useful. (Note: May return 403 for automated fetch; try alternative `/105-type/95-guides/auto/` if needed.) |
| 2 | CDI Rate Factors | `https://www.insurance.ca.gov/01-consumers/help/auto/rate-factors/` | Q4 | Official factors affecting premium. |
| 3 | GEICO Car Insurance Discounts | `https://www.geico.com/save/discounts/car-insurance-discounts/` | Q4 | Concrete discount categories; T1 insurer. |
| 4 | Progressive Auto Discounts | `https://www.progressive.com/auto/discounts/` | Q4 | Snapshot, multi-car, etc.; T1 insurer. |
| 5 | DMV Suspended Registration | `https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/suspended-vehicle-registration/` | Q2 | Already in data_sources; ensure in demo URL list. |
| 6 | DMV SR-22 | `https://www.dmv.ca.gov/portal/driver-education/insurance/sr-22/` | Q2, Q5 | SR-22 definition, who needs it. |
| 7 | CDI Auto Claims | `https://www.insurance.ca.gov/01-consumers/help/auto/claims/` | Q5 | Official claims guidance. |
| 8 | Progressive What to Do After Accident | `https://www.progressive.com/answers/what-to-do-after-car-accident/` | Q5 | Step-by-step; 24h guidance possible. |
| 9 | GEICO Claims Process | `https://www.geico.com/claims/claimsprocess/` | Q5 | Claims flow. |
| 10 | Allstate Discounts (if available) | `https://www.allstate.com/auto-insurance/discounts` or help | Q4 | Add if robots.txt allows. |
| 11 | Nationwide Auto Discounts | `https://www.nationwide.com/personal/insurance/auto/discounts/` | Q4 | Add if exists and crawlable. |
| 12 | Farmers Discounts | `https://www.farmers.com/insurance/auto/discounts/` | Q4 | Add if exists. |

### Shortlist for immediate ingest (next run)

**Created**: `configs/broker_demo_urls.json` and `configs/broker_demo_urls.txt` with 18 curated URLs.

To build demo core from curated list:
```bash
python3 scripts/build_demo_core_collection.py \
  --url-list configs/broker_demo_urls.txt \
  --limit 25 \
  --recreate
```

Or use one-click with discovery (uses passing.json):
```bash
bash scripts/run_demo_ingest_oneclick.sh
```

### Shortlist for later evaluation

- Allstate, Nationwide, Farmers discount pages (verify URLs and robots.txt).
- CDI Chinese consumer pages (`/01-consumers/chinese/`).
- III (Insurance Information Institute) claims/savings guides — T2, supplementary.

---

## 5. Discounts / savings corpus improvement

### What is missing now

1. **Concrete discount categories** with eligibility (good driver, multi-car, student, defensive driving, etc.).
2. **What the broker should ask the client** (driving record, multi-policy, mileage, safety features).
3. **What the client should prepare** (proof of grades, completion certificates, etc.).
4. **What is generally true vs carrier-specific** (e.g., "good driver discount is common" vs "exact % varies by carrier").
5. **Direct links** to insurer discount pages for broker to share or verify.

### What to add

| Content type | Source | Example |
|--------------|--------|---------|
| Official discount list | CDI `/help/auto/discounts/` | Good driver, multi-car, low mileage, etc. |
| Rate factors | CDI `/help/auto/rate-factors/` | Driving record, location, vehicle type. |
| Insurer discount pages | GEICO, Progressive, Allstate, Nationwide, Farmers | Program names, eligibility hints. |
| Broker action template | Internal / generated | "Ask: Do you have multiple cars? Good student? Defensive driving course?" |

### How answers should handle carrier variability

- **Generally applicable**: "Common discounts include good driver, multi-car, good student, defensive driving, low mileage. Eligibility and amounts vary by carrier."
- **Carrier-specific**: "For specific programs and amounts, check [carrier]'s discount page: [URL]. Broker should verify with carrier."
- **Do not**: State exact percentages or dollar amounts as if universal; do not invent carrier rules.
- **Phrasing**: "Many insurers offer…"; "Check with your carrier for…"; "Eligibility varies."

---

## 6. Corpus quality strategy

### Curation rules

1. **Authority first**: Prefer dmv.ca.gov, insurance.ca.gov over third-party.
2. **Broker usefulness**: Prefer pages that answer real client questions (discounts, claims, suspension, compliance).
3. **One document per topic**: Avoid duplicate coverage of same topic from multiple low-value sources.
4. **Max 30–50 URLs for demo core**: Quality over volume.

### Deduplication approach

- **URL-level**: Normalize (remove query, fragment, trailing slash); skip if already ingested.
- **Content-level**: Existing pipeline uses `ContentHasher.hash_document`, `hash_chunk`; keep.
- **Semantic**: If two pages say the same thing (e.g., 15/30/5), prefer official source.

### Freshness / authority considerations

- **Official pages**: DMV, CDI change infrequently; re-crawl monthly or on demand.
- **Insurer pages**: May change; re-crawl quarterly or when broker reports stale info.
- **Stale detection**: Optional: store `last_updated` or `fetched_at`; flag if >6 months.
- **Authority tagging**: `source_tier` in build_demo_core_collection (gov, insurer, other); use for ranking.

### Separating official vs practical guidance

- **Metadata**: Add `authority: official | semi-official | practical` to payload.
- **Official**: dmv.ca.gov, insurance.ca.gov.
- **Semi-official**: Insurer public help/FAQ.
- **Practical**: NerdWallet, ValuePenguin — use for "generally true" context, not regulatory.

### Keeping future China/Europe packs clean

- **Region tags**: `region: ca_auto_insurance` in payload.
- **Separate collections**: `auto_insurance_demo_core` (CA) vs future `cn_auto_insurance` or `eu_auto_insurance`.
- **No cross-region mixing** in same collection without explicit region filter.

---

## 7. Future extraction note

### Common base

- Query/answer flow, translation, embedding model, reranking.
- Broker UI (DemoPage, 复制给客户, scenario tags).
- Quality gate logic (domain allowlist, keyword filter).
- Discovery pattern (seeds → score → filter).

### California-specific

- 15/30/5 minimums, $14 reinstatement fee, DMV, insurance.ca.gov.
- Check a License URL, SR-22, CA registration suspension.
- Question wording (Chinese), scenario tags (新车投保, 注册恢复, etc.).

### Future region/source-pack extraction points

| Component | Current location | Future extraction |
|-----------|------------------|-------------------|
| Questions + fallbacks | `DemoPage.tsx`, `demo_fallback.json`, `snapshot_demo_answers.py` | `configs/regions/ca_auto_insurance.json` |
| Source list | `data_sources.json`, `daily_targets.json` | `configs/regions/ca_auto_insurance_sources.json` |
| Scenario tags | `DemoPage.tsx` | `configs/regions/ca_auto_insurance.json` |
| Broker test sheet | `docs/broker_value_test_sheet.md` | `docs/broker_value_test_sheet_TEMPLATE.md` |

**No heavy re-architecture.** Documentation and light config extraction only.

---

## 8. Work split

| Who | Responsibility |
|-----|----------------|
| **Cursor** | Update `daily_targets.json`, create `configs/broker_demo_urls.json`, update `data_sources.json` discount URLs, document corpus plan, update quality gate allowlist if needed. |
| **OpenClaw** | Run discovery with discount-focused seeds if added; run `build_demo_core_collection.py` with new URL list; run `snapshot_demo_answers.py` when backend live. |
| **Andy** | Run one-click ingest after config updates; validate Q4 (discounts) with broker; decide which insurer discount pages to add; run value-validation meeting. |

---

## 9. Next 12 actions

1. **Add discount URLs to daily_targets.json** — CDI discounts, CDI rate-factors, GEICO discounts, Progressive discounts.
2. **Create configs/broker_demo_urls.json** — Curated shortlist for immediate ingest (10–15 URLs).
3. **Verify CDI discounts URL** — `insurance.ca.gov/01-consumers/help/auto/discounts/` (may 403; find alternative path if needed).
4. **Update data_sources.json** — Ensure ds_002 has discount and rate-factors URLs.
5. **Run discovery** — `python scripts/discover_auto_insurance_sources.py --max-candidates 50` to surface discount pages.
6. **Run one-click ingest** — `bash scripts/run_demo_ingest_oneclick.sh` with new URL list.
7. **Run snapshot** — `python3 scripts/snapshot_demo_answers.py` when backend on 8001.
8. **Validate Q4** — Test "客户想省钱：哪些因素会影响保费？有哪些常见折扣？" with live backend; check if sources include discount pages.
9. **Add broker action template for Q4** — In fallback or answer template: "Ask client: 多车？好学生？防御性驾驶课？"
10. **Document carrier variability** — Add to answer template: "Eligibility and amounts vary by carrier; check insurer discount page."
11. **Expand quality gate allowlist** — If adding Allstate, Nationwide, Farmers to daily.
12. **Extract region config** — When expanding to China/Europe; create `configs/regions/ca_auto_insurance.json` stub.

---

*End of report*
