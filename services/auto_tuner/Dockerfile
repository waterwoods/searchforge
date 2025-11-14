FROM searchforge-base:py311
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

COPY services/auto_tuner/requirements.txt /app/requirements.txt
RUN if [ -s /app/requirements.txt ]; then \
    pip install --no-cache-dir --no-compile -r /app/requirements.txt -c ${CONSTRAINTS_FILE}; \
    fi

COPY services/auto_tuner/ /app/
CMD ["python","controller.py"]
