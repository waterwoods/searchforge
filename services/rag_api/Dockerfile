FROM searchforge-base:py310
WORKDIR /app
ENV PYTHONPATH=/app PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY services/rag_api/requirements.txt /app/requirements.txt
RUN if [ -s /app/requirements.txt ]; then \
    pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
    fi
COPY services/rag_api/ /app/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000","--workers","2"]
