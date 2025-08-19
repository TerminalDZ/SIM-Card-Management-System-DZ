"""
Multi-Modem SIM Card Management System API.

This module provides the main FastAPI application for managing multiple
Huawei USB modems, including SMS, USSD, and SIM card operations.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.core.multi_modem_manager import MultiModemManager
from backend.core.logger import SimManagerLogger, log_operation, log_performance
from backend.core.exceptions import (
    SimManagerException, ModemNotFoundException, ModemNotConnectedException,
    SmsException, UssdException, SimCardException, get_http_status_code
)
from backend.config import get_settings
from backend.models.models import (
    ModemStatus, SimInfo, SmsMessage, UssdResponse, MultiModemStatus,
    ModemConnectionRequest, ModemDisconnectionRequest, SmsRequest, UssdRequest,
    ModemDetectionResponse, SuccessResponse, ErrorResponse
)


# Global instances
settings = get_settings()
logger = SimManagerLogger(settings)
multi_modem_manager = MultiModemManager()


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket client: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Multi-Modem SIM Card Management System API")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Max Concurrent Modems: {settings.MAX_CONCURRENT_MODEMS}")
    
    # Initialize multi-modem manager
    logger.info("MultiModemManager initialized")
    logger.info(f"Max concurrent modems: {settings.MAX_CONCURRENT_MODEMS}")
    
    # Detect modems on startup
    try:
        with log_operation(logger, "Modem Detection"):
            detected_modems = await multi_modem_manager.detect_modems()
            logger.info(f"Detected {len(detected_modems)} modems: {detected_modems}")
    except Exception as e:
        logger.error(f"Failed to detect modems during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Modem SIM Card Management System API")
    try:
        await multi_modem_manager.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(SimManagerException)
async def sim_manager_exception_handler(request, exc: SimManagerException):
    """Handle SimManager exceptions."""
    status_code = get_http_status_code(exc)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.message,
            error_code=exc.error_code,
            details=exc.details
        ).dict()
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation error",
            error_code="VALIDATION_ERROR",
            details={"errors": exc.errors()}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"exception": str(exc)}
        ).dict()
    )


# Health and monitoring endpoints
@app.get("/api/health", response_model=SuccessResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        SuccessResponse: System health status
    """
    with log_operation(logger, "Health Check"):
        return SuccessResponse(
            message="System is healthy",
            data={
                "status": "healthy",
                "version": settings.API_VERSION,
                "connected_modems": len(multi_modem_manager.get_connected_modems())
            }
        )


@app.get("/api/performance", tags=["System"])
async def get_performance_metrics():
    """
    Get performance metrics for monitoring.
    
    Returns:
        Dict: Performance metrics including connected modems, total modems, and WebSocket connections
    """
    with log_operation(logger, "Get Performance Metrics"):
        # Get basic metrics
        connected_modems = multi_modem_manager.get_connected_modems()
        total_modems = len(await multi_modem_manager.detect_modems())
        
        # Log performance metrics
        log_performance(logger, "api_performance", 
            connected_modems=len(connected_modems),
            total_modems=total_modems,
            active_websocket_connections=len(manager.active_connections)
        )
        
        return {
            "connected_modems": len(connected_modems),
            "total_modems": total_modems,
            "active_websocket_connections": len(manager.active_connections),
            "api_version": settings.API_VERSION
        }


# Multi-Modem Management Endpoints
@app.post("/api/modems/detect", response_model=ModemDetectionResponse, tags=["Multi-Modem Management"])
async def detect_modems():
    """
    Detect all available Huawei modems.
    
    Scans all serial ports and identifies Huawei modems that are responsive to AT commands.
    
    Returns:
        ModemDetectionResponse: List of detected modems with their information
    """
    with log_operation(logger, "Modem Detection"):
        detected_modems = await multi_modem_manager.detect_modems()
        connected_modems = multi_modem_manager.get_connected_modems()
        
        return ModemDetectionResponse(
            detected_modems=detected_modems,  # This is already a list of strings
            connected_modems=connected_modems,
            total_detected=len(detected_modems),
            total_connected=len(connected_modems)
        )


@app.post("/api/modems/connect", response_model=SuccessResponse, tags=["Multi-Modem Management"])
async def connect_modem(request: ModemConnectionRequest):
    """
    Connect to a specific modem.
    
    Establishes a connection to the specified modem and initializes it for operations.
    
    Args:
        request: ModemConnectionRequest containing the modem ID to connect to
        
    Returns:
        SuccessResponse: Connection status and modem information
    """
    with log_operation(logger, f"Connect Modem {request.modem_id}"):
        success = await multi_modem_manager.connect_modem(request.modem_id)
        if success:
            modem_info = multi_modem_manager.get_modem_info(request.modem_id)
            return SuccessResponse(
                message=f"Successfully connected to modem {request.modem_id}",
                data={
                    "modem_id": request.modem_id,
                    "port": modem_info.port if modem_info else None,
                    "connected_modems": len(multi_modem_manager.get_connected_modems())
                }
            )
        else:
            raise ModemNotConnectedException(f"Failed to connect to modem {request.modem_id}")


