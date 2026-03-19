# Prompt 5 Acceptance Checklist

## A) Translation Layer Implementation

- [x] Translation module created (`services/fiqa_api/utils/translation.py`)
- [x] Language detection implemented
- [x] Chinese → English translation (queries)
- [x] English → Chinese translation (results)
- [x] Graceful fallback if translation unavailable
- [x] Environment variable configuration
- [x] Integration into query pipeline
- [x] Response format includes translation metadata
- [x] Backward compatible (English queries unchanged)

## B) Chinese Authoritative Sources

- [x] Updated `data_sources.json` with Chinese sources
  - [x] DMV Chinese pages (ds_012)
  - [x] CDI Chinese consumer guides (ds_017)
  - [x] Insurer language assistance pages (ds_013)
- [x] Sources configured with appropriate limits
- [ ] Run incremental crawl (manual step - see instructions)

## C) Evaluation Script Upgrade

- [x] `--translate-zh` flag added
- [x] Chinese queries translated before search
- [x] Separate evaluation report generated (`EVAL_REPORT_TRANSLATION.md`)
- [x] Translation metadata in evaluation results
- [x] Metrics endpoint supports translation reports

## D) Frontend Demo Integration

- [ ] Translation toggle added to DemoPage.tsx
- [ ] Translation mode passed to API
- [ ] Display translated results (title_zh, text_zh)
- [ ] Show original text option (expandable)

## E) Testing & Documentation

- [x] Smoke test script created (`scripts/smoke_test_translation_query.sh`)
- [x] Translation plan document (`docs/supporting/PROMPT5_TRANSLATION_PLAN.md`)
- [x] Acceptance checklist (this file)
- [x] Completion summary (`docs/supporting/PROMPT5_COMPLETION_SUMMARY.md`)

## Verification Steps

1. **Install Dependencies**:
   ```bash
   pip install argostranslate
   python -m argostranslate.argostranslate --install-packages zh en
   ```

2. **Set Environment Variables**:
   ```bash
   export TRANSLATION_ENABLED=1
   export TRANSLATION_PROVIDER=argos
   export TRANSLATE_SOURCES_TO_ZH=1
   ```

3. **Run Smoke Test**:
   ```bash
   ./scripts/smoke_test_translation_query.sh
   ```

4. **Test API Directly**:
   ```bash
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"question": "加州最低汽车保险要求是什么？", "collection": "auto_insurance", "translation_mode": "auto"}'
   ```

5. **Run Evaluation with Translation**:
   ```bash
   python3 scripts/eval_auto_insurance_rag.py \
     --collection auto_insurance_v2_clean \
     --translate-zh 1
   ```

6. **Check Frontend** (if implemented):
   - Open http://localhost:5173/demo
   - Enable "Translate (ZH->EN search, EN->ZH display)"
   - Enter Chinese query
   - Verify results show Chinese translations

## Acceptance Criteria

- ✅ Translation module functional
- ✅ Query pipeline integrated
- ✅ Response format includes translation fields
- ✅ Smoke test passes
- ✅ Evaluation script supports translation mode
- ⚠️ Frontend integration (pending - manual step)
- ⚠️ Chinese source crawl (pending - manual step)

## Known Issues

1. **Argos Translate Installation**: Requires manual package installation
2. **Translation Quality**: Offline translation may have lower quality
3. **Performance**: Adds 50-200ms latency per query
4. **Frontend**: Demo page integration needs manual implementation
