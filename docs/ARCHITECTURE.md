# Smart Bakhmach IoT Architecture

## System Overview
Microservices-based IoT platform with event-driven communication

## Key Services
- **API Gateway (FastAPI)** - Port 8000 - Request routing, auth, rate limiting
- **Energy Service** - Port 8001 - Smart meters, load balancing, forecasting
- **Water Service** - Port 8002 - Flow monitoring, leak detection
- **Transport Service** - Port 8003 - GPS tracking, route optimization
- **Environment Service** - Port 8004 - Air quality, pollution monitoring
- **Analytics Service** - Port 8005 - ML models, predictions, anomaly detection

## Data Flow
Sensors → Message Broker (RabbitMQ/Kafka) → Services → PostgreSQL/Redis
              ↓
         Analytics Engine → Insights & Alerts

## Technology Stack
- Backend: FastAPI, Python 3.11+
- Database: PostgreSQL 15+
- Message Broker: RabbitMQ 3.12+ or Kafka 3.5+
- Caching: Redis 7.0+
- Auth: JWT (PyJWT)
- ML: scikit-learn, TensorFlow
- Container: Docker 24.0+
- Orchestration: Kubernetes 1.28+
- Monitoring: Prometheus, Grafana

## Deployment
- **Development**: Docker Compose
- **Production**: Kubernetes with Istio service mesh

For detailed architecture, see DEPLOYMENT.md
