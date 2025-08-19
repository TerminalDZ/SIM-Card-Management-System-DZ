"""
Operator management for the Multi-Modem SIM Card Management System.

This module provides the OperatorManager class for managing mobile operator
profiles, USSD codes, and operator-specific configurations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.core.logger import SimManagerLogger, log_operation, log_performance
from backend.core.exceptions import (
    OperatorDetectionException, UnsupportedOperatorException, ConfigurationException
)
from backend.config import get_settings
from backend.models.models import OperatorProfile, NetworkType


class OperatorManager:
    """
    Manages mobile operator profiles and configurations.
    
    This class provides operator detection, USSD code management, and
    operator-specific configurations for different mobile networks.
    """
    
    def __init__(self, settings=None):
        """
        Initialize the OperatorManager.
        
        Args:
            settings: Application settings object
        """
        self.settings = settings or get_settings()
        self.logger = SimManagerLogger(self.settings)
        
        # Operator profiles database
        self.operators: Dict[str, OperatorProfile] = {}
        
        # Initialize operator database
        self._initialize_operator_database()
        
        self.logger.info("OperatorManager initialized")
        self.logger.info(f"Loaded {len(self.operators)} operator profiles")
    
    def _initialize_operator_database(self):
        """Initialize the operator profiles database."""
        with log_operation(self.logger, "Initialize operator database"):
            try:
                # Algerian operators
                self.operators["ooredoo_algeria"] = OperatorProfile(
                name="Ooredoo Algeria",
                country="Algeria",
                mcc="603",
                    mnc=["01"],
                    imsi_prefix=["60301"],
                    iccid_prefix=["8921301"],
                balance_ussd="*223#",
                data_balance_ussd="*223*2#",
                recharge_ussd="*100*{code}#",
                apn_settings={
                        "name": "internet",
                    "apn": "internet",
                    "username": "",
                    "password": "",
                        "auth_type": "none"
                },
                common_services={
                        "balance": "*223#",
                    "data_balance": "*223*2#",
                    "recharge": "*100*{code}#",
                        "call_forward": "*21*{number}#",
                        "call_forward_cancel": "#21#",
                        "missed_calls": "*100#",
                        "last_recharge": "*100*1#"
                    }
                )
                
                self.operators["djezzy_algeria"] = OperatorProfile(
                    name="Djezzy Algeria",
                country="Algeria",
                mcc="603",
                    mnc=["03"],
                    imsi_prefix=["60303"],
                    iccid_prefix=["8921303"],
                balance_ussd="*100#",
                    data_balance_ussd="*100*2#",
                recharge_ussd="*100*{code}#",
                apn_settings={
                        "name": "internet",
                        "apn": "internet",
                    "username": "",
                    "password": "",
                        "auth_type": "none"
                },
                common_services={
                        "balance": "*100#",
                        "data_balance": "*100*2#",
                    "recharge": "*100*{code}#",
                        "call_forward": "*21*{number}#",
                        "call_forward_cancel": "#21#",
                        "missed_calls": "*100*1#",
                        "last_recharge": "*100*3#"
                    }
                )
                
                self.operators["mobilis_algeria"] = OperatorProfile(
                    name="Mobilis Algeria",
                country="Algeria",
                mcc="603",
                    mnc=["02"],
                    imsi_prefix=["60302"],
                    iccid_prefix=["8921302"],
                    balance_ussd="*101#",
                    data_balance_ussd="*101*2#",
                    recharge_ussd="*101*{code}#",
                    apn_settings={
                        "name": "internet",
                        "apn": "internet",
                        "username": "",
                        "password": "",
                        "auth_type": "none"
                    },
                    common_services={
                        "balance": "*101#",
                        "data_balance": "*101*2#",
                        "recharge": "*101*{code}#",
                        "call_forward": "*21*{number}#",
                        "call_forward_cancel": "#21#",
                        "missed_calls": "*101*1#",
                        "last_recharge": "*101*3#"
                    }
                )
                
                # International operators (examples)
                self.operators["orange_france"] = OperatorProfile(
                    name="Orange France",
                    country="France",
                    mcc="208",
                    mnc=["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
                    imsi_prefix=["20801", "20802", "20803", "20804", "20805", "20806", "20807", "20808", "20809", "20810"],
                    iccid_prefix=["20801", "20802", "20803", "20804", "20805", "20806", "20807", "20808", "20809", "20810"],
                    balance_ussd="*100#",
                    data_balance_ussd="*100*2#",
                    recharge_ussd="*100*{code}#",
                    apn_settings={
                        "name": "orange",
                        "apn": "orange",
                        "username": "",
                        "password": "",
                        "auth_type": "none"
                    },
                    common_services={
                        "balance": "*100#",
                        "data_balance": "*100*2#",
                        "recharge": "*100*{code}#"
                    }
                )
                
                self.operators["vodafone_uk"] = OperatorProfile(
                    name="Vodafone UK",
                    country="United Kingdom",
                    mcc="234",
                    mnc=["15", "91", "92", "93", "94", "95", "96", "97", "98", "99"],
                    imsi_prefix=["23415", "23491", "23492", "23493", "23494", "23495", "23496", "23497", "23498", "23499"],
                    iccid_prefix=["23415", "23491", "23492", "23493", "23494", "23495", "23496", "23497", "23498", "23499"],
                balance_ussd="*100#",
                data_balance_ussd="*100*2#",
                    recharge_ussd="*100*{code}#",
                apn_settings={
                        "name": "internet",
                    "apn": "internet",
                    "username": "",
                    "password": "",
                        "auth_type": "none"
                },
                common_services={
                        "balance": "*100#",
                    "data_balance": "*100*2#",
                        "recharge": "*100*{code}#"
                    }
                )
                
                self.logger.info(f"Successfully loaded {len(self.operators)} operator profiles")
                
                # Log performance metrics
                log_performance(self.logger, "operator_database_init", 
                    total_operators=len(self.operators),
                    countries=len(set(op.country for op in self.operators.values()))
                )
                
            except Exception as e:
                self.logger.error(f"Failed to initialize operator database: {e}")
                raise ConfigurationException(f"Failed to initialize operator database: {e}")
    
    def detect_operator(self, imsi: str, iccid: str = None) -> Optional[OperatorProfile]:
        """
        Detect operator based on IMSI and ICCID.
        
        Args:
            imsi: International Mobile Subscriber Identity
            iccid: Integrated Circuit Card Identifier (optional)
            
        Returns:
            OperatorProfile if detected, None otherwise
            
        Raises:
            OperatorDetectionException: If detection fails
        """
        with log_operation(self.logger, f"Detect operator for IMSI: {imsi[:6]}..."):
            try:
                if not imsi or len(imsi) < 6:
                    raise OperatorDetectionException("Invalid IMSI provided")
                
                # Extract MCC and MNC from IMSI (first 6 digits)
                mcc_mnc = imsi[:6]
                
                # Search for matching operator
                for operator_id, profile in self.operators.items():
                    # Check IMSI prefix
                    if mcc_mnc in profile.imsi_prefix:
                        self.logger.info(f"Detected operator: {profile.name} (IMSI prefix: {mcc_mnc})")
                        
                        # Log performance metrics
                        log_performance(self.logger, "operator_detection", 
                            operator=profile.name,
                            country=profile.country,
                            mcc_mnc=mcc_mnc,
                            method="imsi_prefix"
                        )
                        
                        return profile
                    
                    # Check ICCID prefix if provided
                    if iccid and profile.iccid_prefix:
                        for iccid_prefix in profile.iccid_prefix:
                            if iccid.startswith(iccid_prefix):
                                self.logger.info(f"Detected operator: {profile.name} (ICCID prefix: {iccid_prefix})")
                                
                                # Log performance metrics
                                log_performance(self.logger, "operator_detection", 
                                    operator=profile.name,
                                    country=profile.country,
                                    iccid_prefix=iccid_prefix,
                                    method="iccid_prefix"
                                )
                                
                                return profile
                
                self.logger.warning(f"No operator found for IMSI: {imsi[:6]}...")
                return None
                
            except Exception as e:
                self.logger.error(f"Operator detection failed: {e}")
                raise OperatorDetectionException(f"Failed to detect operator: {e}")
    
    def get_operator_by_name(self, operator_name: str) -> Optional[OperatorProfile]:
        """
        Get operator profile by name.
        
        Args:
            operator_name: Name of the operator
            
        Returns:
            OperatorProfile if found, None otherwise
        """
        with log_operation(self.logger, f"Get operator by name: {operator_name}"):
            try:
                # Search for exact match
                for operator_id, profile in self.operators.items():
                    if profile.name.lower() == operator_name.lower():
                        return profile
                
                # Search for partial match
                for operator_id, profile in self.operators.items():
                    if operator_name.lower() in profile.name.lower():
                        self.logger.info(f"Found partial match: {profile.name}")
                        return profile
                
                self.logger.warning(f"No operator found with name: {operator_name}")
                return None
                
            except Exception as e:
                self.logger.error(f"Failed to get operator by name: {e}")
        return None
    
    def get_operator_by_mcc_mnc(self, mcc: str, mnc: str) -> Optional[OperatorProfile]:
        """
        Get operator profile by MCC and MNC.
        
        Args:
            mcc: Mobile Country Code
            mnc: Mobile Network Code
            
        Returns:
            OperatorProfile if found, None otherwise
        """
        with log_operation(self.logger, f"Get operator by MCC/MNC: {mcc}/{mnc}"):
            try:
                mcc_mnc = f"{mcc}{mnc}"
                
                for operator_id, profile in self.operators.items():
                    if mcc_mnc in profile.imsi_prefix:
                        return profile
                
                self.logger.warning(f"No operator found for MCC/MNC: {mcc}/{mnc}")
                return None
                
            except Exception as e:
                self.logger.error(f"Failed to get operator by MCC/MNC: {e}")
        return None
    
    def get_operators_by_country(self, country: str) -> List[OperatorProfile]:
        """
        Get all operators for a specific country.
        
        Args:
            country: Country name
            
        Returns:
            List of OperatorProfile objects
        """
        with log_operation(self.logger, f"Get operators by country: {country}"):
            try:
                operators = []
                
                for operator_id, profile in self.operators.items():
                    if profile.country.lower() == country.lower():
                        operators.append(profile)
                
                self.logger.info(f"Found {len(operators)} operators for {country}")
                return operators
                
            except Exception as e:
                self.logger.error(f"Failed to get operators by country: {e}")
                return []
    
    def get_supported_operators(self) -> List[OperatorProfile]:
        """
        Get all supported operators.
        
        Returns:
            List of all OperatorProfile objects
        """
        with log_operation(self.logger, "Get all supported operators"):
            try:
                operators = list(self.operators.values())
                self.logger.info(f"Returning {len(operators)} supported operators")
                return operators
                
            except Exception as e:
                self.logger.error(f"Failed to get supported operators: {e}")
                return []
    
    def get_ussd_code(self, operator_name: str, service: str, **kwargs) -> Optional[str]:
        """
        Get USSD code for a specific operator and service.
        
        Args:
            operator_name: Name of the operator
            service: Service name (e.g., 'balance', 'recharge')
            **kwargs: Additional parameters for the USSD code
            
        Returns:
            USSD code if found, None otherwise
            
        Raises:
            UnsupportedOperatorException: If operator not supported
        """
        with log_operation(self.logger, f"Get USSD code for {operator_name} - {service}"):
            try:
                # Get operator profile
                operator = self.get_operator_by_name(operator_name)
                if not operator:
                    raise UnsupportedOperatorException(f"Operator not supported: {operator_name}")
                
                # Get USSD code from common services
                if operator.common_services and service in operator.common_services:
                    ussd_code = operator.common_services[service]
                    
                    # Replace placeholders with provided values
                    for key, value in kwargs.items():
                        placeholder = f"{{{key}}}"
                        if placeholder in ussd_code:
                            ussd_code = ussd_code.replace(placeholder, str(value))
                    
                    self.logger.info(f"USSD code for {operator_name} - {service}: {ussd_code}")
                    return ussd_code
                
                # Check specific USSD fields
                if service == "balance" and operator.balance_ussd:
                    return operator.balance_ussd
                elif service == "data_balance" and operator.data_balance_ussd:
                    return operator.data_balance_ussd
                elif service == "recharge" and operator.recharge_ussd:
                    ussd_code = operator.recharge_ussd
                    if "code" in kwargs:
                        ussd_code = ussd_code.replace("{code}", str(kwargs["code"]))
                    return ussd_code
                
                self.logger.warning(f"USSD code not found for {operator_name} - {service}")
                return None
                
            except UnsupportedOperatorException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to get USSD code: {e}")
                return None
    
    def get_apn_settings(self, operator_name: str) -> Optional[Dict[str, Any]]:
        """
        Get APN settings for a specific operator.
        
        Args:
            operator_name: Name of the operator
            
        Returns:
            APN settings dictionary if found, None otherwise
        """
        with log_operation(self.logger, f"Get APN settings for {operator_name}"):
            try:
                operator = self.get_operator_by_name(operator_name)
                if operator and operator.apn_settings:
                    return operator.apn_settings
                
                self.logger.warning(f"APN settings not found for {operator_name}")
                return None
                
            except Exception as e:
                self.logger.error(f"Failed to get APN settings: {e}")
                return None
    
    def add_operator(self, operator_id: str, profile: OperatorProfile) -> bool:
        """
        Add a new operator profile.
        
        Args:
            operator_id: Unique identifier for the operator
            profile: OperatorProfile object
            
        Returns:
            True if added successfully, False otherwise
        """
        with log_operation(self.logger, f"Add operator: {operator_id}"):
            try:
                if operator_id in self.operators:
                    self.logger.warning(f"Operator {operator_id} already exists, updating...")
                
                self.operators[operator_id] = profile
                self.logger.info(f"Successfully added operator: {profile.name}")
                
                # Log performance metrics
                log_performance(self.logger, "operator_added", 
                    operator_id=operator_id,
                    operator_name=profile.name,
                    country=profile.country,
                    total_operators=len(self.operators)
                )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add operator {operator_id}: {e}")
                return False
    
    def remove_operator(self, operator_id: str) -> bool:
        """
        Remove an operator profile.
        
        Args:
            operator_id: Unique identifier for the operator
            
        Returns:
            True if removed successfully, False otherwise
        """
        with log_operation(self.logger, f"Remove operator: {operator_id}"):
            try:
                if operator_id not in self.operators:
                    self.logger.warning(f"Operator {operator_id} not found")
                    return False
                
                operator_name = self.operators[operator_id].name
                del self.operators[operator_id]
                
                self.logger.info(f"Successfully removed operator: {operator_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to remove operator {operator_id}: {e}")
                return False
    
    def update_operator(self, operator_id: str, profile: OperatorProfile) -> bool:
        """
        Update an existing operator profile.
        
        Args:
            operator_id: Unique identifier for the operator
            profile: Updated OperatorProfile object
            
        Returns:
            True if updated successfully, False otherwise
        """
        with log_operation(self.logger, f"Update operator: {operator_id}"):
            try:
                if operator_id not in self.operators:
                    self.logger.warning(f"Operator {operator_id} not found, cannot update")
                    return False
                
                old_name = self.operators[operator_id].name
                self.operators[operator_id] = profile
                
                self.logger.info(f"Successfully updated operator: {old_name} -> {profile.name}")
                return True
            
            except Exception as e:
                self.logger.error(f"Failed to update operator {operator_id}: {e}")
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get operator manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        with log_operation(self.logger, "Get operator statistics"):
            try:
                countries = set(op.country for op in self.operators.values())
                mccs = set(op.mcc for op in self.operators.values())
                
                stats = {
                    "total_operators": len(self.operators),
                    "countries": len(countries),
                    "mccs": len(mccs),
                    "countries_list": list(countries),
                    "mccs_list": list(mccs),
                    "operators_with_ussd": len([op for op in self.operators.values() if op.balance_ussd]),
                    "operators_with_apn": len([op for op in self.operators.values() if op.apn_settings])
                }
                
                self.logger.info(f"Operator statistics: {stats}")
                return stats
                
            except Exception as e:
                self.logger.error(f"Failed to get statistics: {e}")
                return {}
    
    def validate_operator_profile(self, profile: OperatorProfile) -> bool:
        """
        Validate an operator profile.
        
        Args:
            profile: OperatorProfile to validate
            
        Returns:
            True if valid, False otherwise
        """
        with log_operation(self.logger, f"Validate operator profile: {profile.name}"):
            try:
                # Check required fields
                if not profile.name or not profile.country or not profile.mcc:
                    self.logger.error("Missing required fields in operator profile")
                    return False
                
                # Check IMSI prefixes
                if not profile.imsi_prefix:
                    self.logger.error("No IMSI prefixes defined")
                    return False
                
                # Validate MCC format (3 digits)
                if not profile.mcc.isdigit() or len(profile.mcc) != 3:
                    self.logger.error("Invalid MCC format")
                    return False
                
                # Validate MNC format (2-3 digits)
                for mnc in profile.mnc:
                    if not mnc.isdigit() or len(mnc) < 2 or len(mnc) > 3:
                        self.logger.error("Invalid MNC format")
                        return False
                
                # Validate IMSI prefixes
                for prefix in profile.imsi_prefix:
                    if not prefix.startswith(profile.mcc):
                        self.logger.error("IMSI prefix must start with MCC")
                        return False
                
                self.logger.info(f"Operator profile validation successful: {profile.name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Operator profile validation failed: {e}")
                return False
