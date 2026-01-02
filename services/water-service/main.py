from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.database.connection import get_db
from shared.auth.jwt_handler import get_current_user
from shared.messaging.kafka_client import kafka_client
from shared.messaging.mqtt_client import mqtt_client

app = FastAPI(
    title="Water Management Service",
    description="Water flow monitoring and leak detection system",
    version="1.0.0"
)


# Pydantic Models
class WaterSensor(BaseModel):
    sensor_id: str
    location: str
    sensor_type: str
    status: str = "active"


class WaterReading(BaseModel):
    sensor_id: str
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    leak_detected: bool = False


# Event handlers
def handle_mqtt_reading(payload: dict):
    """Handle incoming MQTT readings from water sensors"""
    print(f"Received water reading: {payload}")


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    mqtt_client.subscribe("water/sensors/+/reading", handle_mqtt_reading)
    mqtt_client.connect()
    await kafka_client.start_producer()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.disconnect()
    await kafka_client.stop_producer()


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Water Management Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "water-service"}


@app.post("/api/v1/sensors", response_model=dict)
async def create_sensor(
    sensor: WaterSensor,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register a new water sensor"""
    try:
        result = db.execute(
            text("""
                INSERT INTO water_sensors (sensor_id, location, sensor_type, status)
                VALUES (:sensor_id, :location, :sensor_type, :status)
                RETURNING id, sensor_id, location, sensor_type, status, created_at
            """),
            {
                "sensor_id": sensor.sensor_id,
                "location": sensor.location,
                "sensor_type": sensor.sensor_type,
                "status": sensor.status
            }
        )
        db.commit()
        new_sensor = result.fetchone()
        
        await kafka_client.publish("water.sensor.created", {
            "sensor_id": sensor.sensor_id,
            "location": sensor.location,
            "type": sensor.sensor_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "id": new_sensor[0],
            "sensor_id": new_sensor[1],
            "location": new_sensor[2],
            "sensor_type": new_sensor[3],
            "status": new_sensor[4],
            "created_at": new_sensor[5]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/sensors", response_model=List[dict])
async def get_sensors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all water sensors"""
    result = db.execute(text("SELECT * FROM water_sensors ORDER BY created_at DESC"))
    sensors = result.fetchall()
    
    return [
        {
            "id": sensor[0],
            "sensor_id": sensor[1],
            "location": sensor[2],
            "sensor_type": sensor[3],
            "installation_date": sensor[4],
            "status": sensor[5],
            "created_at": sensor[6]
        }
        for sensor in sensors
    ]


@app.post("/api/v1/readings", response_model=dict)
async def create_reading(
    reading: WaterReading,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a water reading"""
    try:
        timestamp = datetime.now(timezone.utc)
        result = db.execute(
            text("""
                INSERT INTO water_readings 
                (sensor_id, timestamp, flow_rate, pressure, temperature, leak_detected)
                VALUES (:sensor_id, :timestamp, :flow_rate, :pressure, :temperature, :leak_detected)
                RETURNING id
            """),
            {
                "sensor_id": reading.sensor_id,
                "timestamp": timestamp,
                "flow_rate": reading.flow_rate,
                "pressure": reading.pressure,
                "temperature": reading.temperature,
                "leak_detected": reading.leak_detected
            }
        )
        db.commit()
        reading_id = result.fetchone()[0]
        
        await kafka_client.publish("water.reading", {
            "sensor_id": reading.sensor_id,
            "flow_rate": reading.flow_rate,
            "leak_detected": reading.leak_detected,
            "timestamp": timestamp.isoformat()
        })
        
        # Alert on leak detection
        if reading.leak_detected:
            await kafka_client.publish("water.leak.alert", {
                "sensor_id": reading.sensor_id,
                "alert_type": "leak_detected",
                "flow_rate": reading.flow_rate,
                "pressure": reading.pressure,
                "timestamp": timestamp.isoformat()
            })
            
            # Store alert in database
            db.execute(
                text("""
                    INSERT INTO alerts 
                    (service_type, entity_id, alert_type, severity, message, timestamp)
                    VALUES (:service_type, :entity_id, :alert_type, :severity, :message, :timestamp)
                """),
                {
                    "service_type": "water",
                    "entity_id": reading.sensor_id,
                    "alert_type": "leak_detected",
                    "severity": "critical",
                    "message": f"Water leak detected at sensor {reading.sensor_id}",
                    "timestamp": timestamp
                }
            )
            db.commit()
        
        return {"id": reading_id, "sensor_id": reading.sensor_id, "timestamp": timestamp}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/readings/{sensor_id}", response_model=List[dict])
async def get_readings(
    sensor_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get water readings for a specific sensor"""
    result = db.execute(
        text("""
            SELECT * FROM water_readings 
            WHERE sensor_id = :sensor_id 
            ORDER BY timestamp DESC 
            LIMIT :limit
        """),
        {"sensor_id": sensor_id, "limit": limit}
    )
    readings = result.fetchall()
    
    return [
        {
            "id": r[0],
            "sensor_id": r[1],
            "timestamp": r[2],
            "flow_rate": r[3],
            "pressure": r[4],
            "temperature": r[5],
            "leak_detected": r[6]
        }
        for r in readings
    ]


@app.get("/api/v1/leaks")
async def get_leak_alerts(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recent leak detections"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = db.execute(
        text("""
            SELECT sensor_id, timestamp, flow_rate, pressure
            FROM water_readings
            WHERE leak_detected = true AND timestamp >= :start_date
            ORDER BY timestamp DESC
        """),
        {"start_date": start_date}
    )
    leaks = result.fetchall()
    
    return {
        "period_days": days,
        "total_leaks": len(leaks),
        "leaks": [
            {
                "sensor_id": leak[0],
                "timestamp": leak[1],
                "flow_rate": leak[2],
                "pressure": leak[3]
            }
            for leak in leaks
        ]
    }


@app.get("/api/v1/analytics/consumption")
async def get_water_analytics(
    sensor_id: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get water consumption analytics"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    if sensor_id:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(flow_rate) as avg_flow,
                    MAX(flow_rate) as max_flow,
                    AVG(pressure) as avg_pressure,
                    COUNT(CASE WHEN leak_detected THEN 1 END) as leak_count
                FROM water_readings
                WHERE sensor_id = :sensor_id AND timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"sensor_id": sensor_id, "start_date": start_date}
        )
    else:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(flow_rate) as avg_flow,
                    MAX(flow_rate) as max_flow,
                    AVG(pressure) as avg_pressure,
                    COUNT(CASE WHEN leak_detected THEN 1 END) as leak_count
                FROM water_readings
                WHERE timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"start_date": start_date}
        )
    
    analytics = result.fetchall()
    
    return {
        "sensor_id": sensor_id,
        "period_days": days,
        "data": [
            {
                "date": str(a[0]),
                "avg_flow_rate": float(a[1]) if a[1] else 0,
                "max_flow_rate": float(a[2]) if a[2] else 0,
                "avg_pressure": float(a[3]) if a[3] else 0,
                "leak_count": int(a[4]) if a[4] else 0
            }
            for a in analytics
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
