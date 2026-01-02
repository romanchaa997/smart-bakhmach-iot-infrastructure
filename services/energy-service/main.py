from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.database.connection import get_db
from shared.auth.jwt_handler import get_current_user
from shared.messaging.kafka_client import kafka_client
from shared.messaging.mqtt_client import mqtt_client

app = FastAPI(
    title="Energy Management Service",
    description="Smart meter monitoring and energy consumption analytics",
    version="1.0.0"
)


# Pydantic Models
class SmartMeter(BaseModel):
    meter_id: str
    location: str
    meter_type: str
    status: str = "active"


class EnergyReading(BaseModel):
    meter_id: str
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_consumption: float
    energy_total: Optional[float] = None
    power_factor: Optional[float] = None


class EnergyReadingResponse(BaseModel):
    id: int
    meter_id: str
    timestamp: datetime
    voltage: Optional[float]
    current: Optional[float]
    power_consumption: float
    energy_total: Optional[float]
    power_factor: Optional[float]


# Event handlers
def handle_mqtt_reading(payload: dict):
    """Handle incoming MQTT readings from smart meters"""
    print(f"Received energy reading: {payload}")
    # Store in database via background task


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    mqtt_client.subscribe("energy/meters/+/reading", handle_mqtt_reading)
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
    return {"service": "Energy Management Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "energy-service"}


@app.post("/api/v1/meters", response_model=dict)
async def create_meter(
    meter: SmartMeter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register a new smart meter"""
    try:
        result = db.execute(
            text("""
                INSERT INTO smart_meters (meter_id, location, meter_type, status)
                VALUES (:meter_id, :location, :meter_type, :status)
                RETURNING id, meter_id, location, meter_type, status, created_at
            """),
            {
                "meter_id": meter.meter_id,
                "location": meter.location,
                "meter_type": meter.meter_type,
                "status": meter.status
            }
        )
        db.commit()
        new_meter = result.fetchone()
        
        # Publish event to Kafka
        await kafka_client.publish("meter.created", {
            "meter_id": meter.meter_id,
            "location": meter.location,
            "type": meter.meter_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "id": new_meter[0],
            "meter_id": new_meter[1],
            "location": new_meter[2],
            "meter_type": new_meter[3],
            "status": new_meter[4],
            "created_at": new_meter[5]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/meters", response_model=List[dict])
async def get_meters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all smart meters"""
    result = db.execute(text("SELECT * FROM smart_meters ORDER BY created_at DESC"))
    meters = result.fetchall()
    
    return [
        {
            "id": meter[0],
            "meter_id": meter[1],
            "location": meter[2],
            "meter_type": meter[3],
            "installation_date": meter[4],
            "status": meter[5],
            "created_at": meter[6]
        }
        for meter in meters
    ]


@app.post("/api/v1/readings", response_model=dict)
async def create_reading(
    reading: EnergyReading,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record an energy reading"""
    try:
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO energy_readings 
                (meter_id, timestamp, voltage, current, power_consumption, energy_total, power_factor)
                VALUES (:meter_id, :timestamp, :voltage, :current, :power_consumption, :energy_total, :power_factor)
                RETURNING id
            """),
            {
                "meter_id": reading.meter_id,
                "timestamp": timestamp,
                "voltage": reading.voltage,
                "current": reading.current,
                "power_consumption": reading.power_consumption,
                "energy_total": reading.energy_total,
                "power_factor": reading.power_factor
            }
        )
        db.commit()
        reading_id = result.fetchone()[0]
        
        # Publish event to Kafka
        await kafka_client.publish("energy.reading", {
            "meter_id": reading.meter_id,
            "power_consumption": reading.power_consumption,
            "timestamp": timestamp.isoformat()
        })
        
        # Check for anomalies and create alerts
        if reading.power_consumption > 10000:  # High consumption threshold
            await kafka_client.publish("energy.alert", {
                "meter_id": reading.meter_id,
                "alert_type": "high_consumption",
                "value": reading.power_consumption,
                "timestamp": timestamp.isoformat()
            })
        
        return {"id": reading_id, "meter_id": reading.meter_id, "timestamp": timestamp}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/readings/{meter_id}", response_model=List[dict])
async def get_readings(
    meter_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get energy readings for a specific meter"""
    result = db.execute(
        text("""
            SELECT * FROM energy_readings 
            WHERE meter_id = :meter_id 
            ORDER BY timestamp DESC 
            LIMIT :limit
        """),
        {"meter_id": meter_id, "limit": limit}
    )
    readings = result.fetchall()
    
    return [
        {
            "id": r[0],
            "meter_id": r[1],
            "timestamp": r[2],
            "voltage": r[3],
            "current": r[4],
            "power_consumption": r[5],
            "energy_total": r[6],
            "power_factor": r[7]
        }
        for r in readings
    ]


@app.get("/api/v1/analytics/consumption")
async def get_consumption_analytics(
    meter_id: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get energy consumption analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    if meter_id:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(power_consumption) as total_consumption,
                    AVG(power_consumption) as avg_consumption,
                    MAX(power_consumption) as peak_consumption
                FROM energy_readings
                WHERE meter_id = :meter_id AND timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"meter_id": meter_id, "start_date": start_date}
        )
    else:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(power_consumption) as total_consumption,
                    AVG(power_consumption) as avg_consumption,
                    MAX(power_consumption) as peak_consumption
                FROM energy_readings
                WHERE timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"start_date": start_date}
        )
    
    analytics = result.fetchall()
    
    return {
        "meter_id": meter_id,
        "period_days": days,
        "data": [
            {
                "date": str(a[0]),
                "total_consumption": float(a[1]) if a[1] else 0,
                "avg_consumption": float(a[2]) if a[2] else 0,
                "peak_consumption": float(a[3]) if a[3] else 0
            }
            for a in analytics
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
