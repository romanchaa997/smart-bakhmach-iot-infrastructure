FROM python:3.11-slim

WORKDIR /app

COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../shared /app/shared
COPY . /app/services/ml-analytics-service

WORKDIR /app/services/ml-analytics-service

EXPOSE 8005

CMD ["python", "main.py"]
