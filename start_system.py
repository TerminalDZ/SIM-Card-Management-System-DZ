#!/usr/bin/env python3
"""
Multi-Modem SIM Card Management System - Backend Starter
Starts the FastAPI backend server with multi-modem support.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def run_backend():
    """Run the backend server"""
    print("Starting multi-modem backend server...")
    try:
        subprocess.run([sys.executable, "run_backend.py"], check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped by user")
    except Exception as e:
        print(f"Backend server error: {e}")

def main():
    """Start the backend server"""
    print("=" * 60)
    print("MULTI-MODEM SIM CARD MANAGEMENT SYSTEM API")
    print("Professional multi-modem API for Algerian mobile operators")
    print("=" * 60)
    print()
    
    # Check dependencies
    try:
        import serial
        import fastapi
        import uvicorn
    except ImportError as e:
        print(f"Missing Python dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return
    
    print("Starting multi-modem backend API server...")
    print()
    print("Multi-Modem Features:")
    print("- Automatic detection of multiple Huawei modems")
    print("- Individual modem management and control")
    print("- Load balancing across multiple modems")
    print("- Real-time monitoring of all connected modems")
    print()
    print("Access the system at:")
    print("- API Documentation: http://localhost:8000/docs")
    print("- API Base URL: http://localhost:8000/api")
    print("- WebSocket: ws://localhost:8000/ws")
    print()
    print("Multi-Modem API Endpoints:")
    print("- GET /api/modems/detect - Detect available modems")
    print("- POST /api/modems/connect - Connect to specific modem")
    print("- GET /api/modems/status - Status of all modems")
    print("- GET /api/modems/{id}/sim-info - SIM info per modem")
    print("- POST /api/modems/{id}/sms/send - Send SMS from specific modem")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Start backend (this will block)
        run_backend()
    except KeyboardInterrupt:
        print("\nShutting down multi-modem server...")

if __name__ == "__main__":
    main()