@app.post("/api/modems/disconnect", response_model=SuccessResponse, tags=["Multi-Modem Management"])
async def disconnect_modem(request: ModemDisconnectionRequest):
    """
    Disconnect from a specific modem.
    
    Closes the connection to the specified modem and releases resources.
    
    Args:
        request: ModemDisconnectionRequest containing the modem ID to disconnect from
        
    Returns:
        SuccessResponse: Disconnection status
    """
    with log_operation(logger, f"Disconnect Modem {request.modem_id}"):
        success = await multi_modem_manager.disconnect_modem(request.modem_id)
        if success:
            return SuccessResponse(
                message=f"Successfully disconnected from modem {request.modem_id}",
                data={
                    "modem_id": request.modem_id,
                    "connected_modems": len(multi_modem_manager.get_connected_modems())
                }
            )
        else:
            raise ModemNotConnectedException(f"Failed to disconnect from modem {request.modem_id}")


@app.get("/api/modems/status", response_model=MultiModemStatus, tags=["Multi-Modem Management"])
async def get_all_modems_status():
    """
    Get status of all connected modems.
    
    Returns comprehensive status information for all currently connected modems.
    
    Returns:
        MultiModemStatus: Status information for all connected modems
    """
    with log_operation(logger, "Get All Modems Status"):
        return await multi_modem_manager.get_all_modems_status()


# Per-Modem Operations
@app.get("/api/modems/{modem_id}/status", response_model=ModemStatus, tags=["Per-Modem Operations"])
async def get_modem_status(modem_id: str):
    """
    Get status of a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        
    Returns:
        ModemStatus: Detailed status information for the specified modem
    """
    with log_operation(logger, f"Get Modem Status {modem_id}"):
        return await multi_modem_manager.get_modem_status(modem_id)


@app.get("/api/modems/{modem_id}/sim-info", response_model=SimInfo, tags=["Per-Modem Operations"])
async def get_modem_sim_info(modem_id: str):
    """
    Get SIM card information for a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        
    Returns:
        SimInfo: SIM card information including IMSI, ICCID, and operator details
    """
    with log_operation(logger, f"Get SIM Info {modem_id}"):
        return await multi_modem_manager.get_modem_sim_info(modem_id)


@app.get("/api/modems/{modem_id}/sms", response_model=List[SmsMessage], tags=["Per-Modem Operations"])
async def get_modem_sms(modem_id: str):
    """
    Get SMS messages from a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        
    Returns:
        List[SmsMessage]: List of SMS messages stored on the modem
    """
    with log_operation(logger, f"Get SMS {modem_id}"):
        return await multi_modem_manager.get_modem_sms(modem_id)


@app.post("/api/modems/{modem_id}/sms/send", response_model=SuccessResponse, tags=["Per-Modem Operations"])
async def send_modem_sms(modem_id: str, request: SmsRequest):
    """
    Send SMS from a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        request: SmsRequest containing recipient number and message content
        
    Returns:
        SuccessResponse: SMS sending status and message ID
    """
    with log_operation(logger, f"Send SMS {modem_id} to {request.number}"):
        success = await multi_modem_manager.send_modem_sms(modem_id, request.number, request.message)
        if success:
            return SuccessResponse(
                message=f"SMS sent successfully from modem {modem_id}",
                data={
                    "modem_id": modem_id,
                    "recipient": request.number,
                    "success": True
                }
            )
        else:
            raise SmsException(f"Failed to send SMS from modem {modem_id}")


@app.delete("/api/modems/{modem_id}/sms/{message_id}", response_model=SuccessResponse, tags=["Per-Modem Operations"])
async def delete_modem_sms(modem_id: str, message_id: int):
    """
    Delete SMS message from a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        message_id: ID of the SMS message to delete
        
    Returns:
        SuccessResponse: Deletion status
    """
    with log_operation(logger, f"Delete SMS {message_id} from {modem_id}"):
        await multi_modem_manager.delete_modem_sms(modem_id, message_id)
        return SuccessResponse(
            message=f"SMS {message_id} deleted successfully from modem {modem_id}",
            data={
                "modem_id": modem_id,
                "message_id": message_id
            }
        )


@app.post("/api/modems/{modem_id}/ussd", response_model=UssdResponse, tags=["Per-Modem Operations"])
async def send_modem_ussd(modem_id: str, request: UssdRequest):
    """
    Send USSD command from a specific modem.
    
    Args:
        modem_id: Unique identifier of the modem
        request: UssdRequest containing the USSD command to send
        
    Returns:
        UssdResponse: USSD command response
    """
    with log_operation(logger, f"Send USSD {request.command} from {modem_id}"):
        return await multi_modem_manager.send_modem_ussd(modem_id, request.command)


