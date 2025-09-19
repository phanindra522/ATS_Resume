#!/usr/bin/env python3
"""
Test script to verify Swagger UI functionality
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting ATS Resume Scoring Assistant API with Enhanced Swagger UI...")
    print("📚 Swagger UI will be available at: http://localhost:8000/docs")
    print("📖 ReDoc will be available at: http://localhost:8000/redoc")
    print("🔧 OpenAPI Schema will be available at: http://localhost:8000/openapi.json")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
