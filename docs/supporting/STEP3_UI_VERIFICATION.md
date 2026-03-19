# Step 3 UI Verification Steps

## Prerequisites

✅ Backend running at http://localhost:8000  
✅ Frontend running at http://localhost:5173  
✅ Translation enabled (TRANSLATION_ENABLED=1)

## Verification Steps

### 1. Access Demo Page

Open browser and navigate to:
```
http://localhost:5173/demo
```

### 2. Enable Translation Toggle

1. Locate the checkbox/toggle: **"Translate results to Chinese"**
2. ✅ **Check/Enable** the toggle

### 3. Test Chinese Query

**Input**: Enter the following Chinese question:
```
加州最低汽车保险要求是什么？
```

**Expected Behavior**:
- Click "Search" or press Enter
- Wait for results to load

### 4. Verify Results

**Expected Results**:
- ✅ Results display in **Chinese** (translated)
- ✅ Each result shows:
  - Chinese title (`title_zh`)
  - Chinese text (`text_zh`)
- ✅ **"Show original"** expandable section available
- ✅ Translation status badge visible (e.g., "Translation Applied (zh → EN search → ZH display)")

### 5. Verify Original Content

1. Click **"Show original"** on any result
2. ✅ Should reveal:
   - Original English title
   - Original English text

### 6. Test Without Translation

1. **Uncheck** "Translate results to Chinese" toggle
2. Enter the same Chinese query
3. ✅ Results should display in **English** (original)
4. ✅ No translation badge shown

### 7. Test English Query

1. Keep translation toggle **OFF**
2. Enter English query: "What are the minimum auto insurance requirements in California?"
3. ✅ Results display normally in English
4. ✅ No translation applied

## Expected API Response (for debugging)

When translation is enabled and Chinese query is sent:

```json
{
  "ok": true,
  "question": "加州最低汽车保险要求是什么？",
  "question_used": "What's California's minimum auto insurance requirement?",
  "translation_applied": true,
  "detected_lang": "zh",
  "sources": [
    {
      "title": "California Auto Insurance Requirements",
      "title_zh": "加州汽车保险要求",
      "text": "California requires...",
      "text_zh": "加州要求...",
      "source_url": "https://...",
      "score": 0.5866
    }
  ]
}
```

## Troubleshooting

### Issue: Translation toggle not visible
- **Check**: Frontend code in `ui/src/pages/DemoPage.tsx`
- **Fix**: Ensure toggle component is rendered

### Issue: Results not translated
- **Check**: Backend logs for translation errors
- **Check**: Browser console for API errors
- **Verify**: `translation_applied: true` in API response

### Issue: "Show original" not working
- **Check**: JavaScript console for errors
- **Verify**: `sources[].title` and `sources[].text` exist in response

### Issue: Backend not responding
- **Check**: `curl http://localhost:8000/healthz`
- **Restart**: `./scripts/dev_local.sh`

## Success Criteria

✅ Translation toggle visible and functional  
✅ Chinese queries return translated results  
✅ Original content accessible via "Show original"  
✅ English queries work normally  
✅ No console errors  
✅ API returns `translation_applied: true` for Chinese queries

---

**Last Updated**: 2026-02-19
