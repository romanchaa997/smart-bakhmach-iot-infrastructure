# IoT Smart City Platform - Project Summary

## Overview

A production-ready, comprehensive IoT smart city infrastructure platform built with microservices architecture, featuring:

- **Energy Management** with smart meter monitoring
- **Water Management** with leak detection
- **Transport Optimization** with vehicle tracking
- **Air Quality Monitoring** with environmental sensors
- **ML Predictive Analytics** with forecasting capabilities

## Architecture

### Microservices (6 services)

1. **API Gateway** (Port 8000)
   - JWT authentication & authorization
   - User management
   - Central routing
   - Service discovery

2. **Energy Service** (Port 8001)
   - Smart meter registry
   - Real-time power consumption monitoring
   - Anomaly detection
   - Historical analytics
   - Consumption predictions

3. **Water Service** (Port 8002)
   - Water sensor management
   - Flow rate & pressure monitoring
   - Automatic leak detection
   - Alert system
   - Leak risk predictions

4. **Transport Service** (Port 8003)
   - Vehicle fleet management
   - Real-time GPS tracking
   - Route optimization (nearest neighbor algorithm)
   - Passenger demand analysis
   - Fuel monitoring

5. **Air Quality Service** (Port 8004)
   - Monitoring station registry
   - Multi-pollutant tracking (PM2.5, PM10, CO2, CO, NO2, O3)
   - AQI calculation
   - Temperature & humidity monitoring
   - Air quality forecasting

6. **ML Analytics Service** (Port 8005)
   - Energy consumption forecasting (Linear Regression)
   - Water leak probability prediction (Random Forest)
   - Transport demand prediction
   - Air quality forecasting
   - Model accuracy tracking

### Infrastructure Components

- **PostgreSQL 15** - Primary database with optimized schema
- **Apache Kafka** - Event streaming platform
- **MQTT (Mosquitto)** - IoT device communication
- **Docker & Docker Compose** - Containerization
- **GitHub Actions** - CI/CD pipeline

## Key Features

### Authentication & Security
- JWT-based authentication with configurable expiration
- Bcrypt password hashing
- Role-based access control (admin/user)
- SQL injection protection
- CORS configuration

### Event-Driven Architecture
- 13+ Kafka topics for inter-service communication
- MQTT topics for IoT device data ingestion
- Async message processing
- Real-time event publishing

### Database Schema
- 11 core tables with proper indexing
- Time-series data optimization
- Prediction storage
- Alert management
- User authentication

### RESTful APIs
- OpenAPI/Swagger documentation
- Consistent response formats
- Proper HTTP status codes
- Pagination support
- Query filtering

### ML Capabilities
- Linear Regression for time-series forecasting
- Random Forest for classification
- Confidence scoring
- Model accuracy metrics
- Historical prediction tracking

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM and database toolkit
- **Pydantic** - Data validation
- **Python-Jose** - JWT handling
- **Passlib** - Password hashing

### ML/Analytics
- **Scikit-learn** - Machine learning
- **NumPy** - Numerical computing
- **Pandas** - Data analysis

### Messaging
- **AIOKafka** - Async Kafka client
- **Paho MQTT** - MQTT protocol

### Infrastructure
- **PostgreSQL** - Relational database
- **Kafka + Zookeeper** - Event streaming
- **Mosquitto** - MQTT broker
- **Docker** - Containerization

## File Structure

```
├── .github/workflows/
│   └── ci-cd.yml              # CI/CD pipeline
├── config/
│   └── mosquitto.conf         # MQTT broker config
├── docs/
│   ├── API_REFERENCE.md       # Complete API documentation
│   └── DEPLOYMENT.md          # Deployment guide
├── scripts/
│   └── init-db.sql            # Database initialization
├── services/
│   ├── api-gateway/           # API Gateway service
│   ├── energy-service/        # Energy management
│   ├── water-service/         # Water management
│   ├── transport-service/     # Transport optimization
│   ├── air-quality-service/   # Air quality monitoring
│   └── ml-analytics-service/  # ML analytics
├── shared/
│   ├── auth/                  # JWT authentication
│   ├── database/              # Database connection
│   ├── messaging/             # Kafka & MQTT clients
│   └── config.py              # Shared configuration
├── tests/
│   └── test_api_gateway.py    # Example tests
├── docker-compose.yml         # Service orchestration
├── requirements.txt           # Python dependencies
├── Makefile                   # Common operations
├── .env.example               # Environment template
└── README.md                  # Main documentation
```

