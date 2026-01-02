from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.database.connection import get_db
from shared.auth.jwt_handler import get_current_user
from shared.messaging.kafka_client import kafka_client
from shared.messaging.mqtt_client import mqtt_client

app = FastAPI(
    title="Transport Service",
    description="Public transport tracking and route optimization",
    version="1.0.0"
)


# Pydantic Models
class Vehicle(BaseModel):
    vehicle_id: str
    vehicle_type: str
    route_id: Optional[str] = None
    capacity: Optional[int] = None
    status: str = "active"


class TransportTelemetry(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    speed: Optional[float] = None
    fuel_level: Optional[float] = None
    passengers: Optional[int] = None


# Event handlers
def handle_mqtt_telemetry(payload: dict):
    """Handle incoming MQTT telemetry from vehicles"""
    print(f"Received transport telemetry: {payload}")


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    mqtt_client.subscribe("transport/vehicles/+/telemetry", handle_mqtt_telemetry)
    mqtt_client.connect()
    await kafka_client.start_producer()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.disconnect()
    await kafka_client.stop_producer()


# Helper functions
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in km"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Transport Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "transport-service"}


@app.post("/api/v1/vehicles", response_model=dict)
async def create_vehicle(
    vehicle: Vehicle,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Register a new vehicle"""
    try:
        result = db.execute(
            text("""
                INSERT INTO transport_vehicles 
                (vehicle_id, vehicle_type, route_id, capacity, status)
                VALUES (:vehicle_id, :vehicle_type, :route_id, :capacity, :status)
                RETURNING id, vehicle_id, vehicle_type, route_id, capacity, status, created_at
            """),
            {
                "vehicle_id": vehicle.vehicle_id,
                "vehicle_type": vehicle.vehicle_type,
                "route_id": vehicle.route_id,
                "capacity": vehicle.capacity,
                "status": vehicle.status
            }
        )
        db.commit()
        new_vehicle = result.fetchone()
        
        await kafka_client.publish("transport.vehicle.created", {
            "vehicle_id": vehicle.vehicle_id,
            "vehicle_type": vehicle.vehicle_type,
            "route_id": vehicle.route_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "id": new_vehicle[0],
            "vehicle_id": new_vehicle[1],
            "vehicle_type": new_vehicle[2],
            "route_id": new_vehicle[3],
            "capacity": new_vehicle[4],
            "status": new_vehicle[5],
            "created_at": new_vehicle[6]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/vehicles", response_model=List[dict])
async def get_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all vehicles"""
    result = db.execute(text("SELECT * FROM transport_vehicles ORDER BY created_at DESC"))
    vehicles = result.fetchall()
    
    return [
        {
            "id": v[0],
            "vehicle_id": v[1],
            "vehicle_type": v[2],
            "route_id": v[3],
            "capacity": v[4],
            "status": v[5],
            "created_at": v[6]
        }
        for v in vehicles
    ]


@app.post("/api/v1/telemetry", response_model=dict)
async def create_telemetry(
    telemetry: TransportTelemetry,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record vehicle telemetry"""
    try:
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO transport_telemetry 
                (vehicle_id, timestamp, latitude, longitude, speed, fuel_level, passengers)
                VALUES (:vehicle_id, :timestamp, :latitude, :longitude, :speed, :fuel_level, :passengers)
                RETURNING id
            """),
            {
                "vehicle_id": telemetry.vehicle_id,
                "timestamp": timestamp,
                "latitude": telemetry.latitude,
                "longitude": telemetry.longitude,
                "speed": telemetry.speed,
                "fuel_level": telemetry.fuel_level,
                "passengers": telemetry.passengers
            }
        )
        db.commit()
        telemetry_id = result.fetchone()[0]
        
        await kafka_client.publish("transport.telemetry", {
            "vehicle_id": telemetry.vehicle_id,
            "latitude": telemetry.latitude,
            "longitude": telemetry.longitude,
            "speed": telemetry.speed,
            "passengers": telemetry.passengers,
            "timestamp": timestamp.isoformat()
        })
        
        # Check for alerts
        if telemetry.fuel_level and telemetry.fuel_level < 20:
            await kafka_client.publish("transport.alert", {
                "vehicle_id": telemetry.vehicle_id,
                "alert_type": "low_fuel",
                "fuel_level": telemetry.fuel_level,
                "timestamp": timestamp.isoformat()
            })
        
        return {"id": telemetry_id, "vehicle_id": telemetry.vehicle_id, "timestamp": timestamp}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/telemetry/{vehicle_id}", response_model=List[dict])
async def get_telemetry(
    vehicle_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get telemetry for a specific vehicle"""
    result = db.execute(
        text("""
            SELECT * FROM transport_telemetry 
            WHERE vehicle_id = :vehicle_id 
            ORDER BY timestamp DESC 
            LIMIT :limit
        """),
        {"vehicle_id": vehicle_id, "limit": limit}
    )
    telemetry = result.fetchall()
    
    return [
        {
            "id": t[0],
            "vehicle_id": t[1],
            "timestamp": t[2],
            "latitude": t[3],
            "longitude": t[4],
            "speed": t[5],
            "fuel_level": t[6],
            "passengers": t[7]
        }
        for t in telemetry
    ]


@app.get("/api/v1/vehicles/live")
async def get_live_positions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get latest positions of all active vehicles"""
    result = db.execute(
        text("""
            SELECT DISTINCT ON (vehicle_id) 
                vehicle_id, timestamp, latitude, longitude, speed, passengers
            FROM transport_telemetry
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            ORDER BY vehicle_id, timestamp DESC
        """)
    )
    positions = result.fetchall()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "vehicles": [
            {
                "vehicle_id": p[0],
                "last_update": p[1],
                "latitude": p[2],
                "longitude": p[3],
                "speed": p[4],
                "passengers": p[5]
            }
            for p in positions
        ]
    }


@app.get("/api/v1/analytics/route/{route_id}")
async def get_route_analytics(
    route_id: str,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get analytics for a specific route"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = db.execute(
        text("""
            SELECT 
                DATE(t.timestamp) as date,
                AVG(t.speed) as avg_speed,
                AVG(t.passengers) as avg_passengers,
                COUNT(*) as trip_count
            FROM transport_telemetry t
            JOIN transport_vehicles v ON t.vehicle_id = v.vehicle_id
            WHERE v.route_id = :route_id AND t.timestamp >= :start_date
            GROUP BY DATE(t.timestamp)
            ORDER BY date DESC
        """),
        {"route_id": route_id, "start_date": start_date}
    )
    analytics = result.fetchall()
    
    return {
        "route_id": route_id,
        "period_days": days,
        "data": [
            {
                "date": str(a[0]),
                "avg_speed": float(a[1]) if a[1] else 0,
                "avg_passengers": float(a[2]) if a[2] else 0,
                "trip_count": int(a[3]) if a[3] else 0
            }
            for a in analytics
        ]
    }


@app.post("/api/v1/optimize/route")
async def optimize_route(
    waypoints: List[dict],
    current_user: dict = Depends(get_current_user)
):
    """Optimize route based on waypoints (simple nearest neighbor)"""
    if len(waypoints) < 2:
        return {"optimized_route": waypoints}
    
    # Simple nearest neighbor algorithm
    unvisited = waypoints.copy()
    route = [unvisited.pop(0)]
    
    while unvisited:
        last = route[-1]
        nearest = min(
            unvisited,
            key=lambda p: calculate_distance(
                last["latitude"], last["longitude"],
                p["latitude"], p["longitude"]
            )
        )
        route.append(nearest)
        unvisited.remove(nearest)
    
    # Calculate total distance
    total_distance = sum(
        calculate_distance(
            route[i]["latitude"], route[i]["longitude"],
            route[i + 1]["latitude"], route[i + 1]["longitude"]
        )
        for i in range(len(route) - 1)
    )
    
    return {
        "optimized_route": route,
        "total_distance_km": round(total_distance, 2),
        "waypoint_count": len(route)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
