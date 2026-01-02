from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import warnings


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
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key is not using default insecure value"""
        if v == "your-secret-key-change-in-production" and len(v) < 32:
            warnings.warn(
                "WARNING: Using default JWT secret key. This is insecure! "
                "Set JWT_SECRET_KEY environment variable to a secure random string.",
                UserWarning
            )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
