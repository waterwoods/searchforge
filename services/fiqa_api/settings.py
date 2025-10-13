"""
Configuration for FIQA API - Environment-driven settings
"""
import os

# Rate Limiting (environment-configurable)
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "3"))
RATE_LIMIT_WINDOW = float(os.getenv("RATE_LIMIT_WINDOW_SEC", "1.0"))
RATE_LIMIT_WINDOW_SEC = RATE_LIMIT_WINDOW  # Alias for clarity

# API Version and Feature Flags
API_VERSION = os.getenv("API_VERSION", "v1.0.0-fiqa")
DISABLE_AUTOTUNER = int(os.getenv("DISABLE_AUTOTUNER", "1"))  # Default: disabled

# Metrics
METRICS_WINDOW = 60  # rolling window in seconds for metrics

# Server
API_TITLE = "FIQA API"

# Qdrant Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "beir_fiqa_full_ta")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
ENABLE_PAGE_INDEX = os.getenv("ENABLE_PAGE_INDEX", "True").lower() == "true"

# Reranker Configuration
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "True").lower() == "true"
RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "6"))  # Reduced to lower per-request cost
CANDIDATE_K_MAX = int(os.getenv("CANDIDATE_K_MAX", "50"))
RERANK_TIMEOUT_MS = int(os.getenv("RERANK_TIMEOUT_MS", "2000"))  # 2s timeout after warmup
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./models")

# Selective Reranking (control hit rate to 15-30%)
RERANK_SELECTIVE_MODE = os.getenv("RERANK_SELECTIVE_MODE", "True").lower() == "true"
RERANK_MIN_QUERY_LENGTH = int(os.getenv("RERANK_MIN_QUERY_LENGTH", "15"))  # 最少字符数
RERANK_SAMPLE_RATE = float(os.getenv("RERANK_SAMPLE_RATE", "0.25"))  # 25% 采样率

# AutoTuner Configuration
AUTOTUNER_ENABLED = os.getenv("AUTOTUNER_ENABLED", "True").lower() == "true"
AUTOTUNER_TICK_SEC = int(os.getenv("AUTOTUNER_TICK_SEC", "10"))
AUTOTUNER_TARGET_P95_MS = float(os.getenv("AUTOTUNER_TARGET_P95_MS", "200"))
AUTOTUNER_MIN_DELTA_RECALL = float(os.getenv("AUTOTUNER_MIN_DELTA_RECALL", "0.05"))
AUTOTUNER_BUCKET_SEC = int(os.getenv("AUTOTUNER_BUCKET_SEC", "10"))
CANARY_ON_PCT = int(os.getenv("CANARY_ON_PCT", "10"))

# Judger Configuration
JUDGE_PASS_RATE = float(os.getenv("JUDGE_PASS_RATE", "0.7"))
JUDGE_DEFAULT_N = int(os.getenv("JUDGE_DEFAULT_N", "20"))

# Reranker v2 - Selective Triggering with Budget & Fallback
RR_MIN_QUERY_LEN = int(os.getenv("RR_MIN_QUERY_LEN", "3"))  # 进一步降低要求
RR_KEYWORDS = os.getenv("RR_KEYWORDS", "etf,yield,roi,apr,401k,bond,inflation,tax,credit,mortgage,invest,retire,fund,stock,portfolio,debt,saving,如何,什么,计算,投资,基金").lower().split(",")
RR_MIN_DISPERSION = float(os.getenv("RR_MIN_DISPERSION", "0.01"))  # 大幅降低分散度要求
RR_MAX_LATENCY_MS = int(os.getenv("RR_MAX_LATENCY_MS", "1800"))  # Conservative upper limit
RR_MAX_HIT_RATE = float(os.getenv("RR_MAX_HIT_RATE", "0.30"))  # Budget brake maintained
RR_WARMUP_REQS = int(os.getenv("RR_WARMUP_REQS", "1"))  # 降低预热要求
RR_COOLDOWN_SEC = int(os.getenv("RR_COOLDOWN_SEC", "10"))
RR_ENABLE_FALLBACK = os.getenv("RR_ENABLE_FALLBACK", "True").lower() == "true"

# Step 3: Demo Tuning - 仅用于演示的参数调优（可恢复）
DEMO_TUNING = os.getenv("DEMO_TUNING", "false").lower() == "true"

if DEMO_TUNING:
    # 演示模式：更激进的参数，增强可见差异
    CANDIDATE_K_MAX = 1500
    RERANK_TOP_K = 20
    RR_MIN_QUERY_LEN = 8
    RR_MIN_DISPERSION = 0.05
    print("🎯 DEMO_TUNING enabled: candidate_k=1500, rerank_top_k=20, min_query_len=8, min_dispersion=0.05")

# Demo Compare Mode - 对比模式强制差异
DEMO_FORCE_DIFF = os.getenv("DEMO_FORCE_DIFF", "false").lower() == "true"
DEMO_QUERIES_PATH = os.getenv("DEMO_QUERIES_PATH", "reports/demo_queries.json")

