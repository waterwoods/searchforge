FROM searchforge-base:py310
WORKDIR /app

COPY services/shadow_proxy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}

COPY services/shadow_proxy/ /app
EXPOSE 8083
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8083"]
