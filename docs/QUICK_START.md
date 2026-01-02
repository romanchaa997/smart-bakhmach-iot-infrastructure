# Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites
- Docker Desktop or Docker Engine + Docker Compose
- Git

### 2. Clone and Start
```bash
git clone https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure.git
cd smart-bakhmach-iot-infrastructure
docker-compose up -d
```

### 3. Wait for Services (30 seconds)
```bash
# Watch logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health
```

### 4. Login and Get Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Save the token from the response.

### 5. Make Your First API Call
```bash
# Replace YOUR_TOKEN with the token from step 4
curl -X GET "http://localhost:8000/api/v1/services" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Interactive API Documentation

Open your browser and visit:
- http://localhost:8000/docs - API Gateway
- http://localhost:8001/docs - Energy Service
- http://localhost:8002/docs - Water Service
- http://localhost:8003/docs - Transport Service
- http://localhost:8004/docs - Air Quality Service
- http://localhost:8005/docs - ML Analytics Service

Click "Authorize" button and paste your token to test endpoints interactively!

## Example Usage

### Register a Smart Meter
```bash
curl -X POST "http://localhost:8001/api/v1/meters" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "METER001",
    "location": "Main Street 123",
    "meter_type": "three_phase"
  }'
```

### Submit Energy Reading
```bash
curl -X POST "http://localhost:8001/api/v1/readings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "METER001",
    "voltage": 230.5,
    "current": 15.2,
    "power_consumption": 3500.0,
    "energy_total": 12500.0,
    "power_factor": 0.95
  }'
```

### Get Analytics
```bash
curl -X GET "http://localhost:8001/api/v1/analytics/consumption?meter_id=METER001&days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Predict Future Consumption
```bash
curl -X POST "http://localhost:8005/api/v1/predict/energy" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "energy",
    "entity_id": "METER001",
    "prediction_type": "consumption_24h",
    "historical_days": 30
  }'
```

## Using Makefile

Common operations are available via Makefile:

```bash
make help      # Show all available commands
make up        # Start all services
make down      # Stop all services
make logs      # View all logs
make health    # Check service health
make test      # Run tests
make db-backup # Backup database
```

## Troubleshooting

### Services won't start
```bash
# Check what's using the ports
netstat -tuln | grep -E '8000|8001|8002|8003|8004|8005'

# Remove everything and start fresh
make clean
make up
```

### Can't connect to database
```bash
# Wait a bit longer (PostgreSQL takes time to initialize)
sleep 30

# Check PostgreSQL logs
docker-compose logs postgres
```

### Token expired
```bash
# Just login again to get a new token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## Next Steps

1. Read the [API Reference](API_REFERENCE.md) for all available endpoints
2. Check [Deployment Guide](DEPLOYMENT.md) for production setup
3. Explore interactive docs at http://localhost:8000/docs
4. Add your own sensors and devices
5. Set up MQTT clients to publish sensor data
6. Create custom dashboards using the APIs

## Need Help?

- GitHub Issues: https://github.com/romanchaa997/smart-bakhmach-iot-infrastructure/issues
- Documentation: See the `docs/` folder
- API Documentation: http://localhost:8000/docs (when running)

## Sample Data

Want to test with sample data? Check out the example scripts in `examples/` folder (coming soon) or use the interactive API docs to manually add test data.

Happy coding! 🚀
