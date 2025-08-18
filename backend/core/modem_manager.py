import serial
import serial.tools.list_ports
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import traceback

from models.models import ModemStatus, SimInfo, SmsMessage, NetworkType, SmsStatus, ATCommand
from core.exceptions import (
    ModemNotConnectedException, 
    ModemDetectionException, 
    ATCommandException,
    SmsException,
    UssdException,
    SerialPortException,
    SimCardException
)
from core.logger import get_modem_logger

logger = get_modem_logger()

class ModemManager:
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self.is_initialized = False
        self.last_sim_info: Optional[SimInfo] = None
        self.sim_change_callbacks: List[callable] = []
        
    async def initialize(self):
        """Initialize modem connection by detecting and connecting to Huawei modem"""
        try:
            logger.info("Starting modem initialization...")
            port = await self._detect_huawei_modem()
            if not port:
                error_msg = "No Huawei modem detected. Please check USB connection and drivers."
                logger.error(error_msg)
                raise ModemDetectionException(error_msg)
            
            await self._connect_to_modem(port)
            await self._configure_modem()
            self.is_initialized = True
            logger.info(f"Modem initialized successfully on port {self.port}")
            
        except ModemDetectionException:
            raise
        except Exception as e:
            error_msg = f"Failed to initialize modem: {str(e)}"
            logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
            raise ModemDetectionException(error_msg) from e
    
    async def _detect_huawei_modem(self) -> Optional[str]:
        """Detect Huawei modem and return the correct serial port"""
        ports = serial.tools.list_ports.comports()
        
        # Known Huawei VID/PID combinations
        huawei_identifiers = [
            (0x12D1, 0x1F01),  # E3531s
            (0x12D1, 0x14DB),  # E3531 variants
            (0x12D1, 0x1506),  # E398
            (0x12D1, 0x140C),  # E173
            (0x12D1, 0x1001),  # Generic Huawei
            (0x12D1, 0x1003),  # Generic Huawei
        ]
        
        for port in ports:
            logger.info(f"Checking port: {port.device} - {port.description}")
            
            # Check by VID/PID
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                for vid, pid in huawei_identifiers:
                    if port.vid == vid and port.pid == pid:
                        # For multi-port modems, prefer the AT command port
                        if await self._test_at_commands(port.device):
                            logger.info(f"Found Huawei modem on {port.device}")
                            return port.device
            
            # Check by description/manufacturer
            description = port.description.lower()
            if any(keyword in description for keyword in ['huawei', 'e3531', 'mobile connect']):
                if await self._test_at_commands(port.device):
                    logger.info(f"Found Huawei modem on {port.device}")
                    return port.device
        
        # Fallback: test all COM ports for AT command response
        for port in ports:
            if await self._test_at_commands(port.device):
                logger.info(f"Found AT command capable device on {port.device}")
                return port.device
        
        return None
    
    async def _test_at_commands(self, port: str) -> bool:
        """Test if a port responds to AT commands"""
        try:
            test_serial = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Clear any existing data
            test_serial.flushInput()
            test_serial.flushOutput()
            
            # Send AT command
            test_serial.write(b'AT\r\n')
            time.sleep(0.5)
            
            response = test_serial.read_all().decode('utf-8', errors='ignore')
            test_serial.close()
            
            return 'OK' in response
            
        except Exception as e:
            logger.debug(f"Failed to test AT commands on {port}: {e}")
            return False
    
    async def _connect_to_modem(self, port: str):
        """Connect to the modem on specified port"""
        try:
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=5,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.port = port
            
            # Clear buffers
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            logger.info(f"Connected to modem on port {port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to modem on {port}: {e}")
            raise
    
    async def _configure_modem(self):
        """Configure modem settings"""
        try:
            # Basic configuration commands
            config_commands = [
                "ATE0",  # Disable echo
                "AT+CMEE=1",  # Enable error reporting
                "AT+CMGF=1",  # Set SMS text mode
                "AT+CSCS=\"GSM\"",  # Set character set
                "AT+CNMI=1,1,0,0,0",  # Configure SMS notifications
            ]
            
            for cmd in config_commands:
                response = await self._send_at_command(cmd)
                if "OK" not in response:
                    logger.warning(f"Command {cmd} failed: {response}")
                    
        except Exception as e:
            logger.error(f"Failed to configure modem: {e}")
            raise
    
    async def _send_at_command(self, command: str, timeout: int = 5) -> str:
        """Send AT command and return response"""
        if not self.serial_connection:
            raise ModemNotConnectedException("Modem not connected")
        
        try:
            logger.debug(f"Sending AT command: {command}")
            
            # Clear input buffer
            self.serial_connection.flushInput()
            
            # Send command
            cmd = f"{command}\r\n"
            self.serial_connection.write(cmd.encode())
            
            # Read response
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting:
                    data = self.serial_connection.read_all().decode('utf-8', errors='ignore')
                    response += data
                    
                    if 'OK' in response or 'ERROR' in response:
                        break
                
                await asyncio.sleep(0.1)
            
            if not response:
                error_msg = f"No response received for command: {command}"
                logger.error(error_msg)
                raise ATCommandException(error_msg)
            
            if 'ERROR' in response:
                error_msg = f"AT command failed: {command} -> {response.strip()}"
                logger.error(error_msg)
                raise ATCommandException(error_msg)
            
            logger.debug(f"Command: {command} -> Response: {response.strip()}")
            return response.strip()
            
        except (ModemNotConnectedException, ATCommandException):
            raise
        except Exception as e:
            error_msg = f"Failed to send AT command {command}: {str(e)}"
            logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
            raise ATCommandException(error_msg) from e
    
    def is_connected(self) -> bool:
        """Check if modem is connected"""
        return self.serial_connection is not None and self.serial_connection.is_open
    
    async def get_status(self) -> ModemStatus:
        """Get current modem status"""
        try:
            if not self.is_connected():
                return ModemStatus(connected=False, error="Modem not connected")
            
            # Get basic modem info
            model_response = await self._send_at_command("AT+GMM")
            firmware_response = await self._send_at_command("AT+GMR")
            signal_response = await self._send_at_command("AT+CSQ")
            network_response = await self._send_at_command("AT+COPS?")
            
            # Parse responses
            model = self._extract_value(model_response, "AT+GMM")
            firmware = self._extract_value(firmware_response, "AT+GMR")
            signal_strength = self._parse_signal_strength(signal_response)
            operator = self._parse_operator(network_response)
            network_type = await self._get_network_type()
            
            return ModemStatus(
                connected=True,
                port=self.port,
                model=model,
                firmware=firmware,
                signal_strength=signal_strength,
                network_type=network_type,
                operator=operator
            )
            
        except Exception as e:
            logger.error(f"Error getting modem status: {e}")
            return ModemStatus(connected=False, error=str(e))
    
    async def get_sim_info(self) -> SimInfo:
        """Get comprehensive SIM card information"""
        try:
            if not self.is_connected():
                raise Exception("Modem not connected")
            
            # Get SIM information with error handling for each command
            imsi = None
            iccid = None
            imei = None
            msisdn = None
            signal_strength = None
            network_operator = None
            network_type = None
            
            try:
                imsi_response = await self._send_at_command("AT+CIMI")
                imsi = self._extract_value(imsi_response, "AT+CIMI")
            except Exception as e:
                logger.warning(f"Failed to get IMSI: {e}")
            
            try:
                iccid_response = await self._send_at_command("AT+CCID")
                iccid = self._extract_value(iccid_response, "AT+CCID")
            except Exception as e:
                logger.warning(f"Failed to get ICCID: {e}")
            
            try:
                imei_response = await self._send_at_command("AT+CGSN")
                imei = self._extract_value(imei_response, "AT+CGSN")
            except Exception as e:
                logger.warning(f"Failed to get IMEI: {e}")
            
            try:
                msisdn_response = await self._send_at_command("AT+CNUM")
                msisdn = self._parse_msisdn(msisdn_response)
            except Exception as e:
                logger.warning(f"Failed to get MSISDN (phone number): {e}")
                # This is common and not critical, many SIM cards don't store phone number
            
            try:
                signal_response = await self._send_at_command("AT+CSQ")
                signal_strength = self._parse_signal_strength(signal_response)
            except Exception as e:
                logger.warning(f"Failed to get signal strength: {e}")
            
            try:
                network_response = await self._send_at_command("AT+COPS?")
                network_operator = self._parse_operator(network_response)
            except Exception as e:
                logger.warning(f"Failed to get network operator: {e}")
            
            try:
                network_type = await self._get_network_type()
            except Exception as e:
                logger.warning(f"Failed to get network type: {e}")
            
            sim_info = SimInfo(
                imsi=imsi,
                iccid=iccid,
                imei=imei,
                msisdn=msisdn,
                signal_strength=signal_strength,
                network_type=network_type,
                network_operator=network_operator
            )
            
            # Check if SIM card has changed
            await self._check_sim_change(sim_info)
            
            return sim_info
            
        except Exception as e:
            logger.error(f"Error getting SIM info: {e}")
            raise
    
    async def _check_sim_change(self, current_sim_info: SimInfo):
        """Check if SIM card has changed and notify callbacks"""
        try:
            if self.last_sim_info is None:
                # First time getting SIM info
                self.last_sim_info = current_sim_info
                if current_sim_info.imsi:
                    logger.info(f"SIM card detected - IMSI: {current_sim_info.imsi[:6]}***")
                return
            
            # Check if IMSI or ICCID changed (indicating new SIM)
            sim_changed = False
            if (current_sim_info.imsi != self.last_sim_info.imsi or 
                current_sim_info.iccid != self.last_sim_info.iccid):
                sim_changed = True
            
            if sim_changed:
                logger.info("SIM card change detected!")
                if current_sim_info.imsi:
                    logger.info(f"New SIM - IMSI: {current_sim_info.imsi[:6]}***")
                
                # Call registered callbacks
                for callback in self.sim_change_callbacks:
                    try:
                        await callback(current_sim_info)
                    except Exception as e:
                        logger.error(f"Error calling SIM change callback: {e}")
                
                self.last_sim_info = current_sim_info
                
        except Exception as e:
            logger.error(f"Error checking SIM change: {e}")
    
    def register_sim_change_callback(self, callback):
        """Register a callback to be called when SIM changes"""
        self.sim_change_callbacks.append(callback)
    
    async def get_sms_messages(self) -> List[SmsMessage]:
        """Get all SMS messages"""
        try:
            if not self.is_connected():
                raise Exception("Modem not connected")
            
            messages = []
            
            # Try different SMS list commands to get all messages
            try:
                # Get all messages
                response = await self._send_at_command("AT+CMGL=\"ALL\"", timeout=10)
                messages.extend(self._parse_sms_messages(response))
            except Exception as e:
                logger.warning(f"Failed to get ALL messages: {e}")
                
                # Try getting specific message types if ALL fails
                try:
                    # Get unread messages
                    response = await self._send_at_command("AT+CMGL=\"REC UNREAD\"", timeout=10)
                    messages.extend(self._parse_sms_messages(response))
                    
                    # Get read messages
                    response = await self._send_at_command("AT+CMGL=\"REC READ\"", timeout=10)
                    messages.extend(self._parse_sms_messages(response))
                    
                    # Get sent messages
                    response = await self._send_at_command("AT+CMGL=\"STO SENT\"", timeout=10)
                    messages.extend(self._parse_sms_messages(response))
                    
                except Exception as e2:
                    logger.warning(f"Failed to get specific message types: {e2}")
            
            logger.info(f"Retrieved {len(messages)} SMS messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting SMS messages: {e}")
            raise
    
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS message"""
        try:
            if not self.is_connected():
                raise Exception("Modem not connected")
            
            # Set SMS destination
            cmd = f"AT+CMGS=\"{phone_number}\""
            response = await self._send_at_command(cmd)
            
            if ">" not in response:
                raise Exception("Failed to enter SMS compose mode")
            
            # Send message content followed by Ctrl+Z
            message_cmd = f"{message}\x1A"
            self.serial_connection.write(message_cmd.encode())
            
            # Wait for response
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < 30:  # SMS can take longer
                if self.serial_connection.in_waiting:
                    data = self.serial_connection.read_all().decode('utf-8', errors='ignore')
                    response += data
                    
                    if '+CMGS:' in response or 'ERROR' in response:
                        break
                
                await asyncio.sleep(0.1)
            
            success = '+CMGS:' in response
            logger.info(f"SMS send result: {success} - {response}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            raise
    
    async def delete_sms(self, message_id: int) -> bool:
        """Delete SMS message"""
        try:
            if not self.is_connected():
                raise Exception("Modem not connected")
            
            response = await self._send_at_command(f"AT+CMGD={message_id}")
            success = "OK" in response
            
            logger.info(f"SMS delete result: {success} - {response}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting SMS: {e}")
            raise
    
    async def send_ussd(self, command: str) -> str:
        """Send USSD command"""
        try:
            if not self.is_connected():
                raise Exception("Modem not connected")
            
            logger.info(f"Sending USSD command: {command}")
            
            # Try different USSD command formats
            ussd_commands = [
                f"AT+CUSD=1,\"{command}\",15",
                f"AT+CUSD=1,\"{command}\"",
                f"AT+CUSD=1,{command},15"
            ]
            
            for cmd in ussd_commands:
                try:
                    response = await self._send_at_command(cmd, timeout=30)
                    parsed_response = self._parse_ussd_response(response)
                    logger.info(f"USSD command successful: {parsed_response}")
                    return parsed_response
                except ATCommandException as e:
                    logger.warning(f"USSD command format failed ({cmd}): {e}")
                    continue
            
            # If all formats failed, try a simpler approach
            try:
                # Enable USSD result codes
                await self._send_at_command("AT+CUSD=1", timeout=5)
                # Send the USSD code directly
                response = await self._send_at_command(f"AT+CUSD=1,\"{command}\"", timeout=30)
                return self._parse_ussd_response(response)
            except Exception as e:
                logger.error(f"All USSD command formats failed: {e}")
                raise UssdException(f"USSD command failed: {command}. Error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error sending USSD: {e}")
            raise
    
    def _extract_value(self, response: str, command: str) -> Optional[str]:
        """Extract value from AT command response"""
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and line != command and 'OK' not in line and 'ERROR' not in line:
                return line
        return None
    
    def _parse_signal_strength(self, response: str) -> Optional[int]:
        """Parse signal strength from CSQ response"""
        match = re.search(r'\+CSQ:\s*(\d+),', response)
        if match:
            csq = int(match.group(1))
            if csq == 99:
                return None
            # Convert CSQ to percentage (approximate)
            return min(100, (csq * 100) // 31)
        return None
    
    def _parse_operator(self, response: str) -> Optional[str]:
        """Parse operator name from COPS response"""
        match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]+)"', response)
        if match:
            return match.group(1)
        return None
    
    def _parse_msisdn(self, response: str) -> Optional[str]:
        """Parse phone number from CNUM response"""
        match = re.search(r'\+CNUM:\s*"[^"]*","(\+?\d+)"', response)
        if match:
            return match.group(1)
        return None
    
    async def _get_network_type(self) -> NetworkType:
        """Get current network type"""
        try:
            response = await self._send_at_command("AT+COPS?")
            if "LTE" in response or "4G" in response:
                return NetworkType.LTE
            elif "UMTS" in response or "3G" in response:
                return NetworkType.UMTS
            elif "GSM" in response or "2G" in response:
                return NetworkType.GSM
            else:
                return NetworkType.UNKNOWN
        except:
            return NetworkType.UNKNOWN
    
    def _parse_sms_messages(self, response: str) -> List[SmsMessage]:
        """Parse SMS messages from CMGL response"""
        messages = []
        lines = response.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('+CMGL:'):
                try:
                    # Parse SMS header
                    parts = line.split(',')
                    message_id = int(parts[0].split(':')[1].strip())
                    status = parts[1].strip('"')
                    phone_number = parts[2].strip('"')
                    timestamp_str = parts[4].strip('"') + ',' + parts[5].strip('"')
                    
                    # Get message content from next line
                    i += 1
                    if i < len(lines):
                        message_content = lines[i].strip()
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, '"%y/%m/%d,%H:%M:%S+%z"')
                        except:
                            timestamp = datetime.now()
                        
                        messages.append(SmsMessage(
                            id=message_id,
                            status=SmsStatus(status),
                            phone_number=phone_number,
                            message=message_content,
                            timestamp=timestamp
                        ))
                except Exception as e:
                    logger.warning(f"Failed to parse SMS line: {line} - {e}")
            
            i += 1
        
        return messages
    
    def _parse_ussd_response(self, response: str) -> str:
        """Parse USSD response"""
        match = re.search(r'\+CUSD:\s*\d+,"([^"]+)"', response)
        if match:
            return match.group(1)
        return response
