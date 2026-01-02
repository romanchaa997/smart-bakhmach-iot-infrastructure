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
    title="Air Quality Service",
    description="Environmental monitoring and air quality analysis",
    version="1.0.0"
)


# Pydantic Models
class AirQualityStation(BaseModel):
    station_id: str
    location: str
    latitude: float
    longitude: float
    status: str = "active"


class AirQualityReading(BaseModel):
    station_id: str
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    co2: Optional[float] = None
    co: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None


# Helper function to calculate AQI
def calculate_aqi(pm25: float = None, pm10: float = None, co: float = None, no2: float = None, o3: float = None) -> int:
    """Calculate Air Quality Index based on pollutant levels"""
    aqi_values = []
    
    # PM2.5 AQI calculation (simplified)
    if pm25 is not None:
        if pm25 <= 12:
            aqi_pm25 = (50 / 12) * pm25
        elif pm25 <= 35.4:
            aqi_pm25 = 50 + ((100 - 50) / (35.4 - 12.1)) * (pm25 - 12.1)
        elif pm25 <= 55.4:
            aqi_pm25 = 100 + ((150 - 100) / (55.4 - 35.5)) * (pm25 - 35.5)
        elif pm25 <= 150.4:
            aqi_pm25 = 150 + ((200 - 150) / (150.4 - 55.5)) * (pm25 - 55.5)
        else:
            aqi_pm25 = 200 + ((300 - 200) / (250 - 150.5)) * (pm25 - 150.5)
        aqi_values.append(aqi_pm25)
    
    # PM10 AQI calculation (simplified)
    if pm10 is not None:
        if pm10 <= 54:
            aqi_pm10 = (50 / 54) * pm10
        elif pm10 <= 154:
            aqi_pm10 = 50 + ((100 - 50) / (154 - 55)) * (pm10 - 55)
        elif pm10 <= 254:
            aqi_pm10 = 100 + ((150 - 100) / (254 - 155)) * (pm10 - 155)
        else:
            aqi_pm10 = 150 + ((200 - 150) / (354 - 255)) * (pm10 - 255)
        aqi_values.append(aqi_pm10)
    
    # Return maximum AQI or 0 if no values
    return int(max(aqi_values)) if aqi_values else 0


