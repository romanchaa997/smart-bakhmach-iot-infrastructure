from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Common settings for all services"""
    
    # Database
    database_url: str = "postgresql://iotuser:iotpass@localhost:5432/iot_platform"
    
    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # MQTT
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    
    # Service
    service_name: str = "iot-service"
    service_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
