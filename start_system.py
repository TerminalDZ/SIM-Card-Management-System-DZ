#!/usr/bin/env python3
"""
SIM Card Management System - Backend Starter
Starts the FastAPI backend server.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def run_backend():
    """Run the backend server"""
    print("Starting backend server...")
    try:
        subprocess.run([sys.executable, "run_backend.py"], check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped by user")
    except Exception as e:
        print(f"Backend server error: {e}")

def main():
    """Start the backend server"""
    print("=" * 60)
    print("SIM CARD MANAGEMENT SYSTEM API")
    print("Professional API for Algerian mobile operators")
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
    
    print("Starting backend API server...")
    print()
    print("Access the system at:")
    print("- API Documentation: http://localhost:8000/docs")
    print("- API Base URL: http://localhost:8000/api")
    print("- WebSocket: ws://localhost:8000/ws")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Start backend (this will block)
        run_backend()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()
