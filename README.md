# IoT Smart City Platform - Bakhmach

A comprehensive IoT-based smart city infrastructure platform for Bakhmach featuring energy management with smart meters, water leak detection, transport optimization, air quality monitoring, and ML-driven predictive analytics.

## 🏗️ Architecture

The platform is built using a microservices architecture with the following components:

### Services

1. **API Gateway** (Port 8000) - Central authentication and routing
2. **Energy Management Service** (Port 8001) - Smart meter monitoring
3. **Water Management Service** (Port 8002) - Water flow and leak detection
4. **Transport Service** (Port 8003) - Vehicle tracking and route optimization
5. **Air Quality Service** (Port 8004) - Environmental monitoring
6. **ML Analytics Service** (Port 8005) - Predictive analytics

### Infrastructure

- **PostgreSQL** - Primary database
- **Apache Kafka** - Event streaming
- **MQTT (Mosquitto)** - IoT device communication
- **Docker & Docker Compose** - Containerization

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure.git
cd smart-bakhmach-iot-infrastructure
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to initialize (about 30 seconds)

4. Access the API Gateway:
```bash
curl http://localhost:8000
```

### Default Credentials

- **Username**: admin
- **Password**: admin123

## 📚 API Documentation

Once the services are running, access the interactive API documentation:

- API Gateway: http://localhost:8000/docs
- Energy Service: http://localhost:8001/docs
- Water Service: http://localhost:8002/docs
- Transport Service: http://localhost:8003/docs
- Air Quality Service: http://localhost:8004/docs
- ML Analytics Service: http://localhost:8005/docs

## 🔐 Authentication

The platform uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:

1. **Login** to get a token:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

2. **Use the token** in subsequent requests:
```bash
curl -X GET "http://localhost:8000/api/v1/services" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📊 Features

### Energy Management
- Real-time smart meter monitoring
- Power consumption tracking
- Anomaly detection and alerts
- Historical analytics and trends
- ML-based consumption predictions

### Water Management
- Flow rate monitoring
- Pressure tracking
- Automatic leak detection
- Real-time alerts
- ML-based leak risk predictions

### Transport Optimization
- Real-time vehicle tracking
- Route optimization algorithms
- Passenger demand analysis
- Fuel monitoring
- ML-based demand predictions

### Air Quality Monitoring
- Multi-pollutant tracking (PM2.5, PM10, CO2, etc.)
- AQI calculation and classification
- Temperature and humidity monitoring
- Historical trends
- ML-based air quality forecasting

### ML Predictive Analytics
- Energy consumption forecasting
- Water leak probability prediction
- Transport demand prediction
- Air quality index forecasting
- Model accuracy tracking

## 🔄 Event-Driven Architecture

The platform uses both Kafka and MQTT for event-driven communication:

### Kafka Topics
- `meter.created` - New meter registration
- `energy.reading` - Energy readings
- `energy.alert` - Energy anomaly alerts
- `water.sensor.created` - New sensor registration
- `water.reading` - Water readings
- `water.leak.alert` - Leak detection alerts
- `transport.vehicle.created` - New vehicle registration
- `transport.telemetry` - Vehicle telemetry
- `transport.alert` - Transport alerts
- `airquality.station.created` - New station registration
- `airquality.reading` - Air quality readings
- `airquality.alert` - Air quality alerts
- `ml.prediction` - ML predictions
- `ml.prediction.alert` - ML prediction alerts

### MQTT Topics
- `energy/meters/+/reading` - Smart meter readings
- `water/sensors/+/reading` - Water sensor readings
- `transport/vehicles/+/telemetry` - Vehicle telemetry
- `airquality/stations/+/reading` - Air quality readings

## 🛠️ Development

### Local Development Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file):
```env
DATABASE_URL=postgresql://iotuser:iotpass@localhost:5432/iot_platform
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
JWT_SECRET_KEY=your-secret-key-change-in-production
```

3. Run individual services:
```bash
# API Gateway
python services/api-gateway/main.py

# Energy Service
python services/energy-service/main.py

# And so on...
```

### Running Tests

```bash
pytest tests/ --cov=services
```

### Code Formatting

```bash
black services/ shared/
flake8 services/ shared/
```

## 📦 Database Schema

The platform uses PostgreSQL with the following main tables:

- `smart_meters` - Smart meter registry
- `energy_readings` - Energy consumption data
- `water_sensors` - Water sensor registry
- `water_readings` - Water flow and leak data
- `transport_vehicles` - Vehicle registry
- `transport_telemetry` - Vehicle location and status
- `air_quality_stations` - Air quality station registry
- `air_quality_readings` - Environmental data
- `predictions` - ML prediction results
- `users` - User accounts
- `alerts` - System alerts

## 🔒 Security

- JWT-based authentication with role-based access control
- Password hashing using bcrypt
- SQL injection protection via parameterized queries
- CORS middleware configuration
- API rate limiting (recommended for production)
- HTTPS/TLS support (configure in production)

## 🚀 Deployment

### Production Deployment

1. Update environment variables in `docker-compose.yml`
2. Configure proper secrets management
3. Set up SSL/TLS certificates
4. Configure database backups
5. Set up monitoring and logging
6. Deploy using Docker Compose or Kubernetes

### Kubernetes Deployment

Kubernetes manifests can be generated from Docker Compose:
```bash
kompose convert -f docker-compose.yml
kubectl apply -f .
```

## 📈 Monitoring

The services expose health check endpoints:

```bash
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Energy Service
curl http://localhost:8002/health  # Water Service
curl http://localhost:8003/health  # Transport Service
curl http://localhost:8004/health  # Air Quality Service
curl http://localhost:8005/health  # ML Analytics Service
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Roman Chaaban - Initial work

## 🙏 Acknowledgments

- FastAPI framework
- PostgreSQL database
- Apache Kafka
- Eclipse Mosquitto
- Scikit-learn ML library
- Docker and containerization ecosystem

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure/issues
- Email: admin@bakhmach.ua

## 🗺️ Roadmap

- [ ] Real-time dashboard with WebSocket support
- [ ] Mobile application for citizens
- [ ] Advanced ML models (LSTM, Prophet for time series)
- [ ] Blockchain integration for data integrity
- [ ] Integration with external weather APIs
- [ ] Multi-language support
- [ ] Advanced visualization and reporting
- [ ] Automated alerting and notification system
- [ ] Integration with city infrastructure systems
