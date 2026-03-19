# Prompt 5: Translation Layer Implementation Plan

## Overview

This document outlines the implementation of a translation layer for Chinese-English queries in the Auto Insurance RAG system. The goal is to improve Chinese user experience without requiring large amounts of Chinese corpus.

## Architecture

### Translation Flow

```
Chinese Query → Detect Language → Translate to English → Search (English corpus) → Translate Results → Return Chinese
```

### Components

1. **Translation Module** (`services/fiqa_api/utils/translation.py`)
   - Language detection
   - Chinese → English translation (for queries)
   - English → Chinese translation (for results)
   - Graceful fallback if translation unavailable

2. **Query Pipeline Integration** (`services/fiqa_api/routes/query.py`)
   - Detect query language
   - Translate Chinese queries to English before search
   - Translate English results to Chinese in response
   - Add translation metadata to response

3. **Evaluation Support** (`scripts/eval_auto_insurance_rag.py`)
   - Support `--translate-zh` flag
   - Evaluate Chinese queries using translation strategy
   - Generate separate translation evaluation report

## Configuration

### Environment Variables

```bash
# Enable translation
TRANSLATION_ENABLED=1

# Translation provider (argos|none)
TRANSLATION_PROVIDER=argos

# Translate source results to Chinese
TRANSLATE_SOURCES_TO_ZH=1
```

### Request Parameters

```json
{
  "question": "加州最低汽车保险要求是什么？",
  "collection": "auto_insurance",
  "translation_mode": "auto"  // or true/false
}
```

### Response Format

```json
{
  "ok": true,
  "question": "加州最低汽车保险要求是什么？",  // Original
  "question_used": "What are the minimum auto insurance requirements in California?",  // Translated
  "translation_applied": true,
  "detected_lang": "zh",
  "sources": [
    {
      "title": "California Auto Insurance Requirements",
      "title_zh": "加州汽车保险要求",
      "text": "California requires...",
      "text_zh": "加州要求...",
      "translations": {
        "zh": {
          "title": "加州汽车保险要求",
          "text": "加州要求..."
        }
      }
    }
  ]
}
```

## Installation

### Install Argos Translate

```bash
pip install argostranslate

# Install language packages (first time only)
python -m argostranslate.argostranslate --install-packages zh en
```

### Verify Installation

```bash
python3 -c "from services.fiqa_api.utils.translation import is_translation_available; print('Available:', is_translation_available())"
```

## Testing

### Smoke Test

```bash
./scripts/smoke_test_translation_query.sh
```

### Manual Test

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "加州最低汽车保险要求是什么？",
    "collection": "auto_insurance",
    "translation_mode": "auto"
  }'
```

### Evaluation with Translation

```bash
python3 scripts/eval_auto_insurance_rag.py \
  --collection auto_insurance_v2_clean \
  --translate-zh 1 \
  --report-dir results/auto_insurance
```

## Frontend Integration

### Enable Translation Mode

Add a toggle in the frontend:

```typescript
const [translationEnabled, setTranslationEnabled] = useState(false);

// In query request
const response = await fetch('/api/query', {
  method: 'POST',
  body: JSON.stringify({
    question: query,
    collection: 'auto_insurance',
    translation_mode: translationEnabled ? 'auto' : undefined
  })
});

// Display translated results
const displayTitle = source.title_zh || source.title;
const displayText = source.text_zh || source.text;
```

## Known Limitations

1. **Translation Quality**: Argos Translate is offline but may have lower quality than commercial APIs
2. **Performance**: Translation adds latency (typically 50-200ms per query)
3. **Language Support**: Currently only Chinese-English, can be extended
4. **Fallback**: If translation fails, system falls back to original text

## Next Steps

1. Add more Chinese authoritative sources
2. Improve translation quality (consider commercial APIs as optional)
3. Add caching for common translations
4. Extend to Spanish and other languages
5. Add translation quality metrics
