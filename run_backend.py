#!/usr/bin/env python3
"""
SIM Card Management System - Backend Server
Starts the FastAPI backend server for the SIM card management system.
"""

import sys
import os
import uvicorn

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import settings

def main():
    """Start the backend server"""
    print("Starting SIM Card Management System Backend...")
    print(f"Server will run on http://{settings.HOST}:{settings.PORT}")
    print(f"Debug mode: {settings.DEBUG}")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        reload_excludes=["../frontend/node_modules/*", "../frontend/node_modules/**/*"]
    )

if __name__ == "__main__":
    main()