@app.get("/api/modems/{modem_id}/balance", response_model=UssdResponse, tags=["Per-Modem Operations"])
async def get_modem_balance(modem_id: str):
    """
    Get account balance from a specific modem.
    
    Attempts to retrieve the account balance using various USSD commands
    based on the detected operator.
    
    Args:
        modem_id: Unique identifier of the modem
        
    Returns:
        UssdResponse: Balance information or error details
    """
    with log_operation(logger, f"Get Balance {modem_id}"):
        return await multi_modem_manager.get_modem_balance(modem_id)


# Legacy Endpoints (Backward Compatibility)
@app.get("/api/status", response_model=ModemStatus, tags=["Legacy"])
async def get_status():
    """
    Get status of the first connected modem (legacy endpoint).
    
    Returns:
        ModemStatus: Status of the first connected modem
    """
    with log_operation(logger, "Get Status (Legacy)"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        return await multi_modem_manager.get_modem_status(first_modem_id)


@app.get("/api/sim-info", response_model=SimInfo, tags=["Legacy"])
async def get_sim_info():
    """
    Get SIM information of the first connected modem (legacy endpoint).
    
    Returns:
        SimInfo: SIM information of the first connected modem
    """
    with log_operation(logger, "Get SIM Info (Legacy)"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        return await multi_modem_manager.get_modem_sim_info(first_modem_id)


@app.get("/api/sms", response_model=List[SmsMessage], tags=["Legacy"])
async def get_sms():
    """
    Get SMS messages from the first connected modem (legacy endpoint).
    
    Returns:
        List[SmsMessage]: SMS messages from the first connected modem
    """
    with log_operation(logger, "Get SMS (Legacy)"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        return await multi_modem_manager.get_modem_sms(first_modem_id)


@app.post("/api/sms/send", response_model=SuccessResponse, tags=["Legacy"])
async def send_sms(request: SmsRequest):
    """
    Send SMS from the first connected modem (legacy endpoint).
    
    Args:
        request: SmsRequest containing recipient number and message content
        
    Returns:
        SuccessResponse: SMS sending status
    """
    with log_operation(logger, f"Send SMS (Legacy) to {request.number}"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        success = await multi_modem_manager.send_modem_sms(first_modem_id, request.number, request.message)
        if success:
            return SuccessResponse(
                message=f"SMS sent successfully from modem {first_modem_id}",
                data={
                    "modem_id": first_modem_id,
                    "recipient": request.number,
                    "success": True
                }
            )
        else:
            raise SmsException(f"Failed to send SMS from modem {first_modem_id}")


@app.delete("/api/sms/{message_id}", response_model=SuccessResponse, tags=["Legacy"])
async def delete_sms(message_id: int):
    """
    Delete SMS message from the first connected modem (legacy endpoint).
    
    Args:
        message_id: ID of the SMS message to delete
        
    Returns:
        SuccessResponse: Deletion status
    """
    with log_operation(logger, f"Delete SMS (Legacy) {message_id}"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        await multi_modem_manager.delete_modem_sms(first_modem_id, message_id)
        return SuccessResponse(
            message=f"SMS {message_id} deleted successfully from modem {first_modem_id}",
            data={
                "modem_id": first_modem_id,
                "message_id": message_id
            }
        )


@app.post("/api/ussd", response_model=UssdResponse, tags=["Legacy"])
async def send_ussd(request: UssdRequest):
    """
    Send USSD command from the first connected modem (legacy endpoint).
    
    Args:
        request: UssdRequest containing the USSD command to send
        
    Returns:
        UssdResponse: USSD command response
    """
    with log_operation(logger, f"Send USSD (Legacy) {request.command}"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        return await multi_modem_manager.send_modem_ussd(first_modem_id, request.command)


@app.get("/api/balance", response_model=UssdResponse, tags=["Legacy"])
async def get_balance():
    """
    Get account balance from the first connected modem (legacy endpoint).
    
    Returns:
        UssdResponse: Balance information
    """
    with log_operation(logger, "Get Balance (Legacy)"):
        connected_modems = multi_modem_manager.get_connected_modems()
        if not connected_modems:
            raise ModemNotConnectedException("No modems connected")
        
        first_modem_id = connected_modems[0]
        return await multi_modem_manager.get_modem_balance(first_modem_id)


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time status updates.
    
    Provides real-time updates for modem status, SMS notifications, and system events.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Multi-Modem SIM Card Management System API server")
    logger.info(f"API Documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"ReDoc Documentation available at: http://{settings.HOST}:{settings.PORT}/redoc")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST, 
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
