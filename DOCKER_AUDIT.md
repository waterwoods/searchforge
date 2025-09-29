# Docker Audit Report
Mon Sep 29 13:58:32 PDT 2025

## 1) ENTRYPOINT/CMD/ports/healthcheck
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
---- docker-compose.yml (ports & image tags)
7:    image: searchforge-base:py310
9:    image: qdrant/qdrant:v1.11.0
11:    ports: ["6333:6333"]
21:    ports: ["8000:8000"]
22:    depends_on: [ qdrant ]
28:    depends_on: [ rag-api ]

## 2) /health 路由存在性 (rag_api)
153:async def health_check():

## 3) 模型/嵌入是否会在启动时下载
提示: 请确认这些调用是否读取挂载目录(~/ssx-lab/models)或已预热, 否则会联网下载

## 4) constraints 与 pip install 一致性
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
---- docker/base/Dockerfile
    pip install --no-cache-dir --no-compile --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-compile --index-url https://download.pytorch.org/whl/cpu \
    pip install --no-cache-dir --no-compile -c /opt/constraints.txt \
WARN: missing `-c ${CONSTRAINTS_FILE}`

## 5) .dockerignore 与构建上下文体积
---- .dockerignore
.git/
__pycache__/
*.pyc
*.pyo
.DS_Store
.env
data/
reports/
*.ipynb
工作区体积(排除 .git/node_modules/models/data/reports)
4.0K	DOCKER_AUDIT.md
4.0K	Makefile
4.0K	README.md
4.0K	REPORT.md
4.0K	constraints.txt
4.0K	docker
4.0K	docker-compose.yml
8.0K	eval
4.0K	infra
4.0K	manifests
108K	modules
 24K	reports
4.0K	requirements.txt
 12K	run_ab_30m_evaluation.py
  0B	scripts
 68K	services

## 6) :latest 漂移风险
No :latest found or compose missing

## 7) 运行时写入位置
检查常见写入路径(需你手动确认是否挂卷): /app/logs, /tmp, /root/.cache, /app/models
services/rag_api/app.py:18:logging.basicConfig(level=logging.INFO)

## 8) 快速镜像/容器状态
---- docker images (searchforge*)
searchforge-auto-tuner     latest     1.53GB
searchforge-rag-api        latest     1.56GB
searchforge-base           py310      1.53GB
---- docker compose ps
NAME                       IMAGE                                                                     COMMAND                  SERVICE      CREATED             STATUS                    PORTS
searchforge-auto-tuner-1   sha256:6a55ec8a86a7d544c16eaa3dc6caaac0efee4cdf4b25562c5c8f24f4fbe3a150   "python controller.py"   auto-tuner   58 minutes ago      Up 58 minutes             
searchforge-qdrant-1       qdrant/qdrant:v1.11.0                                                     "./entrypoint.sh"        qdrant       About an hour ago   Up About an hour          0.0.0.0:6333->6333/tcp, 6334/tcp
searchforge-rag-api-1      sha256:348b0e8027cd2318784d20371cb0438a4453748def2381785933ea60bbe1b20a   "uvicorn app:app --h…"   rag-api      58 minutes ago      Up 58 minutes (healthy)   0.0.0.0:8000->8000/tcp

Done. Open DOCKER_AUDIT.md
