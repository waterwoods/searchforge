FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# 仍挂载源代码便于热更；镜像内也预留一份以备挂载缺失时可用

COPY . /app

EXPOSE 8000

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]


