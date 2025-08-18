"""
Unit tests for ModemManager
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import serial

from core.modem_manager import ModemManager
from core.exceptions import ModemDetectionException, ModemNotConnectedException, ATCommandException
from models.models import ModemStatus, SimInfo, NetworkType

class TestModemManager:
    
    @pytest.fixture
    def modem_manager(self):
        """Create ModemManager instance for testing"""
        return ModemManager()
    
    @pytest.fixture
    def mock_serial(self):
        """Mock serial connection"""
        mock = Mock()
        mock.is_open = True
        mock.in_waiting = 0
        mock.flushInput = Mock()
        mock.flushOutput = Mock()
        mock.write = Mock()
        mock.read_all = Mock(return_value=b'OK\r\n')
        return mock
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, modem_manager):
        """Test successful modem initialization"""
        with patch.object(modem_manager, '_detect_huawei_modem', return_value='COM3'), \
             patch.object(modem_manager, '_connect_to_modem', return_value=None), \
             patch.object(modem_manager, '_configure_modem', return_value=None):
            
            await modem_manager.initialize()
            assert modem_manager.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialization_no_modem(self, modem_manager):
        """Test initialization when no modem is detected"""
        with patch.object(modem_manager, '_detect_huawei_modem', return_value=None):
            with pytest.raises(ModemDetectionException):
                await modem_manager.initialize()
    
    @pytest.mark.asyncio
    async def test_detect_huawei_modem_by_vid_pid(self, modem_manager):
        """Test modem detection by VID/PID"""
        mock_port = Mock()
        mock_port.device = 'COM3'
        mock_port.vid = 0x12D1
        mock_port.pid = 0x1F01
        mock_port.description = 'Huawei Mobile Connect'
        
        with patch('serial.tools.list_ports.comports', return_value=[mock_port]), \
             patch.object(modem_manager, '_test_at_commands', return_value=True):
            
            port = await modem_manager._detect_huawei_modem()
            assert port == 'COM3'
    
    @pytest.mark.asyncio
    async def test_detect_huawei_modem_by_description(self, modem_manager):
        """Test modem detection by description"""
        mock_port = Mock()
        mock_port.device = 'COM3'
        mock_port.vid = None
        mock_port.pid = None
        mock_port.description = 'Huawei Mobile Connect'
        
        with patch('serial.tools.list_ports.comports', return_value=[mock_port]), \
             patch.object(modem_manager, '_test_at_commands', return_value=True):
            
            port = await modem_manager._detect_huawei_modem()
            assert port == 'COM3'
    
    @pytest.mark.asyncio
    async def test_test_at_commands_success(self, modem_manager):
        """Test successful AT command testing"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial = Mock()
            mock_serial.read_all.return_value = b'AT\r\nOK\r\n'
            mock_serial_class.return_value = mock_serial
            
            result = await modem_manager._test_at_commands('COM3')
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_at_commands_failure(self, modem_manager):
        """Test failed AT command testing"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial = Mock()
            mock_serial.read_all.return_value = b'ERROR\r\n'
            mock_serial_class.return_value = mock_serial
            
            result = await modem_manager._test_at_commands('COM3')
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_at_command_success(self, modem_manager, mock_serial):
        """Test successful AT command sending"""
        modem_manager.serial_connection = mock_serial
        mock_serial.in_waiting = 1
        mock_serial.read_all.return_value = b'AT+CIMI\r\n60302123456789\r\nOK\r\n'
        
        response = await modem_manager._send_at_command('AT+CIMI')
        assert 'OK' in response
        assert '60302123456789' in response
    
    @pytest.mark.asyncio
    async def test_send_at_command_not_connected(self, modem_manager):
        """Test AT command when modem not connected"""
        modem_manager.serial_connection = None
        
        with pytest.raises(ModemNotConnectedException):
            await modem_manager._send_at_command('AT+CIMI')
    
    @pytest.mark.asyncio
    async def test_send_at_command_error_response(self, modem_manager, mock_serial):
        """Test AT command with error response"""
        modem_manager.serial_connection = mock_serial
        mock_serial.read_all.return_value = b'AT+CIMI\r\nERROR\r\n'
        
        with pytest.raises(ATCommandException):
            await modem_manager._send_at_command('AT+CIMI')
    
    @pytest.mark.asyncio
    async def test_get_status_connected(self, modem_manager, mock_serial):
        """Test getting status when connected"""
        modem_manager.serial_connection = mock_serial
        modem_manager.port = 'COM3'
        
        # Mock responses for different commands
        responses = {
            'AT+GMM': b'E3531s\r\nOK\r\n',
            'AT+GMR': b'1.0.0\r\nOK\r\n',
            'AT+CSQ': b'+CSQ: 20,99\r\nOK\r\n',
            'AT+COPS?': b'+COPS: 0,0,"Ooredoo Algeria"\r\nOK\r\n'
        }
        
        async def mock_send_at_command(cmd):
            return responses.get(cmd, b'OK\r\n').decode()
        
        with patch.object(modem_manager, '_send_at_command', side_effect=mock_send_at_command), \
             patch.object(modem_manager, '_get_network_type', return_value=NetworkType.LTE):
            
            status = await modem_manager.get_status()
            assert status.connected is True
            assert status.port == 'COM3'
            assert status.model == 'E3531s'
            assert status.firmware == '1.0.0'
    
    @pytest.mark.asyncio
    async def test_get_status_not_connected(self, modem_manager):
        """Test getting status when not connected"""
        modem_manager.serial_connection = None
        
        status = await modem_manager.get_status()
        assert status.connected is False
        assert status.error == "Modem not connected"
    
    @pytest.mark.asyncio
    async def test_get_sim_info(self, modem_manager, mock_serial):
        """Test getting SIM information"""
        modem_manager.serial_connection = mock_serial
        
        responses = {
            'AT+CIMI': b'60302123456789\r\nOK\r\n',
            'AT+CCID': b'8921302123456789012\r\nOK\r\n',
            'AT+CGSN': b'123456789012345\r\nOK\r\n',
            'AT+CNUM': b'+CNUM: "","0555123456",129\r\nOK\r\n',
            'AT+CSQ': b'+CSQ: 20,99\r\nOK\r\n',
            'AT+COPS?': b'+COPS: 0,0,"Ooredoo Algeria"\r\nOK\r\n'
        }
        
        async def mock_send_at_command(cmd):
            return responses.get(cmd, b'OK\r\n').decode()
        
        with patch.object(modem_manager, '_send_at_command', side_effect=mock_send_at_command), \
             patch.object(modem_manager, '_get_network_type', return_value=NetworkType.LTE):
            
            sim_info = await modem_manager.get_sim_info()
            assert sim_info.imsi == '60302123456789'
            assert sim_info.iccid == '8921302123456789012'
            assert sim_info.imei == '123456789012345'
            assert sim_info.msisdn == '0555123456'
    
    def test_is_connected_true(self, modem_manager, mock_serial):
        """Test is_connected when connected"""
        modem_manager.serial_connection = mock_serial
        assert modem_manager.is_connected() is True
    
    def test_is_connected_false(self, modem_manager):
        """Test is_connected when not connected"""
        modem_manager.serial_connection = None
        assert modem_manager.is_connected() is False
    
    def test_parse_signal_strength(self, modem_manager):
        """Test signal strength parsing"""
        response = '+CSQ: 20,99\r\nOK'
        strength = modem_manager._parse_signal_strength(response)
        # CSQ 20 should convert to approximately 64% (20 * 100 / 31)
        assert strength == 64
    
    def test_parse_signal_strength_invalid(self, modem_manager):
        """Test signal strength parsing with invalid value"""
        response = '+CSQ: 99,99\r\nOK'
        strength = modem_manager._parse_signal_strength(response)
        assert strength is None
    
    def test_parse_operator(self, modem_manager):
        """Test operator name parsing"""
        response = '+COPS: 0,0,"Ooredoo Algeria"\r\nOK'
        operator = modem_manager._parse_operator(response)
        assert operator == "Ooredoo Algeria"
    
    def test_parse_msisdn(self, modem_manager):
        """Test MSISDN parsing"""
        response = '+CNUM: "","0555123456",129\r\nOK'
        msisdn = modem_manager._parse_msisdn(response)
        assert msisdn == "0555123456"
