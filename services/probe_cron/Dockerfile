FROM searchforge-base:py311
WORKDIR /app

COPY services/probe_cron/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}

COPY services/probe_cron/ /app
CMD ["python","app.py"]
