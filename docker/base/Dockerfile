FROM python:3.10-slim
WORKDIR /opt
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PIP_NO_CACHE_DIR=1
# constraints 进入镜像，所有服务共享同一套版本
COPY constraints.txt /opt/constraints.txt
RUN python -m venv /opt/venv && \
    pip install --no-cache-dir --no-compile --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-compile --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0 && \
    pip install --no-cache-dir --no-compile -c /opt/constraints.txt \
    "numpy<2" transformers==4.33.3 sentence-transformers==2.2.2 \
    qdrant-client==1.7.3 uvicorn==0.23.2 fastapi==0.103.2 \
    prometheus-client==0.20.0
# 让下游镜像可读 constraints
ENV CONSTRAINTS_FILE=/opt/constraints.txt
