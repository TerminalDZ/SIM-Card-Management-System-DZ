"""
Unit tests for API endpoints
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from main import app, modem_manager, operator_manager
from models.models import ModemStatus, SimInfo, SmsMessage
from core.exceptions import ModemNotConnectedException, SmsException

class TestAPI:
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    def test_get_status_connected(self, client):
        """Test GET /api/status when modem is connected"""
        mock_status = ModemStatus(
            connected=True,
            port="COM3",
            model="E3531s",
            firmware="1.0.0",
            signal_strength=75,
            network_type="LTE",
            operator="Ooredoo Algeria"
        )
        
        with patch.object(modem_manager, 'get_status', return_value=mock_status):
            response = client.get("/api/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is True
            assert data["port"] == "COM3"
            assert data["model"] == "E3531s"
    
    def test_get_status_not_connected(self, client):
        """Test GET /api/status when modem is not connected"""
        with patch.object(modem_manager, 'get_status', 
                         side_effect=ModemNotConnectedException("Modem not connected")):
            response = client.get("/api/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is False
            assert "not connected" in data["error"].lower()
    
    def test_get_sim_info_success(self, client):
        """Test GET /api/sim-info success"""
        mock_sim_info = SimInfo(
            imsi="60302123456789",
            iccid="8921302123456789012",
            imei="123456789012345",
            msisdn="0555123456",
            signal_strength=75,
            network_type="LTE",
            network_operator="Ooredoo Algeria"
        )
        
        mock_operator_info = {
            "name": "Ooredoo Algeria",
            "balance_ussd": "*223#",
            "data_balance_ussd": "*223*2#"
        }
        
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'get_sim_info', return_value=mock_sim_info), \
             patch.object(operator_manager, 'detect_operator', return_value=mock_operator_info):
            
            response = client.get("/api/sim-info")
            
            assert response.status_code == 200
            data = response.json()
            assert data["imsi"] == "60302123456789"
            assert data["operator"]["name"] == "Ooredoo Algeria"
    
    def test_get_sim_info_not_connected(self, client):
        """Test GET /api/sim-info when modem not connected"""
        with patch.object(modem_manager, 'is_connected', return_value=False):
            response = client.get("/api/sim-info")
            
            assert response.status_code == 400
            assert "not connected" in response.json()["detail"].lower()
    
    def test_get_sms_success(self, client):
        """Test GET /api/sms success"""
        mock_messages = [
            SmsMessage(
                id=1,
                status="REC UNREAD",
                phone_number="0555123456",
                message="Test message",
                timestamp="2024-01-01T12:00:00"
            )
        ]
        
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'get_sms_messages', return_value=mock_messages):
            
            response = client.get("/api/sms")
            
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert len(data["messages"]) == 1
            assert data["messages"][0]["phone_number"] == "0555123456"
    
    def test_send_sms_success(self, client):
        """Test POST /api/sms/send success"""
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'send_sms', return_value=True):
            
            response = client.post("/api/sms/send", params={
                "phone_number": "0555123456",
                "message": "Test message"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_send_sms_not_connected(self, client):
        """Test POST /api/sms/send when modem not connected"""
        with patch.object(modem_manager, 'is_connected', return_value=False):
            response = client.post("/api/sms/send", params={
                "phone_number": "0555123456",
                "message": "Test message"
            })
            
            assert response.status_code == 400
            assert "not connected" in response.json()["detail"].lower()
    
    def test_delete_sms_success(self, client):
        """Test DELETE /api/sms/{message_id} success"""
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'delete_sms', return_value=True):
            
            response = client.delete("/api/sms/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_send_ussd_success(self, client):
        """Test POST /api/ussd success"""
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'send_ussd', return_value="Your balance is 100 DZD"):
            
            response = client.post("/api/ussd", json={"command": "*223#"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "balance" in data["response"].lower()
    
    def test_get_balance_success(self, client):
        """Test GET /api/balance success"""
        mock_sim_info = SimInfo(
            imsi="60302123456789",
            iccid="8921302123456789012"
        )
        
        mock_operator_info = {
            "name": "Ooredoo Algeria",
            "balance_ussd": "*223#"
        }
        
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'get_sim_info', return_value=mock_sim_info), \
             patch.object(operator_manager, 'detect_operator', return_value=mock_operator_info), \
             patch.object(modem_manager, 'send_ussd', return_value="Your balance is 100 DZD"):
            
            response = client.get("/api/balance")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["operator"] == "Ooredoo Algeria"
            assert data["ussd_command"] == "*223#"
    
    def test_get_balance_unsupported_operator(self, client):
        """Test GET /api/balance with unsupported operator"""
        mock_sim_info = SimInfo(
            imsi="99999123456789",  # Unknown operator
            iccid="8999999123456789012"
        )
        
        with patch.object(modem_manager, 'is_connected', return_value=True), \
             patch.object(modem_manager, 'get_sim_info', return_value=mock_sim_info), \
             patch.object(operator_manager, 'detect_operator', return_value=None):
            
            response = client.get("/api/balance")
            
            assert response.status_code == 400
            assert "not supported" in response.json()["detail"].lower()
    
    def test_get_operators(self, client):
        """Test GET /api/operators"""
        mock_operators = [
            {
                "name": "Ooredoo Algeria",
                "country": "Algeria",
                "balance_ussd": "*223#"
            },
            {
                "name": "Djezzy",
                "country": "Algeria",
                "balance_ussd": "*100#"
            }
        ]
        
        with patch.object(operator_manager, 'get_all_operators', return_value=mock_operators):
            response = client.get("/api/operators")
            
            assert response.status_code == 200
            data = response.json()
            assert "operators" in data
            assert len(data["operators"]) == 2
    
    def test_api_error_handling(self, client):
        """Test API error handling"""
        with patch.object(modem_manager, 'get_status', side_effect=Exception("Internal error")):
            response = client.get("/api/status")
            
            assert response.status_code == 500
            assert "Failed to get status" in response.json()["detail"]
