FROM python:3.11-slim

WORKDIR /app

COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../shared /app/shared
COPY . /app/services/air-quality-service

WORKDIR /app/services/air-quality-service

EXPOSE 8004

CMD ["python", "main.py"]
