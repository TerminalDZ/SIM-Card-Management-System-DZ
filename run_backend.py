#!/usr/bin/env python3
"""
Backend runner script for the Multi-Modem SIM Card Management System.

This script provides a convenient way to run the backend API server with
proper configuration and logging setup.
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.config import get_settings
from backend.core.logger import SimManagerLogger


def main():
    """Main entry point for the backend server."""
    try:
        # Get application settings
        settings = get_settings()
        
        # Initialize logger
        logger = SimManagerLogger(settings)
        
        # Log startup information
        logger.info("=" * 60)
        logger.info("Multi-Modem SIM Card Management System API")
        logger.info("=" * 60)
        logger.info(f"Version: {settings.API_VERSION}")
        logger.info(f"Host: {settings.HOST}")
        logger.info(f"Port: {settings.PORT}")
        logger.info(f"Debug Mode: {settings.DEBUG}")
        logger.info(f"Log Level: {settings.LOG_LEVEL}")
        logger.info(f"Max Concurrent Modems: {settings.MAX_CONCURRENT_MODEMS}")
        logger.info("=" * 60)
        
        # API documentation URLs
        logger.info("API Documentation:")
        logger.info(f"  - Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"  - ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
        logger.info(f"  - OpenAPI JSON: http://{settings.HOST}:{settings.PORT}/openapi.json")
        logger.info("=" * 60)
        
        # Multi-modem features
        logger.info("Multi-Modem Features:")
        logger.info("  ✓ Concurrent modem management")
        logger.info("  ✓ Automatic modem detection")
        logger.info("  ✓ Individual modem control")
        logger.info("  ✓ Load balancing support")
        logger.info("  ✓ Real-time status tracking")
        logger.info("  ✓ WebSocket notifications")
        logger.info("=" * 60)
        
        # API endpoints overview
        logger.info("API Endpoints:")
        logger.info("  Multi-Modem Management:")
        logger.info("    - POST /api/modems/detect")
        logger.info("    - POST /api/modems/connect")
        logger.info("    - POST /api/modems/disconnect")
        logger.info("    - GET  /api/modems/status")
        logger.info("    - GET  /api/modems/{modem_id}/status")
        logger.info("    - GET  /api/modems/{modem_id}/sim-info")
        logger.info("  Per-Modem Operations:")
        logger.info("    - GET  /api/modems/{modem_id}/sms")
        logger.info("    - POST /api/modems/{modem_id}/sms/send")
        logger.info("    - DELETE /api/modems/{modem_id}/sms/{message_id}")
        logger.info("    - POST /api/modems/{modem_id}/ussd")
        logger.info("    - GET  /api/modems/{modem_id}/balance")
        logger.info("  System:")
        logger.info("    - GET  /api/health")
        logger.info("    - GET  /api/performance")
        logger.info("    - WebSocket /ws")
        logger.info("=" * 60)
        
        # Start the server
        logger.info("Starting Multi-Modem SIM Card Management System API server...")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 60)
        
        uvicorn.run(
            "backend.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
            use_colors=True
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
