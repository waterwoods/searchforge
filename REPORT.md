# SearchForge Audit (local)
Mon Sep 29 13:00:56 PDT 2025

## Files present
constraints.txt
docker-compose.yml
requirements.txt
services/rag_api/Dockerfile
services/rag_api/requirements.txt
services/auto_tuner/Dockerfile

## Grep red flags
grep: cuda|cudnn|nvidia|triton|torchvision

## constraints.txt (head)
numpy<2
transformers==4.33.3
sentence-transformers==2.2.2
qdrant-client==1.7.3
uvicorn==0.23.2
fastapi==0.103.2
prometheus-client==0.20.0

## Root requirements.txt
--index-url https://download.pytorch.org/whl/cpu
torch==2.1.0+cpu
fastapi
uvicorn
prometheus-client
qdrant-client
sentence-transformers
numpy<2
transformers==4.33.3


## rag_api requirements.txt
fastapi==0.103.2
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.25.2
prometheus-client==0.20.0
qdrant-client==1.7.3
sentence-transformers==2.2.2
transformers==4.33.3
numpy<2

## rag_api Dockerfile
FROM searchforge-base:py310
WORKDIR /app
ENV PYTHONPATH=/app PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY services/rag_api/requirements.txt /app/requirements.txt
RUN if [ -s /app/requirements.txt ]; then \
      pip install --no-cache-dir -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
    fi
COPY services/rag_api/ /app/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000","--workers","2"]

## auto_tuner Dockerfile
FROM searchforge-base:py310
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

COPY services/auto_tuner/requirements.txt /app/requirements.txt
RUN if [ -s /app/requirements.txt ]; then \
      pip install --no-cache-dir -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
    fi

COPY services/auto_tuner/ /app/
CMD ["python","controller.py"]

## docker-compose services
2:services:

## Docker images (sizes)
REPOSITORY                   TAG          IMAGE               ID
searchforge-auto-tuner       latest       6a55ec8a86a7 ago      About
searchforge-rag-api          latest       348b0e8027cd ago      About
searchforge-base             py310        cbadf2954a98 1.53GB   2

## Compose ps
NAME                       IMAGE                    COMMAND                  SERVICE      CREATED          STATUS                    PORTS
searchforge-auto-tuner-1   searchforge-auto-tuner   "python controller.py"   auto-tuner   24 seconds ago   Up 23 seconds             
searchforge-qdrant-1       qdrant/qdrant:v1.11.0    "./entrypoint.sh"        qdrant       10 minutes ago   Up 10 minutes             0.0.0.0:6333->6333/tcp, 6334/tcp
searchforge-rag-api-1      searchforge-rag-api      "uvicorn app:app --h…"   rag-api      25 seconds ago   Up 24 seconds (healthy)   0.0.0.0:8000->8000/tcp

## rag-api site-packages top 12 (MB)
  369.7 MB  torch
  102.3 MB  scipy
   55.3 MB  transformers
   48.5 MB  sklearn
   47.4 MB  sympy
   43.7 MB  torch.libs
   27.3 MB  numpy
   26.6 MB  scipy.libs
   26.0 MB  numpy.libs
   17.7 MB  tokenizers
   15.0 MB  grpc
   12.8 MB  pillow.libs

## Heuristics
- torch/transformers pinned via constraints? ✔ if present above
- rag_api requirements should NOT include torch/torchvision: check above
- No torchvision, cuda/cudnn/triton/nvidia in repo: see grep
- Base image exists and reused: see images list for searchforge-base:py310


Done. Open REPORT.md
