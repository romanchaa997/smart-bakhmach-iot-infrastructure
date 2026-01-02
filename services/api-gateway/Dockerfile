FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY ../../requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ../../shared /app/shared

# Copy service code
COPY . /app/services/api-gateway

WORKDIR /app/services/api-gateway

EXPOSE 8000

CMD ["python", "main.py"]
