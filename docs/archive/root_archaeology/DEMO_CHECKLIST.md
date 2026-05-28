# 🎯 Demo Checklist for Presentation

## Cloud Run Service URL
```
https://fiqa-api-g7zatxrycq-uw.a.run.app
```

## Quick Test Commands

### 1. Health Check
```bash
curl https://fiqa-api-g7zatxrycq-uw.a.run.app/healthz
```

### 2. Readiness Check
```bash
curl https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz | python3 -m json.tool
```

**Expected Response:**
```json
{
  "ok": true,
  "status": "ready",
  "clients_ready": true,
  "clients": {
    "qdrant_connected": true,
    "embedding_model": false
  }
}
```

### 3. Query Endpoint
```bash
curl -X POST "https://fiqa-api-g7zatxrycq-uw.a.run.app/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is diversification?", "top_k": 5}'
```

**Note:** Query endpoint may need 1-2 minutes after deployment for embedding model warmup (first cold start downloads model from HuggingFace).

## Vercel Frontend Configuration

Set this environment variable in Vercel:
```
VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

## Expected Query Response Format

```json
{
  "ok": true,
  "trace_id": "uuid-here",
  "question": "What is diversification?",
  "sources": [
    {
      "doc_id": "123",
      "title": "Diversification Explained",
      "snippet": "Diversification is a risk management strategy...",
      "score": 0.85
    }
  ],
  "latency_ms": 123.45
}
```

## Deployment Status

- ✅ Qdrant Preflight: PASS (10,000 points verified)
- ✅ Deploy Succeeded: PASS
- ✅ /readyz (ok:true): PASS
- ✅ qdrant_connected: PASS
- ⚠️ /api/query: May need embedding model warmup (1-2 min on cold start)

## Troubleshooting

If query endpoint returns `embedding_warming`:
1. Wait 1-2 minutes for model download (first cold start)
2. Check logs: `gcloud run services logs read fiqa-api --region us-west1 --limit 50`
3. Model download may succeed on next container start
