export interface ModemStatus {
  connected: boolean;
  port?: string;
  model?: string;
  firmware?: string;
  signal_strength?: number;
  network_type?: 'GSM' | 'UMTS' | 'LTE' | 'Unknown';
  operator?: string;
  error?: string;
}

export interface SimInfo {
  imsi?: string;
  iccid?: string;
  imei?: string;
  msisdn?: string;
  operator_name?: string;
  signal_strength?: number;
  signal_quality?: number;
  rssi?: number;
  network_type?: 'GSM' | 'UMTS' | 'LTE' | 'Unknown';
  network_operator?: string;
  roaming?: boolean;
  operator?: OperatorInfo;
}

export interface OperatorInfo {
  name: string;
  country: string;
  mcc: string;
  mnc: string[];
  balance_ussd?: string;
  data_balance_ussd?: string;
  recharge_ussd?: string;
  apn_settings?: {
    name: string;
    apn: string;
    username: string;
    password: string;
    auth_type: string;
    type: string;
  };
  common_services?: Record<string, string>;
}

export interface SmsMessage {
  id: number;
  status: 'REC UNREAD' | 'REC READ' | 'STO UNSENT' | 'STO SENT';
  phone_number: string;
  message: string;
  timestamp: string;
  pdu_type?: string;
}

export interface UssdResponse {
  command: string;
  response: string;
  success: boolean;
  timestamp: string;
}

export interface BalanceResponse {
  success: boolean;
  operator: string;
  ussd_command: string;
  response: string;
}
