# Multi-Modem SIM Card Management System API

A professional, production-ready API system for managing multiple SIM cards simultaneously with comprehensive support for Algerian mobile operators (Ooredoo Algeria, Djezzy, Mobilis). Features automatic multi-modem detection, real-time monitoring, SMS management, and USSD operations through a comprehensive REST API.

![System Overview](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)
![Multi-Modem](https://img.shields.io/badge/Multi--Modem-Supported-blue)

**GitHub Repository**: https://github.com/TerminalDZ/SIM-Card-Management-System-DZ

## 🚀 Features

### Core Functionality
- **Multi-Modem Support**: Manage multiple Huawei modems simultaneously
- **Automatic Modem Detection**: Robust detection of multiple Huawei modems (E3531s and variants)
- **Operator Recognition**: Automatic detection of Algerian operators based on IMSI/ICCID
- **Real-time Monitoring**: Live signal strength, network type, and connection status for all modems
- **SIM Information**: Complete SIM details (IMSI, ICCID, IMEI, MSISDN) for each modem

### Multi-Modem Management
- **Modem Detection**: Automatically detect all available modems
- **Individual Control**: Connect/disconnect modems independently
- **Status Monitoring**: Get status for all modems or individual modems
- **Load Balancing**: Distribute operations across multiple modems

### SMS Management
- **Multi-Modem SMS**: Send SMS from any connected modem
- **Read SMS**: View all received and sent messages from specific modems
- **Send SMS**: Send text messages with delivery confirmation
- **Delete SMS**: Remove messages from SIM storage
- **Real-time Updates**: Live SMS notifications via WebSocket

### USSD Operations
- **Multi-Modem USSD**: Send USSD commands from any connected modem
- **Balance Check**: Automatic balance inquiry using operator-specific codes
- **Custom USSD**: Send any USSD command
- **Operator Services**: Quick access to common operator services

### Operator Support
- **Ooredoo Algeria**: Full support with balance codes, APN settings
- **Djezzy**: Complete integration with service codes
- **Mobilis**: Full feature support and configuration
- **Extensible**: Easy to add new operators

### API Features
- **RESTful API**: Complete REST API with comprehensive endpoints
- **WebSocket Support**: Real-time updates and notifications for all modems
- **Auto-generated Documentation**: Interactive API docs at `/docs`
- **OpenAPI Specification**: Standard-compliant API specification
- **Backward Compatibility**: Legacy endpoints still work with first connected modem

## 🛠️ System Requirements

### Hardware
- **Multiple Huawei USB Modems**: E3531s, E3531, E398, E173, or compatible
- **USB Ports**: Multiple available USB ports for modem connections
- **Operating System**: Windows 10/11, Linux, or macOS

### Software
- **Python**: 3.8 or higher

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/TerminalDZ/SIM-Card-Management-System-DZ.git
cd SIM-Card-Management-System-DZ
```

### 2. Install Python Dependencies
```bash
# Install backend dependencies
pip install -r requirements.txt
```

### 3. Connect Your Modems
1. Insert SIM cards into multiple Huawei modems
2. Connect the modems to different USB ports
3. Wait for Windows to install drivers (if on Windows)

## 🚀 Quick Start

### Start the API Server
```bash
# Start the backend API server
python run_backend.py
```

This will:
- Start the API server on http://localhost:8000
- Provide interactive API documentation at http://localhost:8000/docs
- Enable WebSocket connections for real-time updates
- Automatically detect available modems

### Alternative: Start Backend Only
```bash
python run_backend.py
```

## 🌐 Access Points

Once running, access the system at:

- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 📖 API Guide

### Initial Setup
1. **Connect Modems**: Ensure your Huawei modems are connected with SIM cards
2. **Detect Modems**: Use `/api/modems/detect` to find available modems
3. **Connect Modems**: Use `/api/modems/connect` to connect to specific modems

### Multi-Modem API Overview

#### 1. Modem Management
- **GET /api/modems/detect**: Detect all available modems
- **POST /api/modems/connect**: Connect to a specific modem
- **POST /api/modems/disconnect**: Disconnect from a specific modem
- **GET /api/modems/status**: Get status for all connected modems
- **GET /api/modems/{modem_id}/status**: Get status for a specific modem

#### 2. SIM Information
- **GET /api/modems/{modem_id}/sim-info**: Get SIM details for a specific modem

#### 3. SMS Operations (Per Modem)
- **GET /api/modems/{modem_id}/sms**: Get SMS from a specific modem
- **POST /api/modems/{modem_id}/sms/send**: Send SMS from a specific modem
- **DELETE /api/modems/{modem_id}/sms/{id}**: Delete SMS from a specific modem

#### 4. USSD Operations (Per Modem)
- **POST /api/modems/{modem_id}/ussd**: Send USSD command from a specific modem
- **GET /api/modems/{modem_id}/balance**: Check balance for a specific modem

#### 5. Real-time Updates
- **WebSocket /ws**: Real-time connection for status updates from all modems

### Legacy Endpoints (Backward Compatibility)
All original endpoints still work and use the first connected modem:
- **GET /api/status**: Status of first connected modem
- **GET /api/sim-info**: SIM info of first connected modem
- **GET /api/sms**: SMS from first connected modem
- **POST /api/sms/send**: Send SMS from first connected modem
- **POST /api/ussd**: Send USSD from first connected modem
- **GET /api/balance**: Balance of first connected modem

### Operator-Specific Features

#### Ooredoo Algeria
- **Balance Code**: `*200#`
- **Data Balance**: `*223*2#`
- **Recharge**: `*100*{code}#`
- **APN**: `internet`

#### Djezzy
- **Balance Code**: `*710#`
- **Data Balance**: `*999#`
- **Recharge**: `*100*{code}#`
- **APN**: `djezzy.internet`

#### Mobilis
- **Balance Code**: `*222#`
- **Data Balance**: `*100*2#`
- **Recharge**: `*130*{code}#`
- **APN**: `internet`

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=sim_manager.log

# Modem Configuration
MODEM_TIMEOUT=30
MODEM_RETRY_COUNT=3
AUTO_DETECT_MODEM=True

# CORS Configuration
ALLOWED_ORIGINS=["*"]
```

### Adding New Operators
To add support for a new operator, edit `backend/core/operator_manager.py`:

```python
"new_operator": OperatorProfile(
    name="New Operator",
    country="Algeria",
    mcc="603",
    mnc=["XX"],
    imsi_prefix=["603XX"],
    iccid_prefix=["89213XX"],
    balance_ussd="*XXX#",
    # ... other settings
)
```

## 🛠️ Development

### Backend Development
```bash
# Run backend in development mode
cd backend
python main.py
```

### API Testing
Visit http://localhost:8000/docs to:
- View all available endpoints
- Test API calls directly in the browser
- See request/response schemas
- Download OpenAPI specification

## �� API Reference

### Complete API Endpoints

#### System Endpoints
- `GET /api/health` - Health check and system status
- `GET /api/performance` - Performance metrics and monitoring

#### Multi-Modem Management
- `POST /api/modems/detect` - Detect all available modems
- `POST /api/modems/connect` - Connect to a specific modem
- `POST /api/modems/disconnect` - Disconnect from a specific modem
- `GET /api/modems/status` - Get status for all connected modems

#### Per-Modem Operations
- `GET /api/modems/{modem_id}/status` - Get status for specific modem
- `GET /api/modems/{modem_id}/sim-info` - Get SIM info for specific modem
- `GET /api/modems/{modem_id}/sms` - Get SMS from specific modem
- `POST /api/modems/{modem_id}/sms/send` - Send SMS from specific modem
- `DELETE /api/modems/{modem_id}/sms/{message_id}` - Delete SMS from specific modem
- `POST /api/modems/{modem_id}/ussd` - Send USSD from specific modem
- `GET /api/modems/{modem_id}/balance` - Get balance for specific modem

#### Legacy Endpoints (Backward Compatibility)
- `GET /api/status` - Status of first connected modem
- `GET /api/sim-info` - SIM info of first connected modem
- `GET /api/sms` - SMS from first connected modem
- `POST /api/sms/send` - Send SMS from first connected modem
- `DELETE /api/sms/{message_id}` - Delete SMS from first connected modem
- `POST /api/ussd` - Send USSD from first connected modem
- `GET /api/balance` - Balance of first connected modem

#### Real-time
- `WebSocket /ws` - Real-time updates for all modems

### Legacy Endpoints (Single Modem)

#### Get Status
```http
GET /api/status
```
Returns modem connection status and basic information.

#### Get SIM Information
```http
GET /api/sim-info
```
Returns comprehensive SIM card details and operator information.

#### SMS Operations
```http
GET /api/sms                    # Get all SMS messages
POST /api/sms/send              # Send SMS
DELETE /api/sms/{message_id}    # Delete SMS
```

#### USSD Operations
```http
POST /api/ussd                  # Send USSD command
GET /api/balance               # Check balance
```

#### WebSocket
```
ws://localhost:8000/ws
```
Real-time updates for status changes and SMS notifications from all modems.

## 🔍 Troubleshooting

### Common Issues

#### Modems Not Detected
1. **Check USB Connections**: Ensure modems are properly connected
2. **Driver Issues**: Install latest Huawei modem drivers
3. **Port Access**: Run as administrator on Windows
4. **Multiple Ports**: Some modems create multiple COM ports; system will auto-detect the correct ones

#### Connection Failed
1. **SIM Cards**: Ensure SIM cards are properly inserted
2. **PIN Codes**: If SIMs have PINs, disable them or enter them manually
3. **Network Coverage**: Check signal strength in your area
4. **Firewall**: Ensure port 8000 is not blocked

#### SMS Not Working
1. **SMS Center**: Ensure SMS center number is configured
2. **Storage Full**: Delete old messages to free space
3. **Network**: SMS requires network connection

#### USSD Not Working
1. **Operator Support**: Ensure your operator supports the USSD code
2. **Balance**: Some codes require account balance
3. **Network**: USSD requires active network connection

### Debug Mode
Enable debug logging by setting `DEBUG=True` in configuration.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Huawei**: For modem hardware and AT command documentation
- **Algerian Operators**: For USSD codes and service information
- **FastAPI**: For the excellent backend framework

## 📞 Support

For technical support or questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review API documentation at http://localhost:8000/docs

---

**Made with ❤️ for the Algerian telecommunications community**
