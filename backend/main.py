from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os
import signal
import sys

# Re-enable database and routers for in-memory testing
from app.database import init_db, close_db
from app.routers import auth, resumes, jobs, scoring
from app.core.config import settings

# Load environment variables
load_dotenv()

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - now using in-memory database with persistence
    await init_db()
    print("🚀 ATS Scoring Assistant Backend Starting with Persistent In-Memory Database...")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    yield
    
    # Shutdown - save data before closing
    print("🛑 ATS Scoring Assistant Backend Shutting down...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="ATS Scoring Assistant API",
    description="AI-powered resume scoring and matching system (Persistent In-Memory Mode)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Updated configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:4173",  # Vite preview
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Re-enable all routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])

@app.get("/")
async def root():
    return {
        "message": "ATS Scoring Assistant API",
        "version": "1.0.0",
        "status": "Persistent in-memory database mode",
        "features": "Full API functionality with data persistence",
        "data_location": "./data/"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ATS Scoring Assistant",
        "mode": "persistent in-memory database",
        "database": "ready"
    }

@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "Backend is working with persistent in-memory database!",
        "endpoints": [
            "/ - Root endpoint",
            "/health - Health check",
            "/api/test - This test endpoint",
            "/api/auth/* - Authentication endpoints",
            "/api/resumes/* - Resume management",
            "/api/jobs/* - Job management",
            "/api/scoring/* - Scoring endpoints"
        ],
        "database": "persistent in-memory (data saved to ./data/ folder)"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
