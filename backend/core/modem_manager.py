"""
Single modem management for the Multi-Modem SIM Card Management System.

This module provides the ModemManager class for managing a single Huawei USB modem,
including connection, AT command execution, SMS, USSD, and SIM card operations.
"""

import asyncio
import serial
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from backend.core.logger import SimManagerLogger, log_operation, log_performance
from backend.core.exceptions import (
    ModemNotConnectedException, ModemDetectionException, SerialPortException,
    ATCommandException, ATCommandTimeoutException, SmsException, SmsSendException,
    SmsReadException, SmsDeleteException, UssdException, UssdTimeoutException,
    SimCardException, SimCardNotDetectedException
)
from backend.config import get_settings
from backend.models.models import (
    ModemStatus, SimInfo, SmsMessage, UssdResponse, NetworkType, SmsStatus
)
from .ussd_encoder import UssdEncoderDecoder


class ModemManager:
    """
    Manages a single Huawei USB modem connection and operations.
    
    This class handles all communication with a single modem including
    connection management, AT command execution, SMS operations, USSD
    commands, and SIM card information retrieval.
    """
    
    def __init__(self, settings=None):
        """
        Initialize the ModemManager.
        
        Args:
            settings: Application settings object
        """
        self.settings = settings or get_settings()
        self.logger = SimManagerLogger(self.settings)
        
        # Connection state
        self.serial_connection: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self.is_initialized: bool = False
        
        # Modem information
        self.model: Optional[str] = None
        self.firmware: Optional[str] = None
        self.imei: Optional[str] = None
        
        # SIM information cache
        self._sim_info_cache: Optional[SimInfo] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = 300  # 5 minutes cache
        
        self.logger.debug("ModemManager initialized")
    
    async def _connect_to_modem(self, port: str) -> bool:
        """
        Connect to a modem on the specified port.
        
        Args:
            port: Serial port to connect to
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            SerialPortException: If connection fails
        """
        with log_operation(self.logger, f"Connect to modem on {port}"):
            try:
                # Close existing connection if any
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                
                # Create new serial connection
                self.serial_connection = serial.Serial(
                port=port,
                    baudrate=self.settings.MODEM_BAUDRATE,
                    timeout=self.settings.MODEM_TIMEOUT,
                    bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                self.port = port
                self.logger.info(f"Serial connection established on {port}")
                
                # Test AT command to verify modem is responsive
                response = await self._send_at_command("AT", timeout=3)
                if "OK" not in response:
                    raise SerialPortException(f"Modem on {port} not responsive to AT commands")
                
                self.logger.info(f"Modem on {port} is responsive")
                return True
                
            except serial.SerialException as e:
                self.logger.error(f"Serial connection failed on {port}: {e}")
                raise SerialPortException(f"Failed to connect to {port}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error connecting to {port}: {e}")
                raise SerialPortException(f"Unexpected error connecting to {port}: {e}")
    
    async def _configure_modem(self) -> bool:
        """
        Configure the modem for optimal operation.
        
        Returns:
            True if configuration successful
            
        Raises:
            ATCommandException: If configuration fails
        """
        with log_operation(self.logger, "Configure modem"):
            try:
                # Basic AT commands to configure modem
                config_commands = [
                    ("ATZ", "Reset modem"),
                    ("AT&F", "Factory reset"),
                    ("AT+CPIN?", "Check SIM status"),
                    ("AT+CREG?", "Check network registration"),
                    ("AT+CSQ", "Check signal quality"),
                    ("AT+CGATT?", "Check GPRS attachment"),
                    ("AT+CGDCONT=1,\"IP\",\"internet\"", "Set APN"),
                    ("AT+CMGF=1", "Set SMS text mode"),
                    ("AT+CNMI=2,2,0,0,0", "Configure SMS notifications"),
                    ("AT+CLIP=1", "Enable caller ID"),
                    ("AT+COPS=0", "Set automatic operator selection")
                ]
                
                for command, description in config_commands:
                    try:
                        self.logger.debug(f"Configuring: {description}")
                        response = await self._send_at_command(command, timeout=5)
                        if "ERROR" in response:
                            self.logger.warning(f"Configuration command failed: {command} - {response}")
                        else:
                            self.logger.debug(f"Configuration successful: {description}")
                    except Exception as e:
                        self.logger.warning(f"Configuration command failed: {command} - {e}")
                
                # Get modem information
                await self._get_modem_info()
                
                self.logger.info("Modem configuration completed")
                return True
                
            except Exception as e:
                self.logger.error(f"Modem configuration failed: {e}")
                raise ATCommandException(f"Failed to configure modem: {e}")
    
    async def _get_modem_info(self):
        """Get modem model and firmware information."""
        try:
            # Get model information
            model_response = await self._send_at_command("AT+CGMM")
            if "OK" in model_response:
                self.model = model_response.split('\n')[1].strip()
            
            # Get firmware version
            firmware_response = await self._send_at_command("AT+CGMR")
            if "OK" in firmware_response:
                self.firmware = firmware_response.split('\n')[1].strip()
            
            # Get IMEI
            imei_response = await self._send_at_command("AT+CGSN")
            if "OK" in imei_response:
                self.imei = imei_response.split('\n')[1].strip()
            
            self.logger.info(f"Modem info - Model: {self.model}, Firmware: {self.firmware}, IMEI: {self.imei}")
            
        except Exception as e:
            self.logger.warning(f"Failed to get modem info: {e}")
    
    async def _send_at_command(self, command: str, timeout: Optional[int] = None, retries: int = 3) -> str:
        """
        Send an AT command to the modem.
        
        Args:
            command: AT command to send
            timeout: Command timeout in seconds
            retries: Number of retry attempts
            
        Returns:
            Response from the modem
            
        Raises:
            ATCommandTimeoutException: If command times out
            ATCommandException: If command fails after retries
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ModemNotConnectedException("Modem is not connected")
        
        timeout = timeout or self.settings.MODEM_OPERATION_TIMEOUT
        last_error = None
        
        for attempt in range(retries):
            try:
                self.logger.debug(f"Sending AT command (attempt {attempt + 1}): {command}")
                
                # Clear input buffer
                self.serial_connection.reset_input_buffer()
                
                # Send command
                self.serial_connection.write(f"{command}\r\n".encode())
                
                # Read response
                response = ""
                start_time = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - start_time < timeout:
                    if self.serial_connection.in_waiting:
                        line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        response += line + "\n"
                        
                        # Check for end of response
                        if "OK" in line or "ERROR" in line or "FAIL" in line:
                            break
                    
                    await asyncio.sleep(0.1)
                else:
                    raise ATCommandTimeoutException(command, timeout)
                
                self.logger.debug(f"AT command response: {response.strip()}")
                return response
                
            except ATCommandTimeoutException:
                last_error = ATCommandTimeoutException(command, timeout)
                self.logger.warning(f"AT command timeout (attempt {attempt + 1}): {command}")
            except Exception as e:
                last_error = ATCommandException(f"Command failed: {command} - {e}")
                self.logger.error(f"AT command error (attempt {attempt + 1}): {command} - {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(1)  # Wait before retry
        
        # Log performance metrics
        log_performance(self.logger, "at_command_failure", 
            command=command,
            retries=retries,
            error=str(last_error)
        )
        
        raise last_error
    
    async def get_status(self) -> ModemStatus:
        """
        Get current modem status.
        
        Returns:
            ModemStatus object with current status information
        """
        with log_operation(self.logger, "Get modem status"):
            try:
                if not self.is_initialized:
                    return ModemStatus(
                        connected=False,
                        modem_id=f"huawei_{self.port}" if self.port else None,
                        port=self.port,
                        error="Modem not initialized"
                    )
                
                # Check connection
                if not self.serial_connection or not self.serial_connection.is_open:
                    return ModemStatus(
                        connected=False,
                        modem_id=f"huawei_{self.port}" if self.port else None,
                        port=self.port,
                        error="Serial connection lost"
                    )
                
                # Get signal strength
                signal_strength = None
                try:
                    csq_response = await self._send_at_command("AT+CSQ")
                    if "CSQ:" in csq_response:
                        csq_match = re.search(r'CSQ:\s*(\d+)', csq_response)
                        if csq_match:
                            raw_signal = int(csq_match.group(1))
                            # Convert to percentage (0-31 -> 0-100)
                            signal_strength = min(100, int((raw_signal / 31) * 100))
                except Exception as e:
                    self.logger.warning(f"Failed to get signal strength: {e}")
                
                # Get network registration status
                operator = None
                network_type = NetworkType.UNKNOWN
                try:
                    cops_response = await self._send_at_command("AT+COPS?")
                    if "COPS:" in cops_response:
                        cops_match = re.search(r'COPS:\s*\d+,(\d+),"([^"]+)"', cops_response)
                        if cops_match:
                            operator = cops_match.group(2)
                    
                    # Get network type
                    creg_response = await self._send_at_command("AT+CREG?")
                    if "CREG:" in creg_response:
                        creg_match = re.search(r'CREG:\s*\d+,(\d+)', creg_response)
                        if creg_match:
                            reg_status = int(creg_match.group(1))
                            if reg_status in [1, 5]:  # Registered
                                # Try to get network type from CGATT
                                try:
                                    cgatt_response = await self._send_at_command("AT+CGATT?")
                                    if "CGATT:" in cgatt_response:
                                        cgatt_match = re.search(r'CGATT:\s*(\d+)', cgatt_response)
                                        if cgatt_match and cgatt_match.group(1) == "1":
                                            network_type = NetworkType.LTE  # Assume LTE if GPRS attached
                                except:
                                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to get network info: {e}")
                
                return ModemStatus(
                    connected=True,
                    modem_id=f"huawei_{self.port}" if self.port else None,
                    port=self.port,
                    model=self.model,
                    firmware=self.firmware,
                    signal_strength=signal_strength,
                    network_type=network_type,
                    operator=operator
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get modem status: {e}")
                return ModemStatus(
                    connected=False,
                    modem_id=f"huawei_{self.port}" if self.port else None,
                    port=self.port,
                    error=str(e)
                )
    
    async def get_sim_info(self) -> SimInfo:
        """
        Get SIM card information.
        
        Returns:
            SimInfo object with SIM card details
            
        Raises:
            SimCardNotDetectedException: If SIM card is not detected
        """
        with log_operation(self.logger, "Get SIM info"):
            # Check cache first
            if (self._sim_info_cache and self._cache_timestamp and 
                (datetime.now() - self._cache_timestamp).seconds < self._cache_duration):
                self.logger.debug("Returning cached SIM info")
                return self._sim_info_cache
            
            try:
                # Check SIM status
                cpin_response = await self._send_at_command("AT+CPIN?")
                if "READY" not in cpin_response:
                    raise SimCardNotDetectedException("SIM card not ready")
                
                # Get IMSI
                imsi = None
                try:
                    cimi_response = await self._send_at_command("AT+CIMI")
                    if "OK" in cimi_response:
                        imsi = cimi_response.split('\n')[1].strip()
                except Exception as e:
                    self.logger.warning(f"Failed to get IMSI: {e}")
                
                # Get ICCID
                iccid = None
                try:
                    cccid_response = await self._send_at_command("AT+CCID")
                    if "OK" in cccid_response:
                        iccid = cccid_response.split('\n')[1].strip()
                except Exception as e:
                    self.logger.warning(f"Failed to get ICCID: {e}")
                
                # Get MSISDN (phone number)
                msisdn = None
                try:
                    cnumn_response = await self._send_at_command("AT+CNUM")
                    if "CNUM:" in cnumn_response:
                        cnum_match = re.search(r'CNUM:\s*"[^"]*","([^"]+)"', cnumn_response)
                        if cnum_match:
                            msisdn = cnum_match.group(1)
                except Exception as e:
                    self.logger.warning(f"Failed to get MSISDN: {e}")
                
                # Get signal strength
                signal_strength = None
                try:
                    csq_response = await self._send_at_command("AT+CSQ")
                    if "CSQ:" in csq_response:
                        csq_match = re.search(r'CSQ:\s*(\d+)', csq_response)
                        if csq_match:
                            raw_signal = int(csq_match.group(1))
                            signal_strength = min(100, int((raw_signal / 31) * 100))
                except Exception as e:
                    self.logger.warning(f"Failed to get signal strength: {e}")
                
                # Get operator information
                operator_name = None
                network_operator = None
                roaming = False
                network_type = NetworkType.UNKNOWN
                
                try:
                    cops_response = await self._send_at_command("AT+COPS?")
                    if "COPS:" in cops_response:
                        cops_match = re.search(r'COPS:\s*(\d+),(\d+),"([^"]+)"', cops_response)
                        if cops_match:
                            operator_name = cops_match.group(3)
                            roaming = cops_match.group(1) == "2"
                except Exception as e:
                    self.logger.warning(f"Failed to get operator info: {e}")
                
                # Create SIM info object
                sim_info = SimInfo(
                    imsi=imsi,
                    iccid=iccid,
                    msisdn=msisdn,
                    signal_strength=signal_strength,
                    operator_name=operator_name,
                    network_operator=network_operator,
                    roaming=roaming,
                    network_type=network_type
                )
                
                # Cache the result
                self._sim_info_cache = sim_info
                self._cache_timestamp = datetime.now()
                
                return sim_info
                
            except Exception as e:
                self.logger.error(f"Failed to get SIM info: {e}")
                raise SimCardNotDetectedException(f"Failed to get SIM info: {e}")
    
    async def get_sms_messages(self) -> List[SmsMessage]:
        """
        Get all SMS messages from the modem.
        
        Returns:
            List of SmsMessage objects
            
        Raises:
            SmsReadException: If SMS reading fails
        """
        with log_operation(self.logger, "Get SMS messages"):
            try:
                # Set SMS text mode
                await self._send_at_command("AT+CMGF=1")
                
                # Get SMS messages
                response = await self._send_at_command("AT+CMGL=\"ALL\"")
                
                messages = []
                if "OK" in response:
                    lines = response.split('\n')
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        # Parse SMS message header
                        if line.startswith('+CMGL:'):
                            try:
                                # Extract SMS details
                                parts = line.split(',')
                                if len(parts) >= 5:
                                    message_id = int(parts[0].split(':')[1])
                                    status = parts[1].strip('"')
                                    phone_number = parts[2].strip('"')
                                    timestamp_str = f"{parts[4]} {parts[5]}"
                                    
                                    # Get message content
                                    i += 1
                                    if i < len(lines):
                                        message_content = lines[i].strip()
                                        
                                        # Parse timestamp
                                        try:
                                            timestamp = datetime.strptime(timestamp_str, "%y/%m/%d,%H:%M:%S%z")
                                        except:
                                            timestamp = datetime.now()
                                        
                                        # Create SMS message object
                                        sms_message = SmsMessage(
                                            id=message_id,
                                            modem_id=f"huawei_{self.port}" if self.port else None,
                                            status=SmsStatus(status),
                                            phone_number=phone_number,
                                            message=message_content,
                                            timestamp=timestamp
                                        )
                                        messages.append(sms_message)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse SMS message: {e}")
                        
                        i += 1
                
                self.logger.info(f"Retrieved {len(messages)} SMS messages")
                return messages
                
            except Exception as e:
                self.logger.error(f"Failed to get SMS messages: {e}")
                raise SmsReadException(f"Failed to read SMS messages: {e}")
    
    async def send_sms(self, number: str, message: str) -> bool:
        """
        Send an SMS message.
        
        Args:
            number: Phone number to send SMS to
            message: SMS message content
            
        Returns:
            True if SMS sent successfully
            
        Raises:
            SmsSendException: If SMS sending fails
        """
        with log_operation(self.logger, f"Send SMS to {number}"):
            try:
                # Check if modem is connected
                if not self.serial_connection or not self.serial_connection.is_open:
                    raise SmsSendException("Modem is not connected")
                
                self.logger.info(f"Modem connection status: {self.serial_connection.is_open}")
                self.logger.info(f"Modem port: {self.port}")
                self.logger.info(f"Modem initialized: {self.is_initialized}")
                
                # Test basic AT command first
                try:
                    test_response = await self._send_at_command("AT", timeout=5)
                    self.logger.info(f"AT test response: {test_response}")
                except Exception as e:
                    self.logger.error(f"AT test failed: {e}")
                    raise SmsSendException(f"Modem not responsive: {e}")
                
                # Check SIM status
                try:
                    cpin_response = await self._send_at_command("AT+CPIN?", timeout=5)
                    self.logger.info(f"SIM status response: {cpin_response}")
                    if "READY" not in cpin_response:
                        raise SmsSendException("SIM card not ready")
                except Exception as e:
                    self.logger.warning(f"Could not check SIM status: {e}")
                
                # Check network registration
                try:
                    creg_response = await self._send_at_command("AT+CREG?", timeout=5)
                    self.logger.info(f"Network registration response: {creg_response}")
                    if "0,1" not in creg_response and "0,5" not in creg_response:
                        self.logger.warning("Network not registered, SMS may fail")
                except Exception as e:
                    self.logger.warning(f"Could not check network registration: {e}")
                
                # Reset SMS configuration
                try:
                    await self._send_at_command("ATZ", timeout=5)  # Reset to default
                    await self._send_at_command("AT&F", timeout=5)  # Factory reset
                except Exception as e:
                    self.logger.warning(f"Could not reset modem: {e}")
                
                # Set SMS text mode
                try:
                    await self._send_at_command("AT+CMGF=1", timeout=5)
                    self.logger.info("SMS text mode set successfully")
                except Exception as e:
                    self.logger.error(f"Failed to set SMS text mode: {e}")
                    raise SmsSendException(f"Failed to set SMS text mode: {e}")
                
                # Set character set
                try:
                    await self._send_at_command("AT+CSCS=\"GSM\"", timeout=5)
                    self.logger.info("Character set set to GSM")
                except Exception as e:
                    self.logger.warning(f"Could not set character set: {e}")
                
                # Check signal strength before sending
                try:
                    csq_response = await self._send_at_command("AT+CSQ", timeout=5)
                    self.logger.info(f"Signal strength response: {csq_response}")
                    if "CSQ:" in csq_response:
                        csq_match = re.search(r'CSQ:\s*(\d+)', csq_response)
                        if csq_match:
                            signal = int(csq_match.group(1))
                            if signal == 99:  # No signal
                                raise SmsSendException("No signal available for SMS sending")
                except Exception as e:
                    self.logger.warning(f"Could not check signal strength: {e}")
                
                # Validate phone number format
                if not number.startswith('+') and not number.startswith('00'):
                    # Add country code if not present (assuming Algeria +213)
                    if number.startswith('0'):
                        number = '+213' + number[1:]
                    else:
                        number = '+213' + number
                
                self.logger.info(f"Formatted phone number: {number}")
                
                # Try alternative SMS sending methods
                success = False
                
                # Method 1: Standard AT+CMGS
                try:
                    self.logger.info("Trying Method 1: Standard AT+CMGS")
                    success = await self._send_sms_method1(number, message)
                    if success:
                        return True
                except Exception as e:
                    self.logger.warning(f"Method 1 failed: {e}")
                
                # Method 2: AT+CMGS with different format
                try:
                    self.logger.info("Trying Method 2: AT+CMGS with different format")
                    success = await self._send_sms_method2(number, message)
                    if success:
                        return True
                except Exception as e:
                    self.logger.warning(f"Method 2 failed: {e}")
                
                # Method 3: AT+CMGS with PDU mode
                try:
                    self.logger.info("Trying Method 3: PDU mode")
                    success = await self._send_sms_method3(number, message)
                    if success:
                        return True
                except Exception as e:
                    self.logger.warning(f"Method 3 failed: {e}")
                
                raise SmsSendException("All SMS sending methods failed")
                
            except Exception as e:
                self.logger.error(f"Failed to send SMS to {number}: {e}")
                raise SmsSendException(f"Failed to send SMS: {e}")
    
    async def _send_sms_method1(self, number: str, message: str) -> bool:
        """Method 1: Standard AT+CMGS with text mode."""
        sms_command = f'AT+CMGS="{number}"'
        self.logger.info(f"Sending SMS command: {sms_command}")
        response = await self._send_at_command(sms_command, timeout=15)
        self.logger.info(f"SMS command response: {response}")
        
        if ">" in response:
            # Send message content with Ctrl+Z terminator
            message_with_terminator = f"{message}\x1A"
            self.logger.info(f"Sending message content: {message[:20]}...")
            self.serial_connection.write(message_with_terminator.encode())
            
            # Wait for final response with longer timeout
            final_response = ""
            start_time = asyncio.get_event_loop().time()
            timeout = 30  # SMS sending timeout
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    final_response += line + "\n"
                    self.logger.debug(f"Received line: {line}")
                    
                    if "OK" in line:
                        self.logger.info(f"SMS sent successfully to {number}")
                        return True
                    elif "ERROR" in line or "FAIL" in line:
                        raise SmsSendException(f"SMS send failed: {line}")
                
                await asyncio.sleep(0.1)
            
            # If we get here, it timed out
            raise SmsSendException(f"SMS send timed out. Response: {final_response}")
        else:
            raise SmsSendException(f"SMS send failed: {response}")
    
    async def _send_sms_method2(self, number: str, message: str) -> bool:
        """Method 2: AT+CMGS with different number format."""
        # Try without quotes
        sms_command = f'AT+CMGS={number}'
        self.logger.info(f"Sending SMS command (Method 2): {sms_command}")
        response = await self._send_at_command(sms_command, timeout=15)
        self.logger.info(f"SMS command response: {response}")
        
        if ">" in response:
            # Send message content with Ctrl+Z terminator
            message_with_terminator = f"{message}\x1A"
            self.serial_connection.write(message_with_terminator.encode())
            
            # Wait for final response
            final_response = ""
            start_time = asyncio.get_event_loop().time()
            timeout = 30
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    final_response += line + "\n"
                    
                    if "OK" in line:
                        self.logger.info(f"SMS sent successfully to {number} (Method 2)")
                        return True
                    elif "ERROR" in line or "FAIL" in line:
                        raise SmsSendException(f"SMS send failed: {line}")
                
                await asyncio.sleep(0.1)
            
            raise SmsSendException(f"SMS send timed out. Response: {final_response}")
        else:
            raise SmsSendException(f"SMS send failed: {response}")
    
    async def _send_sms_method3(self, number: str, message: str) -> bool:
        """Method 3: PDU mode SMS sending."""
        # Set PDU mode
        await self._send_at_command("AT+CMGF=0", timeout=5)
        
        # For PDU mode, we need to encode the message properly
        # This is a simplified version - in production you'd need proper PDU encoding
        try:
            # Try to send with PDU mode
            sms_command = f'AT+CMGS={len(message)}'
            self.logger.info(f"Sending SMS command (PDU mode): {sms_command}")
            response = await self._send_at_command(sms_command, timeout=15)
            
            if ">" in response:
                # Send PDU data (simplified)
                pdu_data = "000100" + number + "0000" + message.encode('hex').upper()
                self.serial_connection.write((pdu_data + "\x1A").encode())
                
                # Wait for response
                final_response = ""
                start_time = asyncio.get_event_loop().time()
                timeout = 30
                
                while asyncio.get_event_loop().time() - start_time < timeout:
                    if self.serial_connection.in_waiting:
                        line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        final_response += line + "\n"
                        
                        if "OK" in line:
                            self.logger.info(f"SMS sent successfully to {number} (PDU mode)")
                            return True
                        elif "ERROR" in line or "FAIL" in line:
                            raise SmsSendException(f"SMS send failed: {line}")
                    
                    await asyncio.sleep(0.1)
                
                raise SmsSendException(f"SMS send timed out. Response: {final_response}")
            else:
                raise SmsSendException(f"SMS send failed: {response}")
        finally:
            # Reset to text mode
            await self._send_at_command("AT+CMGF=1", timeout=5)
    
    async def delete_sms(self, message_id: int) -> bool:
        """
        Delete an SMS message.
        
        Args:
            message_id: ID of the SMS message to delete
            
        Returns:
            True if SMS deleted successfully
            
        Raises:
            SmsDeleteException: If SMS deletion fails
        """
        with log_operation(self.logger, f"Delete SMS {message_id}"):
            try:
                # Delete specific SMS
                response = await self._send_at_command(f"AT+CMGD={message_id}")
                
                if "OK" in response:
                    self.logger.info(f"SMS {message_id} deleted successfully")
                    return True
                else:
                    raise SmsDeleteException(f"SMS deletion failed: {response}")
                
            except Exception as e:
                self.logger.error(f"Failed to delete SMS {message_id}: {e}")
                raise SmsDeleteException(f"Failed to delete SMS: {e}")
    
    async def send_ussd(self, command: str) -> UssdResponse:
        """
        Send a USSD command.
        
        Args:
            command: USSD command to send
            
        Returns:
            UssdResponse object with the response
            
        Raises:
            UssdTimeoutException: If USSD command times out
            UssdException: If USSD command fails
        """
        with log_operation(self.logger, f"Send USSD command: {command}"):
            try:
                # Check if modem is connected
                if not self.serial_connection or not self.serial_connection.is_open:
                    raise UssdException("Modem is not connected")
                
                # Test basic AT command first
                try:
                    test_response = await self._send_at_command("AT", timeout=5)
                    self.logger.info(f"AT test response: {test_response}")
                except Exception as e:
                    self.logger.error(f"AT test failed: {e}")
                    raise UssdException(f"Modem not responsive: {e}")
                
                # Check SIM status
                try:
                    cpin_response = await self._send_at_command("AT+CPIN?", timeout=5)
                    self.logger.info(f"SIM status response: {cpin_response}")
                    if "READY" not in cpin_response:
                        raise UssdException("SIM card not ready")
                except Exception as e:
                    self.logger.warning(f"Could not check SIM status: {e}")
                
                # Check network registration
                try:
                    creg_response = await self._send_at_command("AT+CREG?", timeout=5)
                    self.logger.info(f"Network registration response: {creg_response}")
                    if "0,1" not in creg_response and "0,5" not in creg_response:
                        self.logger.warning("Network not registered, USSD may fail")
                except Exception as e:
                    self.logger.warning(f"Could not check network registration: {e}")
                
                # Reset modem configuration
                try:
                    await self._send_at_command("ATZ", timeout=5)  # Reset to default
                    await self._send_at_command("AT&F", timeout=5)  # Factory reset
                except Exception as e:
                    self.logger.warning(f"Could not reset modem: {e}")
                
                # Set character set to IRA (International Reference Alphabet)
                try:
                    await self._send_at_command('AT+CSCS="IRA"', timeout=5)
                    self.logger.info("Character set set to IRA")
                except Exception as e:
                    self.logger.warning(f"Could not set character set to IRA: {e}")
                    # Try GSM as fallback
                    try:
                        await self._send_at_command('AT+CSCS="GSM"', timeout=5)
                        self.logger.info("Character set set to GSM")
                    except Exception as e2:
                        self.logger.warning(f"Could not set character set to GSM: {e2}")
                
                # Sanitize and encode USSD command
                sanitized_command = UssdEncoderDecoder.sanitize_for_ussd(command)
                self.logger.info(f"Sanitized USSD command: {sanitized_command}")
                
                # Encode command as GSM 7-bit
                encoded_command = UssdEncoderDecoder.encode_as_7bit_gsm(sanitized_command)
                self.logger.info(f"Encoded USSD command: {encoded_command}")
                
                # Try multiple USSD sending methods
                success = False
                response = None
                raw_response = None
                
                # Method 1: Standard USSD with encoded command
                try:
                    self.logger.info("Trying Method 1: Standard USSD with encoded command")
                    response, raw_response = await self._send_ussd_method1(encoded_command)
                    if response:
                        success = True
                except Exception as e:
                    self.logger.warning(f"Method 1 failed: {e}")
                
                # Method 2: USSD with hex encoding
                if not success:
                    try:
                        self.logger.info("Trying Method 2: USSD with hex encoding")
                        response, raw_response = await self._send_ussd_method2(sanitized_command)
                        if response:
                            success = True
                    except Exception as e:
                        self.logger.warning(f"Method 2 failed: {e}")
                
                # Method 3: USSD with different format
                if not success:
                    try:
                        self.logger.info("Trying Method 3: USSD with different format")
                        response, raw_response = await self._send_ussd_method3(sanitized_command)
                        if response:
                            success = True
                    except Exception as e:
                        self.logger.warning(f"Method 3 failed: {e}")
                
                if not success:
                    raise UssdException("All USSD sending methods failed")
                
                return UssdResponse(
                    command=command,
                    modem_id=f"huawei_{self.port}" if self.port else None,
                    response=response,
                    raw_response=raw_response,
                    success=True
                )
                
            except Exception as e:
                self.logger.error(f"Failed to send USSD command {command}: {e}")
                raise UssdException(f"Failed to send USSD command: {e}")
    
    async def _send_ussd_method1(self, encoded_command: str) -> Tuple[str, str]:
        """Method 1: Standard USSD with encoded command."""
        ussd_command = f'AT+CUSD=1,"{encoded_command}",15'
        self.logger.info(f"Sending USSD command: {ussd_command}")
        response = await self._send_at_command(ussd_command, timeout=30)
        self.logger.info(f"USSD command response: {response}")
        
        # Parse USSD response
        ussd_response = ""
        raw_response = response
        
        # Look for USSD response in the output
        lines = response.split('\n')
        for line in lines:
            if "+CUSD:" in line:
                # Extract USSD response
                ussd_match = re.search(r'\+CUSD:\s*\d+,"([^"]*)"', line)
                if ussd_match:
                    ussd_response = ussd_match.group(1)
                    break
            elif "ERROR" in line:
                raise UssdException(f"USSD command failed: {line}")
        
        if not ussd_response:
            raise UssdException(f"USSD command failed: {response}")
        
        return ussd_response, raw_response
    
    async def _send_ussd_method2(self, command: str) -> Tuple[str, str]:
        """Method 2: USSD with hex encoding."""
        # Convert command to hex
        hex_command = UssdEncoderDecoder.encode_as_hex_7bit_gsm(command)
        ussd_command = f'AT+CUSD=1,"{hex_command}",15'
        self.logger.info(f"Sending USSD command (hex): {ussd_command}")
        response = await self._send_at_command(ussd_command, timeout=30)
        self.logger.info(f"USSD command response: {response}")
        
        # Parse USSD response
        ussd_response = ""
        raw_response = response
        
        # Look for USSD response in the output
        lines = response.split('\n')
        for line in lines:
            if "+CUSD:" in line:
                # Extract USSD response
                ussd_match = re.search(r'\+CUSD:\s*\d+,"([^"]*)"', line)
                if ussd_match:
                    ussd_response = ussd_match.group(1)
                    break
            elif "ERROR" in line:
                raise UssdException(f"USSD command failed: {line}")
        
        if not ussd_response:
            raise UssdException(f"USSD command failed: {response}")
        
        return ussd_response, raw_response
    
    async def _send_ussd_method3(self, command: str) -> Tuple[str, str]:
        """Method 3: USSD with different format."""
        # Try without quotes
        ussd_command = f'AT+CUSD=1,{command},15'
        self.logger.info(f"Sending USSD command (no quotes): {ussd_command}")
        response = await self._send_at_command(ussd_command, timeout=30)
        self.logger.info(f"USSD command response: {response}")
        
        # Parse USSD response
        ussd_response = ""
        raw_response = response
        
        # Look for USSD response in the output
        lines = response.split('\n')
        for line in lines:
            if "+CUSD:" in line:
                # Extract USSD response
                ussd_match = re.search(r'\+CUSD:\s*\d+,"([^"]*)"', line)
                if ussd_match:
                    ussd_response = ussd_match.group(1)
                    break
            elif "ERROR" in line:
                raise UssdException(f"USSD command failed: {line}")
        
        if not ussd_response:
            raise UssdException(f"USSD command failed: {response}")
        
        return ussd_response, raw_response
    
    async def get_balance(self) -> UssdResponse:
        """
        Get account balance using USSD.
        
        Returns:
            UssdResponse object with balance information
            
        Raises:
            UssdException: If balance check fails
        """
        with log_operation(self.logger, "Get account balance"):
            try:
                # Try common balance USSD codes
                balance_codes = ["*223#", "*100#", "*101#", "*102#"]
                
                for code in balance_codes:
                    try:
                        response = await self.send_ussd(code)
                        if response.response and "balance" in response.response.lower():
                            return response
                    except Exception as e:
                        self.logger.debug(f"Balance code {code} failed: {e}")
                        continue
                
                # If no specific balance code works, try the first one
                return await self.send_ussd(balance_codes[0])
                
            except Exception as e:
                self.logger.error(f"Failed to get balance: {e}")
                raise UssdException(f"Failed to get account balance: {e}")
    
    def close(self):
        """Close the modem connection."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.logger.info(f"Closed connection to {self.port}")
        
        self.is_initialized = False
        self.serial_connection = None
