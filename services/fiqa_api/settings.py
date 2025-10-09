"""
Configuration for FIQA API - Environment-driven settings
"""
import os

# Rate Limiting (environment-configurable)
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "3"))
RATE_LIMIT_WINDOW = float(os.getenv("RATE_LIMIT_WINDOW_SEC", "1.0"))

# API Version and Feature Flags
API_VERSION = os.getenv("API_VERSION", "v1.0.0-fiqa")
DISABLE_AUTOTUNER = int(os.getenv("DISABLE_AUTOTUNER", "1"))  # Default: disabled

# Metrics
METRICS_WINDOW = 60  # rolling window in seconds for metrics

# Server
API_TITLE = "FIQA API"

