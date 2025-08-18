#!/usr/bin/env python3
"""
SIM Card Management System - System Starter
Starts both backend and frontend servers.
"""

import subprocess
import sys
import os
import time
import signal
import threading
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

def run_frontend():
    """Run the frontend development server"""
    print("Starting frontend server...")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("Frontend directory not found!")
        return
    
    try:
        # Check if node_modules exists, if not run npm install
        if not (frontend_dir / "node_modules").exists():
            print("Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Start the development server
        subprocess.run(["npm", "start"], cwd=frontend_dir, check=True)
    except KeyboardInterrupt:
        print("\nFrontend server stopped by user")
    except FileNotFoundError:
        print("npm not found! Please install Node.js and npm first.")
    except Exception as e:
        print(f"Frontend server error: {e}")

def main():
    """Start both servers"""
    print("=" * 60)
    print("SIM CARD MANAGEMENT SYSTEM")
    print("Professional control panel for Algerian mobile operators")
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
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(3)
    
    print("Backend started successfully!")
    print("Opening frontend...")
    print()
    print("Access the system at:")
    print("- Frontend: http://localhost:3000")
    print("- Backend API: http://localhost:8000")
    print("- API Documentation: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop both servers")
    print("-" * 60)
    
    try:
        # Start frontend (this will block)
        run_frontend()
    except KeyboardInterrupt:
        print("\nShutting down system...")

if __name__ == "__main__":
    main()
