from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.database.connection import get_db
from shared.auth.jwt_handler import get_current_user
from shared.messaging.kafka_client import kafka_client

app = FastAPI(
    title="ML Analytics Service",
    description="Machine learning powered predictive analytics",
    version="1.0.0"
)


# Pydantic Models
class PredictionRequest(BaseModel):
    service_type: str
    entity_id: str
    prediction_type: str
    historical_days: int = 30


class PredictionResponse(BaseModel):
    service_type: str
    entity_id: str
    prediction_type: str
    predicted_value: float
    confidence_score: float
    timestamp: datetime


# ML Models storage
ml_models = {}


@app.on_event("startup")
async def startup_event():
    """Initialize ML models and connections on startup"""
    await kafka_client.start_producer()
    print("ML Analytics Service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await kafka_client.stop_producer()


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "ML Analytics Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ml-analytics-service"}


@app.post("/api/v1/predict/energy", response_model=dict)
async def predict_energy_consumption(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict future energy consumption for a smart meter"""
    try:
        # Fetch historical data
        start_date = datetime.utcnow() - timedelta(days=request.historical_days)
        result = db.execute(
            text("""
                SELECT timestamp, power_consumption
                FROM energy_readings
                WHERE meter_id = :entity_id AND timestamp >= :start_date
                ORDER BY timestamp ASC
            """),
            {"entity_id": request.entity_id, "start_date": start_date}
        )
        data = result.fetchall()
        
        if len(data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Prepare data for ML model
        timestamps = np.array([(d[0] - data[0][0]).total_seconds() / 3600 for d in data]).reshape(-1, 1)
        consumption = np.array([d[1] for d in data])
        
        # Train simple linear regression model
        model = LinearRegression()
        model.fit(timestamps, consumption)
        
        # Predict next 24 hours
        future_timestamp = (datetime.utcnow() - data[0][0]).total_seconds() / 3600 + 24
        prediction = model.predict([[future_timestamp]])[0]
        
        # Calculate confidence score based on R² score
        confidence = model.score(timestamps, consumption)
        
        # Store prediction
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO predictions 
                (service_type, entity_id, prediction_type, predicted_value, confidence_score, timestamp)
                VALUES (:service_type, :entity_id, :prediction_type, :predicted_value, :confidence_score, :timestamp)
                RETURNING id
            """),
            {
                "service_type": "energy",
                "entity_id": request.entity_id,
                "prediction_type": "consumption_24h",
                "predicted_value": float(prediction),
                "confidence_score": float(confidence),
                "timestamp": timestamp
            }
        )
        db.commit()
        prediction_id = result.fetchone()[0]
        
        # Publish event
        await kafka_client.publish("ml.prediction", {
            "service_type": "energy",
            "entity_id": request.entity_id,
            "prediction_type": "consumption_24h",
            "predicted_value": float(prediction),
            "timestamp": timestamp.isoformat()
        })
        
        return {
            "id": prediction_id,
            "service_type": "energy",
            "entity_id": request.entity_id,
            "prediction_type": "consumption_24h",
            "predicted_value": float(prediction),
            "confidence_score": float(confidence),
            "timestamp": timestamp,
            "unit": "kWh"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/water", response_model=dict)
async def predict_water_leak(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict likelihood of water leak"""
    try:
        # Fetch historical data
        start_date = datetime.utcnow() - timedelta(days=request.historical_days)
        result = db.execute(
            text("""
                SELECT flow_rate, pressure, leak_detected
                FROM water_readings
                WHERE sensor_id = :entity_id AND timestamp >= :start_date
                ORDER BY timestamp DESC
            """),
            {"entity_id": request.entity_id, "start_date": start_date}
        )
        data = result.fetchall()
        
        if len(data) < 20:
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Prepare features and labels
        X = np.array([[d[0] or 0, d[1] or 0] for d in data])
        y = np.array([1 if d[2] else 0 for d in data])
        
        # Train random forest classifier
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        # Predict current likelihood
        latest_reading = X[0:1]
        leak_probability = model.predict(latest_reading)[0]
        confidence = model.score(X, y)
        
        # Store prediction
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO predictions 
                (service_type, entity_id, prediction_type, predicted_value, confidence_score, timestamp)
                VALUES (:service_type, :entity_id, :prediction_type, :predicted_value, :confidence_score, :timestamp)
                RETURNING id
            """),
            {
                "service_type": "water",
                "entity_id": request.entity_id,
                "prediction_type": "leak_probability",
                "predicted_value": float(leak_probability),
                "confidence_score": float(confidence),
                "timestamp": timestamp
            }
        )
        db.commit()
        prediction_id = result.fetchone()[0]
        
        # Publish event if high risk
        if leak_probability > 0.7:
            await kafka_client.publish("ml.prediction.alert", {
                "service_type": "water",
                "entity_id": request.entity_id,
                "prediction_type": "leak_risk_high",
                "probability": float(leak_probability),
                "timestamp": timestamp.isoformat()
            })
        
        return {
            "id": prediction_id,
            "service_type": "water",
            "entity_id": request.entity_id,
            "prediction_type": "leak_probability",
            "predicted_value": float(leak_probability),
            "confidence_score": float(confidence),
            "timestamp": timestamp,
            "risk_level": "high" if leak_probability > 0.7 else "medium" if leak_probability > 0.3 else "low"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/transport", response_model=dict)
async def predict_transport_demand(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict passenger demand for a vehicle/route"""
    try:
        # Fetch historical data
        start_date = datetime.utcnow() - timedelta(days=request.historical_days)
        result = db.execute(
            text("""
                SELECT 
                    EXTRACT(HOUR FROM timestamp) as hour,
                    EXTRACT(DOW FROM timestamp) as day_of_week,
                    AVG(passengers) as avg_passengers
                FROM transport_telemetry
                WHERE vehicle_id = :entity_id AND timestamp >= :start_date AND passengers IS NOT NULL
                GROUP BY EXTRACT(HOUR FROM timestamp), EXTRACT(DOW FROM timestamp)
                ORDER BY hour, day_of_week
            """),
            {"entity_id": request.entity_id, "start_date": start_date}
        )
        data = result.fetchall()
        
        if len(data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Prepare data
        X = np.array([[d[0], d[1]] for d in data])
        y = np.array([d[2] for d in data])
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict for current hour and day
        current_hour = datetime.utcnow().hour
        current_day = datetime.utcnow().weekday()
        prediction = model.predict([[current_hour, current_day]])[0]
        confidence = model.score(X, y)
        
        # Store prediction
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO predictions 
                (service_type, entity_id, prediction_type, predicted_value, confidence_score, timestamp)
                VALUES (:service_type, :entity_id, :prediction_type, :predicted_value, :confidence_score, :timestamp)
                RETURNING id
            """),
            {
                "service_type": "transport",
                "entity_id": request.entity_id,
                "prediction_type": "passenger_demand",
                "predicted_value": float(prediction),
                "confidence_score": float(confidence),
                "timestamp": timestamp
            }
        )
        db.commit()
        prediction_id = result.fetchone()[0]
        
        await kafka_client.publish("ml.prediction", {
            "service_type": "transport",
            "entity_id": request.entity_id,
            "prediction_type": "passenger_demand",
            "predicted_value": float(prediction),
            "timestamp": timestamp.isoformat()
        })
        
        return {
            "id": prediction_id,
            "service_type": "transport",
            "entity_id": request.entity_id,
            "prediction_type": "passenger_demand",
            "predicted_value": float(prediction),
            "confidence_score": float(confidence),
            "timestamp": timestamp,
            "demand_level": "high" if prediction > 30 else "medium" if prediction > 15 else "low"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/airquality", response_model=dict)
async def predict_air_quality(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Predict future air quality index"""
    try:
        # Fetch historical data
        start_date = datetime.utcnow() - timedelta(days=request.historical_days)
        result = db.execute(
            text("""
                SELECT timestamp, aqi, temperature, humidity
                FROM air_quality_readings
                WHERE station_id = :entity_id AND timestamp >= :start_date AND aqi IS NOT NULL
                ORDER BY timestamp ASC
            """),
            {"entity_id": request.entity_id, "start_date": start_date}
        )
        data = result.fetchall()
        
        if len(data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Prepare features
        timestamps = np.array([(d[0] - data[0][0]).total_seconds() / 3600 for d in data]).reshape(-1, 1)
        aqi_values = np.array([d[1] for d in data])
        
        # Train model
        model = LinearRegression()
        model.fit(timestamps, aqi_values)
        
        # Predict next 24 hours
        future_timestamp = (datetime.utcnow() - data[0][0]).total_seconds() / 3600 + 24
        prediction = model.predict([[future_timestamp]])[0]
        confidence = model.score(timestamps, aqi_values)
        
        # Store prediction
        timestamp = datetime.utcnow()
        result = db.execute(
            text("""
                INSERT INTO predictions 
                (service_type, entity_id, prediction_type, predicted_value, confidence_score, timestamp)
                VALUES (:service_type, :entity_id, :prediction_type, :predicted_value, :confidence_score, :timestamp)
                RETURNING id
            """),
            {
                "service_type": "air_quality",
                "entity_id": request.entity_id,
                "prediction_type": "aqi_24h",
                "predicted_value": float(prediction),
                "confidence_score": float(confidence),
                "timestamp": timestamp
            }
        )
        db.commit()
        prediction_id = result.fetchone()[0]
        
        await kafka_client.publish("ml.prediction", {
            "service_type": "air_quality",
            "entity_id": request.entity_id,
            "prediction_type": "aqi_24h",
            "predicted_value": float(prediction),
            "timestamp": timestamp.isoformat()
        })
        
        return {
            "id": prediction_id,
            "service_type": "air_quality",
            "entity_id": request.entity_id,
            "prediction_type": "aqi_24h",
            "predicted_value": float(prediction),
            "confidence_score": float(confidence),
            "timestamp": timestamp,
            "quality_level": get_aqi_status(int(prediction))
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
    else:
        return "very_unhealthy"


@app.get("/api/v1/predictions/{service_type}", response_model=List[dict])
async def get_predictions(
    service_type: str,
    entity_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get historical predictions for a service type"""
    if entity_id:
        result = db.execute(
            text("""
                SELECT * FROM predictions
                WHERE service_type = :service_type AND entity_id = :entity_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"service_type": service_type, "entity_id": entity_id, "limit": limit}
        )
    else:
        result = db.execute(
            text("""
                SELECT * FROM predictions
                WHERE service_type = :service_type
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"service_type": service_type, "limit": limit}
        )
    
    predictions = result.fetchall()
    
    return [
        {
            "id": p[0],
            "service_type": p[1],
            "entity_id": p[2],
            "prediction_type": p[3],
            "predicted_value": p[4],
            "confidence_score": p[6],
            "timestamp": p[7]
        }
        for p in predictions
    ]


@app.get("/api/v1/analytics/accuracy")
async def get_model_accuracy(
    service_type: str,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get model accuracy metrics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = db.execute(
        text("""
            SELECT 
                prediction_type,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as prediction_count
            FROM predictions
            WHERE service_type = :service_type AND timestamp >= :start_date
            GROUP BY prediction_type
        """),
        {"service_type": service_type, "start_date": start_date}
    )
    metrics = result.fetchall()
    
    return {
        "service_type": service_type,
        "period_days": days,
        "metrics": [
            {
                "prediction_type": m[0],
                "avg_confidence": float(m[1]) if m[1] else 0,
                "prediction_count": int(m[2])
            }
            for m in metrics
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
