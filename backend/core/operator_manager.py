from typing import Dict, List, Optional, Any
import logging

from models.models import OperatorProfile
from core.logger import get_operator_logger
from core.exceptions import OperatorDetectionException

logger = get_operator_logger()

class OperatorManager:
    def __init__(self):
        self.operators = self._load_operator_profiles()
    
    def _load_operator_profiles(self) -> Dict[str, OperatorProfile]:
        """Load predefined operator profiles for Algerian operators"""
        profiles = {
            "ooredoo": OperatorProfile(
                name="Ooredoo Algeria",
                country="Algeria",
                mcc="603",
                mnc=["02"],
                imsi_prefix=["60302"],
                iccid_prefix=["8921302", "8921303"],
                balance_ussd="*223#",
                data_balance_ussd="*223*2#",
                recharge_ussd="*100*{code}#",
                apn_settings={
                    "name": "Ooredoo Internet",
                    "apn": "internet",
                    "username": "",
                    "password": "",
                    "auth_type": "none",
                    "type": "default,supl"
                },
                common_services={
                    "customer_service": "*220#",
                    "balance_check": "*223#",
                    "data_balance": "*223*2#",
                    "validity_check": "*223*3#",
                    "recharge": "*100*{code}#",
                    "last_recharge": "*223*5#",
                    "sim_info": "*223*6#"
                }
            ),
            "djezzy": OperatorProfile(
                name="Djezzy",
                country="Algeria",
                mcc="603",
                mnc=["01"],
                imsi_prefix=["60301"],
                iccid_prefix=["8921301"],
                balance_ussd="*100#",
                data_balance_ussd="*999#",
                recharge_ussd="*100*{code}#",
                apn_settings={
                    "name": "Djezzy Internet",
                    "apn": "djezzy.internet",
                    "username": "",
                    "password": "",
                    "auth_type": "none",
                    "type": "default,supl"
                },
                common_services={
                    "customer_service": "*123#",
                    "balance_check": "*100#",
                    "data_balance": "*999#",
                    "recharge": "*100*{code}#",
                    "validity_check": "*555#",
                    "bonus_balance": "*100*2#",
                    "sim_info": "*444#"
                }
            ),
            "mobilis": OperatorProfile(
                name="Mobilis",
                country="Algeria",
                mcc="603",
                mnc=["00"],
                imsi_prefix=["60300"],
                iccid_prefix=["8921300"],
                balance_ussd="*100#",
                data_balance_ussd="*100*2#",
                recharge_ussd="*130*{code}#",
                apn_settings={
                    "name": "Mobilis Internet",
                    "apn": "internet",
                    "username": "",
                    "password": "",
                    "auth_type": "none",
                    "type": "default,supl"
                },
                common_services={
                    "customer_service": "*200#",
                    "balance_check": "*100#",
                    "data_balance": "*100*2#",
                    "recharge": "*130*{code}#",
                    "validity_check": "*100*3#",
                    "bonus_check": "*100*4#",
                    "sim_info": "*101#"
                }
            )
        }
        
        return profiles
    
    def detect_operator(self, imsi: Optional[str], iccid: Optional[str]) -> Optional[Dict[str, Any]]:
        """Detect operator based on IMSI and ICCID"""
        if not imsi and not iccid:
            return None
        
        logger.info(f"Detecting operator for IMSI: {imsi}, ICCID: {iccid}")
        
        for operator_key, profile in self.operators.items():
            # Check IMSI prefix
            if imsi:
                for prefix in profile.imsi_prefix:
                    if imsi.startswith(prefix):
                        logger.info(f"Detected operator {profile.name} by IMSI prefix {prefix}")
                        return self._profile_to_dict(profile)
            
            # Check ICCID prefix
            if iccid:
                for prefix in profile.iccid_prefix:
                    if iccid.startswith(prefix):
                        logger.info(f"Detected operator {profile.name} by ICCID prefix {prefix}")
                        return self._profile_to_dict(profile)
        
        # Fallback: try to detect by MCC/MNC from IMSI
        if imsi and len(imsi) >= 5:
            mcc = imsi[:3]
            mnc = imsi[3:5]
            
            for operator_key, profile in self.operators.items():
                if profile.mcc == mcc and mnc in profile.mnc:
                    logger.info(f"Detected operator {profile.name} by MCC/MNC {mcc}/{mnc}")
                    return self._profile_to_dict(profile)
        
        logger.warning("Could not detect operator")
        return None
    
    def get_operator_by_name(self, name: str) -> Optional[OperatorProfile]:
        """Get operator profile by name"""
        for profile in self.operators.values():
            if profile.name.lower() == name.lower():
                return profile
        return None
    
    def get_all_operators(self) -> List[Dict[str, Any]]:
        """Get all supported operators"""
        return [self._profile_to_dict(profile) for profile in self.operators.values()]
    
    def add_operator(self, key: str, profile: OperatorProfile):
        """Add a new operator profile"""
        self.operators[key] = profile
        logger.info(f"Added operator profile: {profile.name}")
    
    def get_balance_ussd(self, operator_name: str) -> Optional[str]:
        """Get balance USSD code for operator"""
        profile = self.get_operator_by_name(operator_name)
        return profile.balance_ussd if profile else None
    
    def get_data_balance_ussd(self, operator_name: str) -> Optional[str]:
        """Get data balance USSD code for operator"""
        profile = self.get_operator_by_name(operator_name)
        return profile.data_balance_ussd if profile else None
    
    def get_apn_settings(self, operator_name: str) -> Optional[Dict[str, Any]]:
        """Get APN settings for operator"""
        profile = self.get_operator_by_name(operator_name)
        return profile.apn_settings if profile else None
    
    def get_common_services(self, operator_name: str) -> Optional[Dict[str, str]]:
        """Get common service USSD codes for operator"""
        profile = self.get_operator_by_name(operator_name)
        return profile.common_services if profile else None
    
    def _profile_to_dict(self, profile: OperatorProfile) -> Dict[str, Any]:
        """Convert OperatorProfile to dictionary"""
        return {
            "name": profile.name,
            "country": profile.country,
            "mcc": profile.mcc,
            "mnc": profile.mnc,
            "balance_ussd": profile.balance_ussd,
            "data_balance_ussd": profile.data_balance_ussd,
            "recharge_ussd": profile.recharge_ussd,
            "apn_settings": profile.apn_settings,
            "common_services": profile.common_services
        }
    
    def validate_phone_number(self, phone_number: str, operator_name: str) -> bool:
        """Validate phone number format for specific operator"""
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Algerian mobile numbers are typically 10 digits starting with 05, 06, or 07
        if len(clean_number) == 10 and clean_number.startswith(('05', '06', '07')):
            return True
        
        # International format +213 followed by 9 digits
        if len(clean_number) == 12 and clean_number.startswith('213'):
            return True
        
        return False
    
    def format_phone_number(self, phone_number: str, international: bool = False) -> str:
        """Format phone number for Algerian operators"""
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        if len(clean_number) == 10 and clean_number.startswith(('05', '06', '07')):
            if international:
                return f"+213{clean_number[1:]}"
            else:
                return clean_number
        elif len(clean_number) == 12 and clean_number.startswith('213'):
            if international:
                return f"+{clean_number}"
            else:
                return f"0{clean_number[3:]}"
        
        return phone_number  # Return as-is if format not recognized
