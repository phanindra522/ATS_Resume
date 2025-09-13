#!/usr/bin/env python3
"""
Start Multi-Agent Server with Performance Monitoring
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import uvicorn
        import fastapi
        import chromadb
        import numpy
        import redis
        print("   ✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   💡 Install with: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration"""
    print("🔧 Checking environment...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("   ⚠️  .env file not found")
        print("   💡 Copy from env.example and configure")
        return False
    
    print("   ✅ Environment file found")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Multi-Agent Server...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("   ✅ Server starting...")
        return process
    except Exception as e:
        print(f"   ❌ Failed to start server: {e}")
        return None

def wait_for_server(max_wait=30):
    """Wait for server to be ready"""
    print("⏳ Waiting for server to be ready...")
    
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/docs", timeout=2)
            if response.status_code == 200:
                print("   ✅ Server is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
        print(f"   ⏳ Waiting... ({i+1}/{max_wait})")
    
    print("   ❌ Server failed to start within timeout")
    return False

def test_multi_agent_endpoints():
    """Test the multi-agent endpoints"""
    print("🧪 Testing Multi-Agent Endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/scoring/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed: {health_data['status']}")
            print(f"   ⚡ Processing time: {health_data.get('processing_time', 0):.2f}s")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test formula endpoint
        response = requests.get("http://localhost:8000/api/scoring/formula", timeout=10)
        if response.status_code == 200:
            formula_data = response.json()
            print(f"   ✅ Formula endpoint working")
            print(f"   📊 Formula: {formula_data['formula']}")
        else:
            print(f"   ❌ Formula endpoint failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Endpoint test failed: {e}")
        return False

def main():
    """Main startup sequence"""
    print("🎯 Multi-Agent Server Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check environment
    if not check_environment():
        return False
    
    # Start server
    process = start_server()
    if not process:
        return False
    
    # Wait for server
    if not wait_for_server():
        process.terminate()
        return False
    
    # Test endpoints
    if not test_multi_agent_endpoints():
        print("   ⚠️  Some endpoints failed, but server is running")
    
    print("\n🎉 Multi-Agent Server is Ready!")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🧪 Test Script: python test_multi_agent_api.py")
    print("🛑 Stop Server: Ctrl+C")
    
    try:
        # Keep server running
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        process.terminate()
        print("✅ Server stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
