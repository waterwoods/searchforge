# Final Docker/Deps Audit
Mon Sep 29 14:12:47 PDT 2025

## 0) Context
no git

## 1) constraints vs requirements coherence
requirements.txt (should be only: -r constraints.txt)
-r constraints.txt

constraints.txt (pinned list; must NOT contain -r constraints.txt)
numpy<2
transformers==4.33.3
sentence-transformers==2.2.2
qdrant-client==1.7.3
uvicorn==0.23.2
fastapi==0.103.2
prometheus-client==0.20.0
requests==2.31.0
httpx==0.25.2
pydantic==2.5.0
OK: no self-include in constraints

## 2) Dockerfiles pip flags & constraints usage
---- docker/base/Dockerfile
    pip install --no-cache-dir --no-compile --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-compile --index-url https://download.pytorch.org/whl/cpu \
    pip install --no-cache-dir --no-compile -c ${CONSTRAINTS_FILE} \
---- services/auto_tuner/Dockerfile
    pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
---- services/chaos_injector/Dockerfile
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}
---- services/probe_cron/Dockerfile
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}
---- services/rag_api/Dockerfile
    pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
---- services/shadow_proxy/Dockerfile
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}

## 3) Heavy deps leaking into services (should be absent)
OK: no heavy deps in service requirements

## 4) Service requirements snapshot
---- services/auto_tuner/requirements.txt
requests
---- services/chaos_injector/requirements.txt
---- services/probe_cron/requirements.txt
requests
---- services/rag_api/requirements.txt
fastapi==0.103.2
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.25.2
prometheus-client==0.20.0
qdrant-client==1.7.3
---- services/shadow_proxy/requirements.txt
httpx

## 5) Entrypoint/port/healthcheck alignment
---- services/auto_tuner/Dockerfile
CMD ["python","controller.py"]
---- services/chaos_injector/Dockerfile
EXPOSE 8084
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8084"]
---- services/probe_cron/Dockerfile
CMD ["python","app.py"]
---- services/rag_api/Dockerfile
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000","--workers","2"]
---- services/shadow_proxy/Dockerfile
EXPOSE 8083
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8083"]
rag_api /health route presence:
WARN: /health not found

## 6) Compose drift & volumes
image tags using :latest (should pin) :
OK: no :latest
models volume mount presence:
NOTE: models volume not found in compose (ensure models are prewarmed or mounted)
ports/depends_on:

## 7) Model download at startup (risk of slow/unstable boot)
OK: no obvious startup downloads
Tip: ensure HF cache/paths point to mounted dir (e.g., /app/models) to avoid network download.

## 8) Runtime writes (should be on volumes, not image layer)
OK: no obvious writes
Check mounts for: /app/logs /app/models /root/.cache /tmp

## 9) .dockerignore & build context bloat
---- .dockerignore (head)
.git/
__pycache__/
*.pyc
*.pyo
.DS_Store
.env
data/
reports/
*.ipynb
## 10) Images/containers/health
images (searchforge*)
searchforge-auto-tuner     latest     1.53GB
searchforge-rag-api        latest     1.56GB
searchforge-base           py310      1.53GB
compose ps
NAME                       IMAGE                                                                     COMMAND                  SERVICE      CREATED             STATUS                       PORTS
searchforge-auto-tuner-1   sha256:6a55ec8a86a7d544c16eaa3dc6caaac0efee4cdf4b25562c5c8f24f4fbe3a150   "python controller.py"   auto-tuner   About an hour ago   Up About an hour             
searchforge-qdrant-1       qdrant/qdrant:v1.11.0                                                     "./entrypoint.sh"        qdrant       About an hour ago   Up About an hour             0.0.0.0:6333->6333/tcp, 6334/tcp
searchforge-rag-api-1      sha256:348b0e8027cd2318784d20371cb0438a4453748def2381785933ea60bbe1b20a   "uvicorn app:app --h…"   rag-api      About an hour ago   Up About an hour (healthy)   0.0.0.0:8000->8000/tcp
health check (rag-api)
{"status":"healthy","features":{"bandit_routing":false,"standard_routing":true},"routing_method":"standard","collections":["amazon_electronics_100k","amazon_reviews_hybrid"]}