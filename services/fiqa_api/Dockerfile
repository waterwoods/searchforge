FROM searchforge-base:py311

ARG GIT_SHA=unknown
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:${PYTHONPATH} \
    SENTENCE_TRANSFORMERS_HOME=/app/models \
    HF_HOME=/app/models \
    TRANSFORMERS_CACHE=/app/models \
    MPLBACKEND=Agg \
    UVICORN_WORKERS=${UVICORN_WORKERS:-1} \
    MAIN_PORT=${MAIN_PORT:-8000} \
    GIT_SHA=${GIT_SHA}

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

# 1) Install CPU-only torch
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1

# 2) Project dependencies (excluding torch)
COPY services/rag_api/requirements.txt /app/requirements.txt
RUN python -m pip install -U pip && \
    PIP_EXTRA_INDEX_URL="" \
    pip install --no-cache-dir --no-compile -r /app/requirements.txt

# 3) Copy source tree
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
COPY services/autotuner_router.py /app/services/autotuner_router.py
COPY routes/ /app/routes/
COPY orchestrators/ /app/orchestrators/
COPY services/code_intelligence/ /app/services/code_intelligence/
COPY services/black_swan/ /app/services/black_swan/
COPY tools/ /app/tools/
COPY experiments/ /app/experiments/

# 4) Ensure no CUDA packages
RUN set -eux; \
    pip freeze | tee /tmp/freeze.txt; \
    if egrep -i '^(nvidia|torch[-_]?cuda)' /tmp/freeze.txt; then \
    echo 'ERROR: CUDA-related packages detected'; exit 1; \
    else echo 'OK-no-CUDA'; fi

# 5) Verify torch is CPU-only
RUN python - <<'PY'
import torch
cuda_version = getattr(torch.version, "cuda", None)
if cuda_version is not None:
    print(f"ERROR: torch has CUDA support: {cuda_version}", file=__import__('sys').stderr)
    exit(1)
assert not torch.cuda.is_available(), "CUDA should not be available"
print("✅ torch is CPU-only (no CUDA)")
PY

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=2s --start-period=25s --retries=10 \
    CMD curl -fsS "http://127.0.0.1:${MAIN_PORT}/health" || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["sh","-lc","python -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port ${MAIN_PORT:-8000} --workers ${UVICORN_WORKERS}"]

