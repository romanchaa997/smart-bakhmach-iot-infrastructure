# API Reference Guide

## Authentication

### POST /api/v1/auth/token
Login and obtain JWT access token.

**Request Body (form-data):**
```
username: string (required)
password: string (required)
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true
}
```

### GET /api/v1/auth/me
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "username": "john_doe",
  "role": "user"
}
```

## Energy Management

### POST /api/v1/meters
Register a new smart meter.

**Request Body:**
```json
{
  "meter_id": "METER001",
  "location": "Main Street 123",
  "meter_type": "three_phase",
  "status": "active"
}
```

### GET /api/v1/meters
Get all registered smart meters.

### POST /api/v1/readings
Submit an energy reading.

**Request Body:**
```json
{
  "meter_id": "METER001",
  "voltage": 230.5,
  "current": 15.2,
  "power_consumption": 3500.0,
  "energy_total": 12500.0,
  "power_factor": 0.95
}
```

### GET /api/v1/readings/{meter_id}
Get energy readings for a specific meter.

**Query Parameters:**
- `limit`: Number of readings to return (default: 100)

### GET /api/v1/analytics/consumption
Get energy consumption analytics.

**Query Parameters:**
- `meter_id`: Filter by specific meter (optional)
- `days`: Number of days to analyze (default: 7)

## Water Management

### POST /api/v1/sensors
Register a new water sensor.

### GET /api/v1/sensors
Get all registered water sensors.

### POST /api/v1/readings
Submit a water reading.

**Request Body:**
```json
{
  "sensor_id": "WATER001",
  "flow_rate": 25.5,
  "pressure": 4.2,
  "temperature": 18.5,
  "leak_detected": false
}
```

### GET /api/v1/readings/{sensor_id}
Get water readings for a specific sensor.

### GET /api/v1/leaks
Get recent leak detections.

**Query Parameters:**
- `days`: Number of days to check (default: 7)

### GET /api/v1/analytics/consumption
Get water consumption analytics.

## Transport Service

### POST /api/v1/vehicles
Register a new vehicle.

**Request Body:**
```json
{
  "vehicle_id": "BUS001",
  "vehicle_type": "bus",
  "route_id": "ROUTE5",
  "capacity": 50,
  "status": "active"
}
```

### GET /api/v1/vehicles
Get all registered vehicles.

### POST /api/v1/telemetry
Submit vehicle telemetry.

**Request Body:**
```json
{
  "vehicle_id": "BUS001",
  "latitude": 51.0937,
  "longitude": 32.3544,
  "speed": 45.5,
  "fuel_level": 75.0,
  "passengers": 32
}
```

### GET /api/v1/vehicles/live
Get live positions of all active vehicles.

### POST /api/v1/optimize/route
Optimize route based on waypoints.

**Request Body:**
```json
{
  "waypoints": [
    {"latitude": 51.0937, "longitude": 32.3544, "name": "Stop 1"},
    {"latitude": 51.0945, "longitude": 32.3560, "name": "Stop 2"},
    {"latitude": 51.0920, "longitude": 32.3570, "name": "Stop 3"}
  ]
}
```

## Air Quality Service

### POST /api/v1/stations
Register a new air quality station.

**Request Body:**
```json
{
  "station_id": "AQ001",
  "location": "Central Park",
  "latitude": 51.0937,
  "longitude": 32.3544,
  "status": "active"
}
```

### GET /api/v1/stations
Get all air quality stations.

### POST /api/v1/readings
Submit an air quality reading.

**Request Body:**
```json
{
  "station_id": "AQ001",
  "pm25": 15.2,
  "pm10": 25.5,
  "co2": 415.0,
  "co": 0.5,
  "no2": 25.0,
  "o3": 45.0,
  "temperature": 22.5,
  "humidity": 65.0
}
```

### GET /api/v1/current
Get current air quality conditions from all stations.

### GET /api/v1/analytics/trends
Get air quality trends.

**Query Parameters:**
- `station_id`: Filter by specific station (optional)
- `days`: Number of days to analyze (default: 7)

## ML Analytics Service

### POST /api/v1/predict/energy
Predict future energy consumption.

**Request Body:**
```json
{
  "service_type": "energy",
  "entity_id": "METER001",
  "prediction_type": "consumption_24h",
  "historical_days": 30
}
```

### POST /api/v1/predict/water
Predict water leak probability.

### POST /api/v1/predict/transport
Predict passenger demand.

### POST /api/v1/predict/airquality
Predict future air quality index.

### GET /api/v1/predictions/{service_type}
Get historical predictions.

**Query Parameters:**
- `entity_id`: Filter by specific entity (optional)
- `limit`: Number of predictions to return (default: 50)

### GET /api/v1/analytics/accuracy
Get model accuracy metrics.

**Query Parameters:**
- `service_type`: Service type (required)
- `days`: Number of days to analyze (default: 7)

## Common Response Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Error Response Format

```json
{
  "detail": "Error message description"
}
```
