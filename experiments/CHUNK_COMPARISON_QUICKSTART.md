# Chunking Strategy Comparison - Quick Start

## TL;DR

```bash
# One command to run everything:
bash scripts/run_chunk_comparison.sh --api-url http://andy-wsl:8000

# View results:
cat reports/winners_chunk.json
```

---

## Prerequisites

```bash
# 1. Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# 2. Start API
docker-compose up -d

# 3. Verify API is running
curl http://andy-wsl:8000/api/health/embeddings
# Should return: {"ok": true, "model": "all-MiniLM-L6-v2", "dim": 384}
```

---

## Quick Commands

### Full Pipeline (Production)
```bash
bash scripts/run_chunk_comparison.sh --api-url http://andy-wsl:8000
# Time: ~50 minutes
# Output: All artifacts in reports/
```

### Fast Test (Development)
```bash
bash scripts/run_chunk_comparison.sh --sample 100 --recreate
# Time: ~10 minutes
# Output: Quick validation with 100 queries
```

### Skip Building (Use Existing)
```bash
bash scripts/run_chunk_comparison.sh --skip-build
# Time: ~15 minutes
# Useful: Re-run experiments without rebuilding
```

---

## View Results

```bash
# Winners JSON (main deliverable)
cat reports/winners_chunk.json | jq .

# Recommendations
cat reports/chunk_recommendations.txt

# Charts
ls reports/chunk_charts/
# - pareto_quality_latency.png
# - index_metrics.png

# Health checks
cat reports/chunk_health/health_summary.json

# Raw results
ls reports/chunk_experiments_*.json
```

---

## What Gets Built

### Collections (in Qdrant)
- `fiqa_para_50k` - Paragraph chunking
- `fiqa_sent_50k` - Sentence chunking
- `fiqa_win256_o64_50k` - Sliding window (256 chars, 64 overlap)

### Reports (in reports/)
- `winners_chunk.json` ⭐ Main deliverable
- `chunk_recommendations.txt` - Use case guidance
- `chunk_charts/` - Visualizations
- `chunk_experiments_*.json` - Raw results

### Metadata (in configs/)
- `configs/collection_tags/fiqa_para_50k.json`
- `configs/collection_tags/fiqa_sent_50k.json`
- `configs/collection_tags/fiqa_win256_o64_50k.json`

---

## Interpreting Results

### Winner Tiers

**🚀 Fast (省时)**
- **Best for**: Latency-critical, high QPS
- **Trade-off**: Slightly lower quality

**⚖️ Balanced (均衡)** ← Recommended Default
- **Best for**: Production, most use cases
- **Trade-off**: Good quality/latency balance

**🏆 High-Quality (高质)**
- **Best for**: Quality-first, research
- **Trade-off**: Higher latency

### Key Metrics

- **Recall@10**: Fraction of relevant docs in top-10 (higher is better)
- **nDCG@10**: Ranking quality (higher is better)
- **p95 Latency**: 95th percentile latency in ms (lower is better)
- **Quality Score**: 0.6×Recall@10 + 0.4×nDCG@10 (higher is better)

---

## Troubleshooting

### "Collection already exists"
```bash
bash scripts/run_chunk_comparison.sh --recreate
```

### "API not reachable"
```bash
docker-compose up -d
curl http://andy-wsl:8000/api/health
```

### "Qrels coverage < 99%"
```bash
# Check qrels file
cat data/fiqa_v1/fiqa_qrels_50k_v1.jsonl | head

# Verify collection
curl http://localhost:6333/collections/fiqa_para_50k
```

---

## File Structure

```
searchforge/
├── experiments/
│   ├── chunking_strategies.py         # Chunking implementations
│   ├── build_chunk_collections.py     # Collection builder
│   ├── run_chunk_health_checks.py     # Health check runner
│   ├── run_chunk_experiments.py       # Experiment runner
│   ├── analyze_chunk_results.py       # Analysis & viz
│   └── run_chunk_comparison.py        # Master orchestration
├── scripts/
│   └── run_chunk_comparison.sh        # Shell wrapper
├── configs/
│   └── collection_tags/
│       ├── fiqa_para_50k.json
│       ├── fiqa_sent_50k.json
│       └── fiqa_win256_o64_50k.json
└── reports/
    ├── winners_chunk.json             ⭐ Main deliverable
    ├── chunk_recommendations.txt
    ├── chunk_charts/
    │   ├── pareto_quality_latency.png
    │   └── index_metrics.png
    └── chunk_health/
        └── health_summary.json
```

---

## Next Steps

1. **Run pipeline**: `bash scripts/run_chunk_comparison.sh --api-url http://andy-wsl:8000`
2. **Review winners**: `cat reports/winners_chunk.json`
3. **Read recommendations**: `cat reports/chunk_recommendations.txt`
4. **View charts**: `open reports/chunk_charts/pareto_quality_latency.png`
5. **Deploy winner**: Update API config with winning collection

---

## Documentation

- 📘 **Full README**: `reports/CHUNK_COMPARISON_README.md`
- 📋 **Delivery Report**: `reports/CHUNK_COMPARISON_DELIVERY.md`
- ⚡ **This Quickstart**: `experiments/CHUNK_COMPARISON_QUICKSTART.md`

---

## Support

Questions? Issues?
1. Check `reports/chunk_health/` for health check failures
2. Review console logs for errors
3. Inspect `reports/chunk_experiments_*.json` for detailed results
4. See full documentation in `reports/CHUNK_COMPARISON_README.md`

---

**Status**: ✅ Ready to run  
**Time**: ~50 min (full), ~10 min (fast test)  
**Output**: `reports/winners_chunk.json` + charts + recommendations

