FROM python:3.11-slim

WORKDIR /app

COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../shared /app/shared
COPY . /app/services/energy-service

WORKDIR /app/services/energy-service

EXPOSE 8001

CMD ["python", "main.py"]
