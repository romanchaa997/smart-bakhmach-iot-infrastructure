FROM python:3.11-slim

WORKDIR /app

COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../shared /app/shared
COPY . /app/services/transport-service

WORKDIR /app/services/transport-service

EXPOSE 8003

CMD ["python", "main.py"]
