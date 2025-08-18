from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
import sys
import os

from core.modem_manager import ModemManager
from core.operator_manager import OperatorManager
from models.models import SimInfo, SmsMessage, UssdResponse, ModemStatus
from config import settings
from core.logger import setup_logging, get_api_logger
from core.exceptions import (
    ModemNotConnectedException,
    ModemDetectionException,
    SmsException,
    UssdException,
    SimManagerException
)

# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = get_api_logger()

app = FastAPI(
    title="SIM Card Management System", 
    version="1.0.0",
    description="Professional SIM card management system for Algerian operators"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
modem_manager = ModemManager()
operator_manager = OperatorManager()

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize the modem connection on startup"""
    try:
        logger.info("Starting SIM Card Management System...")
        await modem_manager.initialize()
        logger.info("Modem manager initialized successfully")
    except ModemDetectionException as e:
        logger.warning(f"Modem not detected on startup: {e}")
        logger.info("System will continue to run, modem can be connected later")
    except Exception as e:
        logger.error(f"Failed to initialize modem manager: {e}")
        logger.info("System will continue to run in degraded mode")

@app.get("/api/status")
async def get_status():
    """Get current modem and connection status"""
    try:
        logger.debug("Getting modem status...")
        status = await modem_manager.get_status()
        logger.debug(f"Status retrieved: connected={status.connected}")
        return status
    except ModemNotConnectedException as e:
        logger.warning(f"Modem not connected: {e}")
        return ModemStatus(connected=False, error=str(e))
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/api/sim-info")
async def get_sim_info():
    """Get detailed SIM card information"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        sim_info = await modem_manager.get_sim_info()
        operator_info = operator_manager.detect_operator(sim_info.imsi, sim_info.iccid)
        
        result = {
            **sim_info.dict(),
            "operator": operator_info
        }
        
        # Log successful SIM detection
        if sim_info.imsi:
            logger.info(f"SIM info retrieved successfully - Operator: {operator_info.get('name', 'Unknown') if operator_info else 'Unknown'}")
        
        return result
    except Exception as e:
        logger.error(f"Error getting SIM info: {e}")
        # Return partial information even if some commands fail
        try:
            # Try to get basic status at least
            status = await modem_manager.get_status()
            return {
                "imsi": None,
                "iccid": None,
                "imei": None,
                "msisdn": None,
                "signal_strength": status.signal_strength,
                "network_type": status.network_type,
                "network_operator": status.operator,
                "operator": None,
                "error": str(e)
            }
        except:
            raise HTTPException(status_code=500, detail=f"Failed to get SIM info: {str(e)}")

@app.get("/api/sms")
async def get_sms():
    """Get all SMS messages"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        messages = await modem_manager.get_sms_messages()
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sms/send")
async def send_sms(phone_number: str, message: str):
    """Send an SMS message"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        result = await modem_manager.send_sms(phone_number, message)
        
        # Broadcast SMS sent event
        await manager.broadcast({
            "type": "sms_sent",
            "data": {"phone_number": phone_number, "message": message, "result": result}
        })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sms/{message_id}")
async def delete_sms(message_id: int):
    """Delete an SMS message"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        result = await modem_manager.delete_sms(message_id)
        
        # Broadcast SMS deleted event
        await manager.broadcast({
            "type": "sms_deleted",
            "data": {"message_id": message_id}
        })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error deleting SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ussd")
async def send_ussd(command: str):
    """Send USSD command"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        response = await modem_manager.send_ussd(command)
        return {"success": True, "response": response}
    except Exception as e:
        logger.error(f"Error sending USSD: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/balance")
async def get_balance():
    """Get account balance using operator-specific USSD codes"""
    try:
        if not modem_manager.is_connected():
            raise HTTPException(status_code=400, detail="Modem not connected")
        
        sim_info = await modem_manager.get_sim_info()
        operator_info = operator_manager.detect_operator(sim_info.imsi, sim_info.iccid)
        
        if not operator_info or not operator_info.get("balance_ussd"):
            raise HTTPException(status_code=400, detail="Balance check not supported for this operator")
        
        balance_ussd = operator_info["balance_ussd"]
        response = await modem_manager.send_ussd(balance_ussd)
        
        return {
            "success": True,
            "operator": operator_info["name"],
            "ussd_command": balance_ussd,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/operators")
async def get_operators():
    """Get list of supported operators"""
    return {"operators": operator_manager.get_all_operators()}

@app.get("/api/sim-status")
async def get_sim_status():
    """Get comprehensive SIM status with automatic detection"""
    try:
        if not modem_manager.is_connected():
            return {
                "connected": False,
                "sim_detected": False,
                "error": "Modem not connected"
            }
        
        # Get basic status
        status = await modem_manager.get_status()
        
        # Try to get SIM info
        sim_detected = False
        sim_info = None
        operator_info = None
        
        try:
            sim_info = await modem_manager.get_sim_info()
            sim_detected = bool(sim_info.imsi or sim_info.iccid)
            if sim_detected:
                operator_info = operator_manager.detect_operator(sim_info.imsi, sim_info.iccid)
        except Exception as e:
            logger.warning(f"Could not get SIM info: {e}")
        
        return {
            "connected": status.connected,
            "sim_detected": sim_detected,
            "modem_info": {
                "port": status.port,
                "model": status.model,
                "firmware": status.firmware
            },
            "sim_info": {
                "imsi": sim_info.imsi if sim_info else None,
                "iccid": sim_info.iccid if sim_info else None,
                "imei": sim_info.imei if sim_info else None,
                "msisdn": sim_info.msisdn if sim_info else None,
                "signal_strength": sim_info.signal_strength if sim_info else status.signal_strength,
                "network_type": sim_info.network_type if sim_info else status.network_type,
                "network_operator": sim_info.network_operator if sim_info else status.operator
            },
            "operator": operator_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting SIM status: {e}")
        return {
            "connected": False,
            "sim_detected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic status updates
            try:
                status = await modem_manager.get_status()
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "data": status.dict()
                }))
            except:
                pass
            
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
