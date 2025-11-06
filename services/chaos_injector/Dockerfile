FROM searchforge-base:py310
WORKDIR /app

COPY services/chaos_injector/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}

COPY services/chaos_injector/ /app
EXPOSE 8084
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8084"]
