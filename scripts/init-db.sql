-- Initialize database schema for IoT Platform

-- Energy Management Tables
CREATE TABLE IF NOT EXISTS smart_meters (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(50) UNIQUE NOT NULL,
    location VARCHAR(200) NOT NULL,
    meter_type VARCHAR(50) NOT NULL,
    installation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS energy_readings (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(50) REFERENCES smart_meters(meter_id),
    timestamp TIMESTAMP NOT NULL,
    voltage FLOAT,
    current FLOAT,
    power_consumption FLOAT NOT NULL,
    energy_total FLOAT,
    power_factor FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_energy_readings_meter_timestamp ON energy_readings(meter_id, timestamp DESC);

-- Water Management Tables
CREATE TABLE IF NOT EXISTS water_sensors (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) UNIQUE NOT NULL,
    location VARCHAR(200) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    installation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS water_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES water_sensors(sensor_id),
    timestamp TIMESTAMP NOT NULL,
    flow_rate FLOAT,
    pressure FLOAT,
    temperature FLOAT,
    leak_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_water_readings_sensor_timestamp ON water_readings(sensor_id, timestamp DESC);

-- Transport Tables
CREATE TABLE IF NOT EXISTS transport_vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    route_id VARCHAR(50),
    capacity INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transport_telemetry (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) REFERENCES transport_vehicles(vehicle_id),
    timestamp TIMESTAMP NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    speed FLOAT,
    fuel_level FLOAT,
    passengers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transport_telemetry_vehicle_timestamp ON transport_telemetry(vehicle_id, timestamp DESC);

-- Air Quality Tables
CREATE TABLE IF NOT EXISTS air_quality_stations (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) UNIQUE NOT NULL,
    location VARCHAR(200) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    installation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS air_quality_readings (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) REFERENCES air_quality_stations(station_id),
    timestamp TIMESTAMP NOT NULL,
    pm25 FLOAT,
    pm10 FLOAT,
    co2 FLOAT,
    co FLOAT,
    no2 FLOAT,
    o3 FLOAT,
    temperature FLOAT,
    humidity FLOAT,
    aqi INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_air_quality_readings_station_timestamp ON air_quality_readings(station_id, timestamp DESC);

-- ML Analytics Tables
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(100) NOT NULL,
    predicted_value FLOAT,
    prediction_metadata JSONB,
    confidence_score FLOAT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_service_entity_timestamp ON predictions(service_type, entity_id, timestamp DESC);

-- Users and Authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts and Notifications
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'active',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_alerts_service_status_timestamp ON alerts(service_type, status, timestamp DESC);

-- Insert sample admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, full_name, role) 
VALUES ('admin', 'admin@bakhmach.ua', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLGj7OYi', 'System Administrator', 'admin')
ON CONFLICT (username) DO NOTHING;