## API Endpoints Summary

### Authentication
- POST `/api/v1/auth/token` - Login
- POST `/api/v1/auth/register` - Register
- GET `/api/v1/auth/me` - Current user

### Energy Management
- POST/GET `/api/v1/meters` - Meter management
- POST/GET `/api/v1/readings` - Energy readings
- GET `/api/v1/analytics/consumption` - Analytics

### Water Management
- POST/GET `/api/v1/sensors` - Sensor management
- POST/GET `/api/v1/readings` - Water readings
- GET `/api/v1/leaks` - Leak alerts
- GET `/api/v1/analytics/consumption` - Analytics

### Transport
- POST/GET `/api/v1/vehicles` - Vehicle management
- POST/GET `/api/v1/telemetry` - GPS tracking
- GET `/api/v1/vehicles/live` - Live positions
- POST `/api/v1/optimize/route` - Route optimization

### Air Quality
- POST/GET `/api/v1/stations` - Station management
- POST/GET `/api/v1/readings` - AQ readings
- GET `/api/v1/current` - Current conditions
- GET `/api/v1/analytics/trends` - Trends

### ML Analytics
- POST `/api/v1/predict/energy` - Energy forecasting
- POST `/api/v1/predict/water` - Leak prediction
- POST `/api/v1/predict/transport` - Demand prediction
- POST `/api/v1/predict/airquality` - AQI forecasting
- GET `/api/v1/predictions/{service}` - Historical predictions
- GET `/api/v1/analytics/accuracy` - Model metrics

## Deployment

### Quick Start
```bash
docker-compose up -d
```

### Default Credentials
- Username: `admin`
- Password: `admin123`

### Ports
- 8000: API Gateway
- 8001: Energy Service
- 8002: Water Service
- 8003: Transport Service
- 8004: Air Quality Service
- 8005: ML Analytics Service
- 5432: PostgreSQL
- 9092: Kafka
- 1883: MQTT

## Event Topics

### Kafka Events
- Device registration events (meter.created, etc.)
- Reading events (energy.reading, etc.)
- Alert events (energy.alert, water.leak.alert, etc.)
- Prediction events (ml.prediction)

### MQTT Topics
- energy/meters/+/reading
- water/sensors/+/reading
- transport/vehicles/+/telemetry
- airquality/stations/+/reading

## Testing

```bash
# Run all tests
pytest tests/ --cov=services

# Lint code
flake8 services/ shared/

# Format code
black services/ shared/
```

## CI/CD Pipeline

GitHub Actions workflow includes:
1. **Test** - Python linting and pytest
2. **Build** - Docker image building
3. **Security Scan** - Trivy vulnerability scanning
4. **Deploy** - Automated deployment (configurable)

## Performance Considerations

- Database indexes on timestamp + entity_id columns
- Async message processing with Kafka
- Connection pooling for database
- Efficient time-series data storage
- Optimized SQL queries with proper joins

## Security Features

- JWT tokens with expiration
- Bcrypt password hashing (12 rounds)
- Parameterized SQL queries
- CORS middleware
- Role-based access control
- Environment variable configuration

## Scalability

- Stateless microservices (horizontal scaling)
- Event-driven architecture (decoupled services)
- Database connection pooling
- Kafka for high-throughput messaging
- Docker orchestration ready (K8s compatible)

## Future Enhancements

- WebSocket support for real-time updates
- Advanced ML models (LSTM, Prophet)
- Blockchain integration
- Mobile applications
- Advanced visualization dashboards
- Multi-tenancy support
- API rate limiting
- Redis caching layer

## Documentation

- **README.md** - Quick start and overview
- **docs/API_REFERENCE.md** - Complete API documentation
- **docs/DEPLOYMENT.md** - Detailed deployment guide
- **Inline code comments** - Throughout codebase
- **OpenAPI/Swagger** - Interactive API docs at /docs endpoints

## Quality Assurance

- Type hints throughout Python code
- Pydantic models for validation
- Error handling and proper status codes
- Health check endpoints
- Logging infrastructure ready
- Test structure in place

## License

MIT License - See LICENSE file

## Contact

- GitHub: romanchaa997/smart-bakhmach-iot-infrastructure
- Email: admin@bakhmach.ua
