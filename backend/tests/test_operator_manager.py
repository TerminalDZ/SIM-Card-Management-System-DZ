"""
Unit tests for OperatorManager
"""

import pytest
from core.operator_manager import OperatorManager
from models.models import OperatorProfile

class TestOperatorManager:
    
    @pytest.fixture
    def operator_manager(self):
        """Create OperatorManager instance for testing"""
        return OperatorManager()
    
    def test_detect_operator_ooredoo_by_imsi(self, operator_manager):
        """Test Ooredoo detection by IMSI"""
        imsi = "60302123456789"
        operator = operator_manager.detect_operator(imsi, None)
        
        assert operator is not None
        assert operator["name"] == "Ooredoo Algeria"
        assert operator["balance_ussd"] == "*223#"
    
    def test_detect_operator_djezzy_by_imsi(self, operator_manager):
        """Test Djezzy detection by IMSI"""
        imsi = "60301987654321"
        operator = operator_manager.detect_operator(imsi, None)
        
        assert operator is not None
        assert operator["name"] == "Djezzy"
        assert operator["balance_ussd"] == "*100#"
    
    def test_detect_operator_mobilis_by_imsi(self, operator_manager):
        """Test Mobilis detection by IMSI"""
        imsi = "60300111222333"
        operator = operator_manager.detect_operator(imsi, None)
        
        assert operator is not None
        assert operator["name"] == "Mobilis"
        assert operator["balance_ussd"] == "*100#"
    
    def test_detect_operator_ooredoo_by_iccid(self, operator_manager):
        """Test Ooredoo detection by ICCID"""
        iccid = "8921302123456789012"
        operator = operator_manager.detect_operator(None, iccid)
        
        assert operator is not None
        assert operator["name"] == "Ooredoo Algeria"
    
    def test_detect_operator_djezzy_by_iccid(self, operator_manager):
        """Test Djezzy detection by ICCID"""
        iccid = "8921301987654321012"
        operator = operator_manager.detect_operator(None, iccid)
        
        assert operator is not None
        assert operator["name"] == "Djezzy"
    
    def test_detect_operator_mobilis_by_iccid(self, operator_manager):
        """Test Mobilis detection by ICCID"""
        iccid = "8921300111222333012"
        operator = operator_manager.detect_operator(None, iccid)
        
        assert operator is not None
        assert operator["name"] == "Mobilis"
    
    def test_detect_operator_by_mcc_mnc(self, operator_manager):
        """Test operator detection by MCC/MNC from IMSI"""
        # IMSI with MCC 603 and MNC 02 (Ooredoo)
        imsi = "60302999999999"  # Different from standard prefix
        operator = operator_manager.detect_operator(imsi, None)
        
        assert operator is not None
        assert operator["name"] == "Ooredoo Algeria"
    
    def test_detect_operator_unknown(self, operator_manager):
        """Test detection with unknown operator"""
        imsi = "99999123456789"  # Unknown MCC
        iccid = "8999999123456789012"  # Unknown prefix
        
        operator = operator_manager.detect_operator(imsi, iccid)
        assert operator is None
    
    def test_detect_operator_no_info(self, operator_manager):
        """Test detection with no IMSI or ICCID"""
        operator = operator_manager.detect_operator(None, None)
        assert operator is None
    
    def test_get_operator_by_name(self, operator_manager):
        """Test getting operator by name"""
        operator = operator_manager.get_operator_by_name("Ooredoo Algeria")
        assert operator is not None
        assert operator.name == "Ooredoo Algeria"
        assert operator.balance_ussd == "*223#"
    
    def test_get_operator_by_name_case_insensitive(self, operator_manager):
        """Test getting operator by name (case insensitive)"""
        operator = operator_manager.get_operator_by_name("ooredoo algeria")
        assert operator is not None
        assert operator.name == "Ooredoo Algeria"
    
    def test_get_operator_by_name_not_found(self, operator_manager):
        """Test getting operator by name when not found"""
        operator = operator_manager.get_operator_by_name("Unknown Operator")
        assert operator is None
    
    def test_get_all_operators(self, operator_manager):
        """Test getting all operators"""
        operators = operator_manager.get_all_operators()
        assert len(operators) == 3
        
        operator_names = [op["name"] for op in operators]
        assert "Ooredoo Algeria" in operator_names
        assert "Djezzy" in operator_names
        assert "Mobilis" in operator_names
    
    def test_add_operator(self, operator_manager):
        """Test adding a new operator"""
        new_operator = OperatorProfile(
            name="Test Operator",
            country="Algeria",
            mcc="603",
            mnc=["99"],
            imsi_prefix=["60399"],
            iccid_prefix=["8921399"],
            balance_ussd="*999#"
        )
        
        operator_manager.add_operator("test", new_operator)
        
        # Test that it was added
        operators = operator_manager.get_all_operators()
        assert len(operators) == 4
        
        # Test detection works
        operator = operator_manager.detect_operator("60399123456789", None)
        assert operator is not None
        assert operator["name"] == "Test Operator"
    
    def test_get_balance_ussd(self, operator_manager):
        """Test getting balance USSD code"""
        ussd = operator_manager.get_balance_ussd("Ooredoo Algeria")
        assert ussd == "*223#"
        
        ussd = operator_manager.get_balance_ussd("Djezzy")
        assert ussd == "*100#"
        
        ussd = operator_manager.get_balance_ussd("Unknown")
        assert ussd is None
    
    def test_get_data_balance_ussd(self, operator_manager):
        """Test getting data balance USSD code"""
        ussd = operator_manager.get_data_balance_ussd("Ooredoo Algeria")
        assert ussd == "*223*2#"
        
        ussd = operator_manager.get_data_balance_ussd("Djezzy")
        assert ussd == "*999#"
    
    def test_get_apn_settings(self, operator_manager):
        """Test getting APN settings"""
        apn = operator_manager.get_apn_settings("Ooredoo Algeria")
        assert apn is not None
        assert apn["apn"] == "internet"
        
        apn = operator_manager.get_apn_settings("Djezzy")
        assert apn is not None
        assert apn["apn"] == "djezzy.internet"
    
    def test_validate_phone_number_valid(self, operator_manager):
        """Test phone number validation with valid numbers"""
        # Local format
        assert operator_manager.validate_phone_number("0555123456", "Ooredoo Algeria") is True
        assert operator_manager.validate_phone_number("0666987654", "Djezzy") is True
        assert operator_manager.validate_phone_number("0777111222", "Mobilis") is True
        
        # International format
        assert operator_manager.validate_phone_number("213555123456", "Ooredoo Algeria") is True
    
    def test_validate_phone_number_invalid(self, operator_manager):
        """Test phone number validation with invalid numbers"""
        # Too short
        assert operator_manager.validate_phone_number("055512345", "Ooredoo Algeria") is False
        
        # Too long
        assert operator_manager.validate_phone_number("05551234567", "Ooredoo Algeria") is False
        
        # Wrong prefix
        assert operator_manager.validate_phone_number("0855123456", "Ooredoo Algeria") is False
        
        # Invalid international format
        assert operator_manager.validate_phone_number("212555123456", "Ooredoo Algeria") is False
    
    def test_format_phone_number_local_to_international(self, operator_manager):
        """Test formatting local number to international"""
        formatted = operator_manager.format_phone_number("0555123456", international=True)
        assert formatted == "+213555123456"
    
    def test_format_phone_number_international_to_local(self, operator_manager):
        """Test formatting international number to local"""
        formatted = operator_manager.format_phone_number("213555123456", international=False)
        assert formatted == "0555123456"
    
    def test_format_phone_number_already_formatted(self, operator_manager):
        """Test formatting already formatted numbers"""
        # Local number stays local
        formatted = operator_manager.format_phone_number("0555123456", international=False)
        assert formatted == "0555123456"
        
        # International number stays international
        formatted = operator_manager.format_phone_number("213555123456", international=True)
        assert formatted == "+213555123456"
