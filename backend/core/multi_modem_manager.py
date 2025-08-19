"""
Multi-modem management for the Multi-Modem SIM Card Management System.

This module provides the MultiModemManager class for managing multiple Huawei USB modems,
including detection, connection management, load balancing, and concurrent operations.
"""

import asyncio
import serial.tools.list_ports
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

from backend.core.modem_manager import ModemManager
from backend.core.logger import SimManagerLogger, log_operation, log_performance
from backend.core.exceptions import (
    MultiModemException, ModemLimitExceededException, ModemAlreadyConnectedException,
    ModemNotFoundException, ModemNotConnectedException, ModemDetectionException
)
from backend.config import get_settings
from backend.models.models import (
    ModemStatus, SimInfo, SmsMessage, UssdResponse, ModemInfo, MultiModemStatus
)


class MultiModemManager:
    """
    Manages multiple Huawei USB modems concurrently.
    
    This class provides centralized management for multiple modems including
    automatic detection, connection management, load balancing, and concurrent
    operations across all connected modems.
    """
    
    def __init__(self, settings=None):
        """
        Initialize the MultiModemManager.
        
        Args:
            settings: Application settings object
        """
        self.settings = settings or get_settings()
        self.logger = SimManagerLogger(self.settings)
        
        # Modem management
        self.modems: Dict[str, ModemManager] = {}
        self.modem_info: Dict[str, ModemInfo] = {}
        self.active_modem_ids: List[str] = []
        
        # Concurrency control
        self._lock = asyncio.Lock()
        
        # Performance tracking
        self._operation_count = 0
        self._last_operation_time = datetime.now()
        
        self.logger.info("MultiModemManager initialized")
        self.logger.info(f"Max concurrent modems: {self.settings.MAX_CONCURRENT_MODEMS}")
    
    async def detect_modems(self) -> List[str]:
        """
        Detect all available Huawei modems.
        
        Returns:
            List of detected modem IDs
            
        Raises:
            ModemDetectionException: If detection fails
        """
        with log_operation(self.logger, "Detect modems"):
            try:
                detected_modems = []
                
                # Get all available serial ports
                ports = list(serial.tools.list_ports.comports())
                self.logger.info(f"Found {len(ports)} serial ports")
                
                for port in ports:
                    try:
                        # Check if it's a Huawei modem
                        if self._is_huawei_modem(port):
                            modem_id = f"huawei_{port.device}"
                            
                            # Test if modem responds to AT commands
                            if await self._test_at_commands(port.device):
                                detected_modems.append(modem_id)
                                self.logger.info(f"Detected Huawei modem: {modem_id} on {port.device}")
                                
                                # Store modem information
                                self.modem_info[modem_id] = ModemInfo(
                                    modem_id=modem_id,
                                    port=port.device,
                                    connected_at=datetime.now(),
                                    last_activity=datetime.now()
                                )
                            else:
                                self.logger.warning(f"Huawei modem on {port.device} not responsive to AT commands")
                        else:
                            self.logger.debug(f"Port {port.device} is not a Huawei modem")
                            
                    except Exception as e:
                        self.logger.warning(f"Error checking port {port.device}: {e}")
                
                self.logger.info(f"Detection completed: {len(detected_modems)} modems found")
                
                # Log performance metrics
                log_performance(self.logger, "modem_detection", 
                    total_ports=len(ports),
                    detected_modems=len(detected_modems),
                    huawei_modems=len([p for p in ports if self._is_huawei_modem(p)])
                )
                
                return detected_modems
                
            except Exception as e:
                self.logger.error(f"Modem detection failed: {e}")
                raise ModemDetectionException(f"Failed to detect modems: {e}")
    
    def _is_huawei_modem(self, port) -> bool:
        """
        Check if a port is a Huawei modem.
        
        Args:
            port: Serial port object
            
        Returns:
            True if it's a Huawei modem
        """
        # Check vendor ID and product ID for Huawei
        huawei_vids = [0x12d1, 0x19d2, 0x1c9e]  # Common Huawei vendor IDs
        
        if hasattr(port, 'vid') and port.vid in huawei_vids:
            return True
        
        # Check description for Huawei keywords
        if hasattr(port, 'description'):
            description = port.description.lower()
            huawei_keywords = ['huawei', 'e3531', 'e3131', 'e3372', 'e5573', 'e5785']
            return any(keyword in description for keyword in huawei_keywords)
        
        return False
    
    async def _test_at_commands(self, port: str) -> bool:
        """
        Test if a port responds to AT commands.
        
        Args:
            port: Serial port to test
            
        Returns:
            True if port responds to AT commands
        """
        try:
            # Create temporary connection to test AT commands
            with serial.Serial(
                port=port,
                baudrate=self.settings.MODEM_BAUDRATE,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            ) as test_connection:
                # Some devices require DTR/RTS asserted
                try:
                    test_connection.dtr = True
                    test_connection.rts = True
                except Exception:
                    pass
                # Flush any stale data
                try:
                    test_connection.reset_input_buffer()
                    test_connection.reset_output_buffer()
                except Exception:
                    pass

                # Try a short sequence of probe commands
                probe_commands = [b"AT\r\n", b"ATZ\r\n", b"ATI\r\n"]
                for cmd in probe_commands:
                    try:
                        test_connection.write(cmd)
                    except Exception:
                        continue

                    # Read for up to 2 seconds looking for OK or typical ID lines
                    deadline = time.monotonic() + 2.0
                    buffer = ""
                    while time.monotonic() < deadline:
                        try:
                            if test_connection.in_waiting:
                                line = test_connection.readline().decode('utf-8', errors='ignore').strip()
                                if not line:
                                    await asyncio.sleep(0.05)
                                    continue
                                buffer += line + "\n"
                                if "OK" in line or "+CSQ" in line or "Manufacturer" in line or "Model" in line:
                                    return True
                        except Exception:
                            # Keep probing within the deadline
                            await asyncio.sleep(0.05)
                            continue
                        await asyncio.sleep(0.05)
                # As a last check, consider any buffered OK
                return "OK" in buffer
        except Exception as e:
            self.logger.debug(f"AT command test failed for {port}: {e}")
            return False
    
    async def connect_modem(self, modem_id: str) -> bool:
        """
        Connect to a specific modem.
        
        Args:
            modem_id: Modem identifier to connect to
            
        Returns:
            True if connection successful
            
        Raises:
            ModemLimitExceededException: If maximum modems limit reached
            ModemAlreadyConnectedException: If modem is already connected
            ModemNotFoundException: If modem not found
        """
        async with self._lock:
            with log_operation(self.logger, f"Connect modem {modem_id}"):
                try:
                    # Check if modem is already connected
                    if modem_id in self.modems:
                        raise ModemAlreadyConnectedException(f"Modem {modem_id} is already connected")
                    
                    # Check if we've reached the maximum number of modems
                    if len(self.modems) >= self.settings.MAX_CONCURRENT_MODEMS:
                        raise ModemLimitExceededException(
                            f"Maximum number of modems ({self.settings.MAX_CONCURRENT_MODEMS}) reached"
                        )
                    
                    # Check if modem info exists
                    if modem_id not in self.modem_info:
                        raise ModemNotFoundException(modem_id)
                    
                    # Extract port from modem ID
                    port = self.modem_info[modem_id].port
                    
                    # Create and connect modem manager
                    modem_manager = ModemManager(self.settings)
                    await self._connect_modem_to_port(modem_manager, port)
                    
                    # Store the connected modem
                    self.modems[modem_id] = modem_manager
                    self.active_modem_ids.append(modem_id)
                    
                    # Update modem info
                    self.modem_info[modem_id].connected_at = datetime.now()
                    self.modem_info[modem_id].last_activity = datetime.now()
                    
                    self.logger.info(f"Successfully connected to modem {modem_id} on {port}")
                    
                    # Log performance metrics
                    log_performance(self.logger, "modem_connection", 
                        modem_id=modem_id,
                        port=port,
                        total_connected=len(self.modems)
                    )
                    
                    return True
                    
                except (ModemLimitExceededException, ModemAlreadyConnectedException, ModemNotFoundException):
                    raise
                except Exception as e:
                    self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                    raise MultiModemException(f"Failed to connect to modem {modem_id}: {e}", "connect_modem")
    
    async def _connect_modem_to_port(self, modem_manager: ModemManager, port: str):
        """
        Connect a modem manager to a specific port.
        
        Args:
            modem_manager: ModemManager instance
            port: Serial port to connect to
            
        Raises:
            MultiModemException: If connection fails
        """
        try:
            # Connect to the port
            await modem_manager._connect_to_modem(port)
            
            # Configure the modem
            await modem_manager._configure_modem()
            
            # Mark as initialized
            modem_manager.is_initialized = True
            modem_manager.port = port
            
            self.logger.info(f"Modem manager connected and configured on {port}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect modem manager to {port}: {e}")
            raise MultiModemException(f"Failed to connect modem manager to {port}: {e}", "connect_modem_to_port")
    
    async def disconnect_modem(self, modem_id: str) -> bool:
        """
        Disconnect from a specific modem.
        
        Args:
            modem_id: Modem identifier to disconnect from
            
        Returns:
            True if disconnection successful
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        async with self._lock:
            with log_operation(self.logger, f"Disconnect modem {modem_id}"):
                try:
                    # Check if modem is connected
                    if modem_id not in self.modems:
                        raise ModemNotFoundException(modem_id)
                    
                    # Close the modem connection
                    modem_manager = self.modems[modem_id]
                    modem_manager.close()
                    
                    # Remove from active modems
                    del self.modems[modem_id]
                    if modem_id in self.active_modem_ids:
                        self.active_modem_ids.remove(modem_id)
                    
                    # Update modem info
                    if modem_id in self.modem_info:
                        self.modem_info[modem_id].last_activity = datetime.now()
                    
                    self.logger.info(f"Successfully disconnected from modem {modem_id}")
                    
                    # Log performance metrics
                    log_performance(self.logger, "modem_disconnection", 
                        modem_id=modem_id,
                        total_connected=len(self.modems)
                    )
                    
                    return True
                    
                except ModemNotFoundException:
                    raise
                except Exception as e:
                    self.logger.error(f"Failed to disconnect from modem {modem_id}: {e}")
                    raise MultiModemException(f"Failed to disconnect from modem {modem_id}: {e}", "disconnect_modem")
    
    async def get_all_modems_status(self) -> MultiModemStatus:
        """
        Get status of all modems.
        
        Returns:
            MultiModemStatus object
        """
        with log_operation(self.logger, "Get all modems status"):
            try:
                statuses = {}
                
                for modem_id, modem_manager in self.modems.items():
                    try:
                        status = await modem_manager.get_status()
                        statuses[modem_id] = status
                        
                        # Update last activity
                        if modem_id in self.modem_info:
                            self.modem_info[modem_id].last_activity = datetime.now()
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to get status for modem {modem_id}: {e}")
                        # Return error status
                        statuses[modem_id] = ModemStatus(
                            connected=False,
                            modem_id=modem_id,
                            error=str(e)
                        )
                
                self.logger.info(f"Retrieved status for {len(statuses)} modems")
                
                # Create MultiModemStatus object
                return MultiModemStatus(
                    total_modems=len(self.modem_info),
                    connected_modems=len(self.modems),
                    modems=statuses
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get all modems status: {e}")
                raise MultiModemException(f"Failed to get all modems status: {e}", "get_all_modems_status")
    
    async def get_modem_status(self, modem_id: str) -> ModemStatus:
        """
        Get status of a specific modem.
        
        Args:
            modem_id: Modem identifier
            
        Returns:
            ModemStatus object
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Get modem status {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                status = await modem_manager.get_status()
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return status
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get status for modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to get status for modem {modem_id}: {e}", "get_modem_status")
    
    async def get_modem_sim_info(self, modem_id: str) -> SimInfo:
        """
        Get SIM information for a specific modem.
        
        Args:
            modem_id: Modem identifier
            
        Returns:
            SimInfo object
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Get SIM info {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                sim_info = await modem_manager.get_sim_info()
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return sim_info
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get SIM info for modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to get SIM info for modem {modem_id}: {e}", "get_modem_sim_info")
    
    async def get_modem_sms(self, modem_id: str) -> List[SmsMessage]:
        """
        Get SMS messages for a specific modem.
        
        Args:
            modem_id: Modem identifier
            
        Returns:
            List of SmsMessage objects
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Get SMS {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                messages = await modem_manager.get_sms_messages()
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return messages
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get SMS for modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to get SMS for modem {modem_id}: {e}", "get_modem_sms")
    
    async def send_modem_sms(self, modem_id: str, number: str, message: str) -> bool:
        """
        Send SMS from a specific modem.
        
        Args:
            modem_id: Modem identifier
            number: Phone number to send SMS to
            message: SMS message content
            
        Returns:
            True if SMS sent successfully
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Send SMS {modem_id} to {number}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                success = await modem_manager.send_sms(number, message)
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return success
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to send SMS from modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to send SMS from modem {modem_id}: {e}", "send_modem_sms")
    
    async def delete_modem_sms(self, modem_id: str, message_id: int) -> bool:
        """
        Delete SMS from a specific modem.
        
        Args:
            modem_id: Modem identifier
            message_id: SMS message ID to delete
            
        Returns:
            True if SMS deleted successfully
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Delete SMS {message_id} from {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                success = await modem_manager.delete_sms(message_id)
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return success
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to delete SMS from modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to delete SMS from modem {modem_id}: {e}", "delete_modem_sms")
    
    async def send_modem_ussd(self, modem_id: str, command: str) -> UssdResponse:
        """
        Send USSD command from a specific modem.
        
        Args:
            modem_id: Modem identifier
            command: USSD command to send
            
        Returns:
            UssdResponse object
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Send USSD {command} from {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                response = await modem_manager.send_ussd(command)
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return response
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to send USSD from modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to send USSD from modem {modem_id}: {e}", "send_modem_ussd")
    
    async def get_modem_balance(self, modem_id: str) -> UssdResponse:
        """
        Get balance for a specific modem.
        
        Args:
            modem_id: Modem identifier
            
        Returns:
            UssdResponse object with balance information
            
        Raises:
            ModemNotFoundException: If modem not found
        """
        with log_operation(self.logger, f"Get balance {modem_id}"):
            try:
                # Check if modem is connected, if not, try to connect it
                if modem_id not in self.modems:
                    self.logger.info(f"Modem {modem_id} not connected, attempting to connect...")
                    try:
                        await self.connect_modem(modem_id)
                        self.logger.info(f"Successfully connected to modem {modem_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to connect to modem {modem_id}: {e}")
                        raise ModemNotFoundException(f"Modem {modem_id} not found or could not be connected")
                
                modem_manager = self.modems[modem_id]
                response = await modem_manager.get_balance()
                
                # Update last activity
                if modem_id in self.modem_info:
                    self.modem_info[modem_id].last_activity = datetime.now()
                
                return response
                
            except ModemNotFoundException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get balance for modem {modem_id}: {e}")
                raise MultiModemException(f"Failed to get balance for modem {modem_id}: {e}", "get_modem_balance")
    
    def get_connected_modems(self) -> List[str]:
        """
        Get list of currently connected modem IDs.
        
        Returns:
            List of connected modem IDs
        """
        return list(self.modems.keys())
    
    def get_modem_info(self, modem_id: str) -> Optional[ModemInfo]:
        """
        Get additional information about a modem.
        
        Args:
            modem_id: Modem identifier
            
        Returns:
            ModemInfo object or None if not found
        """
        return self.modem_info.get(modem_id)
    
    async def cleanup(self):
        """Clean up all modem connections."""
        with log_operation(self.logger, "Cleanup all modems"):
            try:
                for modem_id in list(self.modems.keys()):
                    try:
                        await self.disconnect_modem(modem_id)
                    except Exception as e:
                        self.logger.warning(f"Failed to disconnect modem {modem_id} during cleanup: {e}")
                
                self.logger.info("All modem connections cleaned up")
                
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "total_modems": len(self.modem_info),
            "connected_modems": len(self.modems),
            "active_modem_ids": self.active_modem_ids,
            "operation_count": self._operation_count,
            "last_operation_time": self._last_operation_time.isoformat()
        }
