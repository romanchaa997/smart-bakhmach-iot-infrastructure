from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.database.connection import get_db
from shared.auth.jwt_handler import (
    create_access_token, 
    verify_password, 
    get_password_hash,
    get_current_user
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from datetime import datetime, timezone

app = FastAPI(
    title="IoT Smart City Platform - API Gateway",
    description="Central API Gateway for Bakhmach Smart City IoT Platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str = None
    role: str
    is_active: bool


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IoT Smart City Platform API Gateway",
        "version": "1.0.0",
        "services": [
            "Energy Management",
            "Water Management",
            "Transport Optimization",
            "Air Quality Monitoring",
            "ML Predictive Analytics"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}


@app.post("/api/v1/auth/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    # Query user from database
    result = db.execute(
        text("SELECT id, username, email, hashed_password, role FROM users WHERE username = :username"),
        {"username": form_data.username}
    )
    user = result.fetchone()
    
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user[1], "role": user[4]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    result = db.execute(
        text("SELECT id FROM users WHERE username = :username OR email = :email"),
        {"username": user.username, "email": user.email}
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash password and insert user
    hashed_password = get_password_hash(user.password)
    result = db.execute(
        text("""
            INSERT INTO users (username, email, hashed_password, full_name, role)
            VALUES (:username, :email, :hashed_password, :full_name, :role)
            RETURNING id, username, email, full_name, role, is_active
        """),
        {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password,
            "full_name": user.full_name,
            "role": "user"
        }
    )
    db.commit()
    new_user = result.fetchone()
    
    return UserResponse(
        id=new_user[0],
        username=new_user[1],
        email=new_user[2],
        full_name=new_user[3],
        role=new_user[4],
        is_active=new_user[5]
    )


@app.get("/api/v1/auth/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.get("/api/v1/services")
async def get_services(current_user: dict = Depends(get_current_user)):
    """Get list of available services"""
    return {
        "services": [
            {
                "name": "Energy Management",
                "endpoint": "http://energy-service:8001",
                "description": "Smart meter data and energy consumption analytics"
            },
            {
                "name": "Water Management",
                "endpoint": "http://water-service:8002",
                "description": "Water flow monitoring and leak detection"
            },
            {
                "name": "Transport",
                "endpoint": "http://transport-service:8003",
                "description": "Public transport tracking and optimization"
            },
            {
                "name": "Air Quality",
                "endpoint": "http://air-quality-service:8004",
                "description": "Environmental monitoring and air quality index"
            },
            {
                "name": "ML Analytics",
                "endpoint": "http://ml-analytics-service:8005",
                "description": "Predictive analytics and machine learning insights"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
