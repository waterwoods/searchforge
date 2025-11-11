FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:${PYTHONPATH} \
    SENTENCE_TRANSFORMERS_HOME=/app/models \
    HF_HOME=/app/models \
    TRANSFORMERS_CACHE=/app/models \
    MPLBACKEND=Agg \
    UVICORN_WORKERS=${UVICORN_WORKERS:-1} \
    MAIN_PORT=${MAIN_PORT:-8000}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    build-essential \
    git \
    jq \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# 1) 安装 CPU 版 torch（固定 CPU index，绝不装 CUDA）
# DO NOT INSTALL CUDA/TORCH-CUDA - This is a CPU-only service
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1

# 2) 安装项目依赖（不包含 torch；如需 sbert/fastembed 在 requirements.txt 中）
COPY services/rag_api/requirements.txt /app/requirements.txt
RUN python -m pip install -U pip && \
    PIP_EXTRA_INDEX_URL="" \
    pip install --no-cache-dir --no-compile -r /app/requirements.txt

# 3) 复制源代码
COPY services/rag_api/ /app/
COPY modules/ /app/modules/
COPY engines/ /app/engines/
COPY interfaces/ /app/interfaces/
COPY agents/ /app/agents/
COPY services/fiqa_api/ /app/services/fiqa_api/
COPY services/core/ /app/services/core/
COPY services/plugins/ /app/services/plugins/
COPY services/api/ /app/services/api/
COPY services/routers/ /app/services/routers/
COPY routes/ /app/routes/
COPY orchestrators/ /app/orchestrators/
COPY services/code_intelligence/ /app/services/code_intelligence/
COPY services/black_swan/ /app/services/black_swan/
COPY tools/ /app/tools/
COPY experiments/ /app/experiments/

# 4) CUDA 守门：若 pip freeze 出现 nvidia/torch-cuda 直接失败
RUN set -eux; \
    pip freeze | tee /tmp/freeze.txt; \
    if egrep -i '^(nvidia|torch[-_]?cuda)' /tmp/freeze.txt; then \
    echo 'ERROR: CUDA-related packages detected'; exit 1; \
    else echo 'OK-no-CUDA'; fi

# 5) 验证 torch 是 CPU-only
RUN python - <<'PY'
import torch
cuda_version = getattr(torch.version, "cuda", None)
if cuda_version is not None:
    print(f"ERROR: torch has CUDA support: {cuda_version}", file=__import__('sys').stderr)
    exit(1)
assert not torch.cuda.is_available(), "CUDA should not be available"
print("✅ torch is CPU-only (no CUDA)")
PY

# Expose port
EXPOSE 8000

# 6) 健康检查，给足启动宽限
HEALTHCHECK --interval=5s --timeout=2s --start-period=25s --retries=10 \
    CMD curl -fsS "http://127.0.0.1:${MAIN_PORT}/health" || exit 1

# Use tini as entrypoint and run uvicorn
ENTRYPOINT ["tini", "--"]
CMD ["sh","-lc","python -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port ${MAIN_PORT:-8000} --workers ${UVICORN_WORKERS}"]
