from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NetworkType(str, Enum):
    GSM = "2G"
    UMTS = "3G"
    LTE = "4G"
    UNKNOWN = "Unknown"

class SmsStatus(str, Enum):
    UNREAD = "REC UNREAD"
    READ = "REC READ"
    STORED_UNSENT = "STO UNSENT"
    STORED_SENT = "STO SENT"

class ModemStatus(BaseModel):
    connected: bool
    port: Optional[str] = None
    model: Optional[str] = None
    firmware: Optional[str] = None
    signal_strength: Optional[int] = None
    network_type: Optional[NetworkType] = None
    operator: Optional[str] = None
    error: Optional[str] = None

class SimInfo(BaseModel):
    imsi: Optional[str] = None
    iccid: Optional[str] = None
    imei: Optional[str] = None
    msisdn: Optional[str] = None
    operator_name: Optional[str] = None
    signal_strength: Optional[int] = None
    signal_quality: Optional[int] = None
    rssi: Optional[int] = None
    network_type: Optional[NetworkType] = None
    network_operator: Optional[str] = None
    roaming: Optional[bool] = None

class SmsMessage(BaseModel):
    id: int
    status: SmsStatus
    phone_number: str
    message: str
    timestamp: datetime
    pdu_type: Optional[str] = None

class UssdResponse(BaseModel):
    command: str
    response: str
    success: bool
    timestamp: datetime

class OperatorProfile(BaseModel):
    name: str
    country: str
    mcc: str  # Mobile Country Code
    mnc: List[str]  # Mobile Network Codes
    imsi_prefix: List[str]
    iccid_prefix: List[str]
    balance_ussd: Optional[str] = None
    data_balance_ussd: Optional[str] = None
    recharge_ussd: Optional[str] = None
    apn_settings: Optional[Dict[str, Any]] = None
    common_services: Optional[Dict[str, str]] = None

class ATCommand(BaseModel):
    command: str
    expected_response: Optional[str] = "OK"
    timeout: Optional[int] = 5
    retries: Optional[int] = 3
