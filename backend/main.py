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
from app.core.openapi import setup_custom_openapi

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

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="ATS Resume Scoring Assistant API",
    description="""
    ## 🚀 AI-Powered Resume Scoring and Matching System
    
    This API provides comprehensive resume analysis and job matching capabilities using advanced AI technologies:
    
    ### 🎯 Key Features
    - **Multi-Agent Scoring System**: 5 specialized AI agents analyze different aspects of resume-job matching
    - **Intelligent Document Processing**: PDF/DOCX resume parsing with text extraction
    - **Semantic Similarity Analysis**: Vector-based matching using ChromaDB and sentence transformers
    - **Comprehensive Scoring**: Weighted scoring across keywords, skills, experience, education, and semantic similarity
    - **Secure Authentication**: JWT-based user authentication and authorization
    
    ### 🤖 Multi-Agent Architecture
    1. **Keyword Matching Agent** (20%): Identifies exact keyword matches
    2. **Skill Matching Agent** (25%): Matches technical and soft skills using taxonomy
    3. **Experience Relevance Agent** (20%): Analyzes years of experience and seniority level
    4. **Education Alignment Agent** (10%): Matches educational background with job requirements
    5. **Semantic Similarity Agent** (25%): Analyzes semantic similarity using embeddings
    
    ### 🔧 Technology Stack
    - **Backend**: FastAPI, Python 3.12+
    - **Database**: MongoDB (structured data) + ChromaDB (vector storage)
    - **AI/ML**: Sentence Transformers, Multi-Agent Architecture
    - **Authentication**: JWT with bcrypt password hashing
    
    ### 📊 Current Status
    - ✅ **Mode**: Persistent In-Memory Database
    - ✅ **Data Persistence**: Automatic saving to `./data/` folder
    - ✅ **Full API Functionality**: All endpoints operational
    - ✅ **Multi-Agent Scoring**: Advanced AI-powered analysis
    
    ### 🔐 Authentication
    Most endpoints require JWT authentication. Use the `/api/auth/login` endpoint to get a token, then include it in the Authorization header as `Bearer <token>`.
    
    ### 📝 API Documentation
    - **Swagger UI**: Interactive API documentation (this page)
    - **ReDoc**: Alternative documentation format at `/redoc`
    - **OpenAPI Schema**: Available at `/openapi.json`
    """,
    version="1.0.0",
    contact={
        "name": "ATS Resume Scoring Assistant",
        "email": "support@ats-scoring.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.ats-scoring.com",
            "description": "Production server (future)"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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

# Setup custom OpenAPI schema
setup_custom_openapi(app)

# Re-enable all routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])

@app.get(
    "/",
    summary="API Root",
    description="Get basic information about the ATS Resume Scoring Assistant API",
    tags=["System"]
)
async def root():
    return {
        "message": "ATS Resume Scoring Assistant API",
        "version": "1.0.0",
        "status": "Persistent in-memory database mode",
        "features": "Full API functionality with data persistence",
        "data_location": "./data/",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "authentication": "/api/auth/*",
            "resumes": "/api/resumes/*",
            "jobs": "/api/jobs/*",
            "scoring": "/api/scoring/*"
        }
    }

@app.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the API service",
    tags=["System"]
)
async def health_check():
    return {
        "status": "healthy",
        "service": "ATS Resume Scoring Assistant",
        "mode": "persistent in-memory database",
        "database": "ready",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

@app.get(
    "/api/test",
    summary="Test Endpoint",
    description="Test endpoint to verify API functionality and list available endpoints",
    tags=["System"]
)
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
        "database": "persistent in-memory (data saved to ./data/ folder)",
        "swagger_ui": "Visit /docs for interactive API documentation"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
