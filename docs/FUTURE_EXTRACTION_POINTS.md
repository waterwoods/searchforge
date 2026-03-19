# Future Extensibility — Region Config Pack

**Purpose**: Lightweight note on what is common base vs region-specific. No refactor now.

---

## 1. Common base (reusable)

| Component | Location | Notes |
|-----------|----------|-------|
| Search/RAG pipeline | `services/fiqa_api/`, `services/fiqa_api/services/search_core.py` | Collection-agnostic |
| Query route, translation | `services/fiqa_api/routes/query.py` | Mode-agnostic |
| Demo UI shell | `ui/src/pages/DemoPage.tsx` | Scenario labels, copy flow |
| Copy utilities | `ui/src/utils/demoCopy.ts` | Format-agnostic |
| Health, metrics | `services/fiqa_api/health/`, `routes/metrics.py` | Shared |

---

## 2. California auto insurance–specific (candidate for region config pack)

| Item | Location | Future extraction |
|------|----------|-------------------|
| Sample questions | `DemoPage.tsx` SAMPLE_QUESTIONS, SCENARIOS | `configs/ca_auto_insurance.json` |
| Fallback answers | `DemoPage.tsx` DEFAULT_FALLBACK_ITEMS | Same config or `demo_fallback.json` |
| Scenario detection | `DemoPage.tsx` detectScenario(), fallbackNewCar, etc. | Config: `scenario_patterns`, `fallbacks` |
| Domain badges | `DemoPage.tsx` INSURER_DOMAINS | Config: `gov_domains`, `insurer_domains` |
| Collection mapping | `query.py` COLLECTION_MAP | Env or config: `demo_collection` |
| Value prop copy | `DemoPage.tsx` header, labels | Config: `ui_strings` |

---

## 3. Minimal extraction points (when expanding to China/Europe)

1. **Config file**: `configs/regions/ca_auto_insurance.json` (or similar)
   - `questions`, `scenarios`, `fallbacks`, `domains`, `ui_strings`
2. **DemoPage**: Load config by `region` or `profile` param
3. **Collection**: Env `DEMO_COLLECTION` or config `collection`
4. **No heavy refactor**: Keep current structure; add config loader only when needed

---

*Documentation only. No code changes.*