# Event handlers
def handle_mqtt_reading(payload: dict):
    """Handle incoming MQTT readings from air quality stations"""
    print(f"Received air quality reading: {payload}")


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    mqtt_client.subscribe("airquality/stations/+/reading", handle_mqtt_reading)
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
    return {"service": "Air Quality Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "air-quality-service"}


@app.post("/api/v1/stations", response_model=dict)
async def create_station(
    station: AirQualityStation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register a new air quality station"""
    try:
        result = db.execute(
            text("""
                INSERT INTO air_quality_stations 
                (station_id, location, latitude, longitude, status)
                VALUES (:station_id, :location, :latitude, :longitude, :status)
                RETURNING id, station_id, location, latitude, longitude, status, created_at
            """),
            {
                "station_id": station.station_id,
                "location": station.location,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "status": station.status
            }
        )
        db.commit()
        new_station = result.fetchone()
        
        await kafka_client.publish("airquality.station.created", {
            "station_id": station.station_id,
            "location": station.location,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "id": new_station[0],
            "station_id": new_station[1],
            "location": new_station[2],
            "latitude": new_station[3],
            "longitude": new_station[4],
            "status": new_station[5],
            "created_at": new_station[6]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/stations", response_model=List[dict])
async def get_stations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all air quality stations"""
    result = db.execute(text("SELECT * FROM air_quality_stations ORDER BY created_at DESC"))
    stations = result.fetchall()
    
    return [
        {
            "id": s[0],
            "station_id": s[1],
            "location": s[2],
            "latitude": s[3],
            "longitude": s[4],
            "installation_date": s[5],
            "status": s[6],
            "created_at": s[7]
        }
        for s in stations
    ]


@app.post("/api/v1/readings", response_model=dict)
async def create_reading(
    reading: AirQualityReading,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record an air quality reading"""
    try:
        timestamp = datetime.now(timezone.utc)
        aqi = calculate_aqi(reading.pm25, reading.pm10, reading.co, reading.no2, reading.o3)
        
        result = db.execute(
            text("""
                INSERT INTO air_quality_readings 
                (station_id, timestamp, pm25, pm10, co2, co, no2, o3, temperature, humidity, aqi)
                VALUES (:station_id, :timestamp, :pm25, :pm10, :co2, :co, :no2, :o3, :temperature, :humidity, :aqi)
                RETURNING id
            """),
            {
                "station_id": reading.station_id,
                "timestamp": timestamp,
                "pm25": reading.pm25,
                "pm10": reading.pm10,
                "co2": reading.co2,
                "co": reading.co,
                "no2": reading.no2,
                "o3": reading.o3,
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "aqi": aqi
            }
        )
        db.commit()
        reading_id = result.fetchone()[0]
        
        await kafka_client.publish("airquality.reading", {
            "station_id": reading.station_id,
            "aqi": aqi,
            "pm25": reading.pm25,
            "timestamp": timestamp.isoformat()
        })
        
        # Alert on poor air quality
        if aqi > 150:  # Unhealthy for sensitive groups
            severity = "critical" if aqi > 200 else "warning"
            await kafka_client.publish("airquality.alert", {
                "station_id": reading.station_id,
                "alert_type": "poor_air_quality",
                "aqi": aqi,
                "severity": severity,
                "timestamp": timestamp.isoformat()
            })
            
            db.execute(
                text("""
                    INSERT INTO alerts 
                    (service_type, entity_id, alert_type, severity, message, timestamp)
                    VALUES (:service_type, :entity_id, :alert_type, :severity, :message, :timestamp)
                """),
                {
                    "service_type": "air_quality",
                    "entity_id": reading.station_id,
                    "alert_type": "poor_air_quality",
                    "severity": severity,
                    "message": f"Poor air quality detected (AQI: {aqi}) at station {reading.station_id}",
                    "timestamp": timestamp
                }
            )
            db.commit()
        
        return {"id": reading_id, "station_id": reading.station_id, "aqi": aqi, "timestamp": timestamp}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/readings/{station_id}", response_model=List[dict])
async def get_readings(
    station_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get air quality readings for a specific station"""
    result = db.execute(
        text("""
            SELECT * FROM air_quality_readings 
            WHERE station_id = :station_id 
            ORDER BY timestamp DESC 
            LIMIT :limit
        """),
        {"station_id": station_id, "limit": limit}
    )
    readings = result.fetchall()
    
    return [
        {
            "id": r[0],
            "station_id": r[1],
            "timestamp": r[2],
            "pm25": r[3],
            "pm10": r[4],
            "co2": r[5],
            "co": r[6],
            "no2": r[7],
            "o3": r[8],
            "temperature": r[9],
            "humidity": r[10],
            "aqi": r[11]
        }
        for r in readings
    ]


@app.get("/api/v1/current")
async def get_current_conditions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current air quality conditions from all stations"""
    result = db.execute(
        text("""
            SELECT DISTINCT ON (station_id)
                station_id, timestamp, pm25, pm10, co2, temperature, humidity, aqi
            FROM air_quality_readings
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            ORDER BY station_id, timestamp DESC
        """)
    )
    conditions = result.fetchall()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stations": [
            {
                "station_id": c[0],
                "last_update": c[1],
                "pm25": c[2],
                "pm10": c[3],
                "co2": c[4],
                "temperature": c[5],
                "humidity": c[6],
                "aqi": c[7],
                "status": get_aqi_status(c[7]) if c[7] else "unknown"
            }
            for c in conditions
        ]
    }


def get_aqi_status(aqi: int) -> str:
    """Get air quality status from AQI value"""
    if aqi <= 50:
        return "good"
    elif aqi <= 100:
        return "moderate"
    elif aqi <= 150:
        return "unhealthy_sensitive"
    elif aqi <= 200:
        return "unhealthy"
    elif aqi <= 300:
        return "very_unhealthy"
    else:
        return "hazardous"


@app.get("/api/v1/analytics/trends")
async def get_air_quality_trends(
    station_id: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get air quality trends"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    if station_id:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(pm25) as avg_pm25,
                    AVG(pm10) as avg_pm10,
                    AVG(co2) as avg_co2,
                    AVG(aqi) as avg_aqi,
                    MAX(aqi) as max_aqi
                FROM air_quality_readings
                WHERE station_id = :station_id AND timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"station_id": station_id, "start_date": start_date}
        )
    else:
        result = db.execute(
            text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(pm25) as avg_pm25,
                    AVG(pm10) as avg_pm10,
                    AVG(co2) as avg_co2,
                    AVG(aqi) as avg_aqi,
                    MAX(aqi) as max_aqi
                FROM air_quality_readings
                WHERE timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """),
            {"start_date": start_date}
        )
    
    trends = result.fetchall()
    
    return {
        "station_id": station_id,
        "period_days": days,
        "data": [
            {
                "date": str(t[0]),
                "avg_pm25": float(t[1]) if t[1] else 0,
                "avg_pm10": float(t[2]) if t[2] else 0,
                "avg_co2": float(t[3]) if t[3] else 0,
                "avg_aqi": int(t[4]) if t[4] else 0,
                "max_aqi": int(t[5]) if t[5] else 0,
                "status": get_aqi_status(int(t[4])) if t[4] else "unknown"
            }
            for t in trends
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
