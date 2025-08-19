# Project Structure - Multi-Modem SIM Card Management System

```
etg-api/
├── README.md                      # Main documentation
├── SETUP.md                       # Detailed setup guide
├── LICENSE                        # MIT License
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
├── run_backend.py                # Backend-only starter
└── PROJECT_STRUCTURE.md          # This file

backend/                           # Python FastAPI Backend
├── __init__.py
├── main.py                       # Main FastAPI application
├── config.py                     # Configuration settings
├── core/                         # Core functionality
│   ├── __init__.py
│   ├── modem_manager.py          # Single modem detection & AT commands
│   ├── multi_modem_manager.py    # Multi-modem management & coordination
│   └── operator_manager.py      # Operator profiles & detection
└── models/                       # Data models
    ├── __init__.py
    └── models.py                 # Pydantic models (including multi-modem)
```

## 📁 Directory Descriptions

### Root Directory
- **README.md**: Comprehensive documentation with features, installation, and usage
- **SETUP.md**: Detailed step-by-step setup instructions
- **requirements.txt**: Python package dependencies
- **run_backend.py**: Backend-only starter script

### Backend (`backend/`)
- **main.py**: FastAPI application with all API endpoints and WebSocket support
- **config.py**: Configuration management with environment variables
- **core/modem_manager.py**: Single modem functionality including:
  - Automatic Huawei modem detection
  - Serial port management
  - AT command interface
  - SMS operations
  - USSD operations
- **core/multi_modem_manager.py**: Multi-modem management including:
  - Multiple modem detection and management
  - Individual modem connection/disconnection
  - Load balancing across modems
  - Concurrent operations handling
  - Modem status tracking
- **core/operator_manager.py**: Operator management including:
  - Algerian operator profiles (Ooredoo, Djezzy, Mobilis)
  - Automatic operator detection
  - USSD codes and APN settings
- **models/models.py**: Pydantic data models for API including multi-modem support

## 🔧 Key Features Implemented

### 1. Multi-Modem Support
- **Concurrent Modem Management**: Handle multiple modems simultaneously
- **Automatic Detection**: Detect all available Huawei modems
- **Individual Control**: Connect/disconnect modems independently
- **Load Balancing**: Distribute operations across multiple modems
- **Status Tracking**: Monitor each modem's status independently

### 2. Automatic Modem Detection
- Supports multiple Huawei models (E3531s, E3531, E398, E173)
- VID/PID recognition for each modem
- Multiple port testing and validation
- Robust error handling per modem

### 3. Operator Detection
- **Ooredoo Algeria**: IMSI prefix 60302, USSD *223#
- **Djezzy**: IMSI prefix 60301, USSD *100#
- **Mobilis**: IMSI prefix 60300, USSD *100#
- Automatic detection via IMSI/ICCID for each modem
- Extensible for new operators

### 4. Complete SMS Management
- **Multi-Modem SMS**: Send SMS from any connected modem
- Read all SMS messages from specific modems
- Send SMS with delivery confirmation
- Delete SMS messages from specific modems
- Real-time SMS notifications for all modems

### 5. USSD Operations
- **Multi-Modem USSD**: Send USSD commands from any connected modem
- Balance checking with operator-specific codes
- Custom USSD command support
- Response parsing and display per modem

### 6. Real-time Monitoring
- WebSocket connection for live updates from all modems
- Signal strength monitoring for each modem
- Network type detection (2G/3G/4G) per modem
- Connection status tracking for all modems

### 7. API Architecture
- **Multi-Modem Endpoints**: New endpoints for managing multiple modems
- **Legacy Compatibility**: Original endpoints work with first connected modem
- **RESTful Design**: Clean, consistent API structure
- **WebSocket Support**: Real-time updates for all modems

## 🚀 Quick Start Commands

```bash
# Install dependencies and start
pip install -r requirements.txt
python run_backend.py

```

## �� API Endpoints

### System Endpoints
- `GET /api/health` - Health check and system status
- `GET /api/performance` - Performance metrics and monitoring

### Multi-Modem Management
- `POST /api/modems/detect` - Detect all available modems
- `POST /api/modems/connect` - Connect to a specific modem
- `POST /api/modems/disconnect` - Disconnect from a specific modem
- `GET /api/modems/status` - Get status for all connected modems

### Per-Modem Operations
- `GET /api/modems/{modem_id}/status` - Get status for specific modem
- `GET /api/modems/{modem_id}/sim-info` - Get SIM info for specific modem
- `GET /api/modems/{modem_id}/sms` - Get SMS from specific modem
- `POST /api/modems/{modem_id}/sms/send` - Send SMS from specific modem
- `DELETE /api/modems/{modem_id}/sms/{message_id}` - Delete SMS from specific modem
- `POST /api/modems/{modem_id}/ussd` - Send USSD from specific modem
- `GET /api/modems/{modem_id}/balance` - Get balance for specific modem

### Legacy Endpoints (Backward Compatibility)
- `GET /api/status` - Status of first connected modem
- `GET /api/sim-info` - SIM info of first connected modem
- `GET /api/sms` - SMS from first connected modem
- `POST /api/sms/send` - Send SMS from first connected modem
- `DELETE /api/sms/{message_id}` - Delete SMS from first connected modem
- `POST /api/ussd` - Send USSD from first connected modem
- `GET /api/balance` - Balance of first connected modem

### Real-time
- `WebSocket /ws` - Real-time updates for all modems

## 🎯 Production Ready Features

- **Error Handling**: Comprehensive error handling throughout
- **Logging**: Configurable logging system
- **Configuration**: Environment-based configuration
- **Documentation**: Complete API documentation at `/docs`
- **Security**: CORS configuration for API access
- **Monitoring**: Real-time status monitoring for all modems
- **Extensibility**: Easy to add new operators and features
- **Concurrency**: Thread-safe multi-modem operations
- **Resource Management**: Proper cleanup and connection management

## 📱 Operator Support

### Ooredoo Algeria
- Balance: `*223#`
- Data Balance: `*223*2#`
- Recharge: `*100*{code}#`
- APN: `internet`

### Djezzy
- Balance: `*100#`
- Data Balance: `*999#`
- Recharge: `*100*{code}#`
- APN: `djezzy.internet`

### Mobilis
- Balance: `*100#`
- Data Balance: `*100*2#`
- Recharge: `*130*{code}#`
- APN: `internet`

## 🔄 Multi-Modem Workflow

1. **Detection**: System automatically detects all available modems
2. **Connection**: Connect to specific modems as needed
3. **Operations**: Perform SMS/USSD operations on specific modems
4. **Monitoring**: Real-time status updates from all connected modems
5. **Management**: Connect/disconnect modems dynamically

This system is production-ready and provides professional-grade multi-modem SIM card management capabilities through a comprehensive REST API with full backward compatibility.
