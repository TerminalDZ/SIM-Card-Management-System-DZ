# SIM Card Management System API

A professional, production-ready API system for managing SIM cards with comprehensive support for Algerian mobile operators (Ooredoo Algeria, Djezzy, Mobilis). Features automatic modem detection, real-time monitoring, SMS management, and USSD operations through a comprehensive REST API.

![System Overview](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)

## 🚀 Features

### Core Functionality
- **Automatic Modem Detection**: Robust detection of Huawei modems (E3531s and variants)
- **Operator Recognition**: Automatic detection of Algerian operators based on IMSI/ICCID
- **Real-time Monitoring**: Live signal strength, network type, and connection status
- **SIM Information**: Complete SIM details (IMSI, ICCID, IMEI, MSISDN)

### SMS Management
- **Read SMS**: View all received and sent messages
- **Send SMS**: Send text messages with delivery confirmation
- **Delete SMS**: Remove messages from SIM storage
- **Real-time Updates**: Live SMS notifications via WebSocket

### USSD Operations
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
- **WebSocket Support**: Real-time updates and notifications
- **Auto-generated Documentation**: Interactive API docs at `/docs`
- **OpenAPI Specification**: Standard-compliant API specification

## 🛠️ System Requirements

### Hardware
- **Huawei USB Modem**: E3531s, E3531, E398, E173, or compatible
- **USB Port**: Available USB port for modem connection
- **Operating System**: Windows 10/11, Linux, or macOS

### Software
- **Python**: 3.8 or higher

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd etg-api
```

### 2. Install Python Dependencies
```bash
# Install backend dependencies
pip install -r requirements.txt
```

### 3. Connect Your Modem
1. Insert your SIM card into the Huawei modem
2. Connect the modem to a USB port
3. Wait for Windows to install drivers (if on Windows)

## 🚀 Quick Start

### Start the API Server
```bash
# Start the backend API server
python start_system.py
```

This will:
- Start the API server on http://localhost:8000
- Provide interactive API documentation at http://localhost:8000/docs
- Enable WebSocket connections for real-time updates

### Alternative: Start Backend Only
```bash
python run_backend.py
```

## 🌐 Access Points

Once running, access the system at:

- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000/api
- **WebSocket**: ws://localhost:8000/ws

## 📖 API Guide

### Initial Setup
1. **Connect Modem**: Ensure your Huawei modem is connected with a SIM card
2. **Start API**: Run `python start_system.py`
3. **Check Connection**: Use the `/api/status` endpoint to verify connection

### API Overview
The API provides comprehensive endpoints for SIM card management:

#### 1. Status & Information
- **GET /api/status**: Modem connection status and basic information
- **GET /api/sim-info**: Complete SIM card details and operator information
- **GET /api/operators**: List of supported operators

#### 2. SMS Operations
- **GET /api/sms**: Retrieve all SMS messages
- **POST /api/sms/send**: Send a new SMS message
- **DELETE /api/sms/{id}**: Delete a specific SMS message

#### 3. USSD Operations
- **POST /api/ussd**: Send any USSD command
- **GET /api/balance**: Check account balance using operator-specific codes

#### 4. Real-time Updates
- **WebSocket /ws**: Real-time connection for status updates and SMS notifications

### Operator-Specific Features

#### Ooredoo Algeria
- **Balance Code**: `*223#`
- **Data Balance**: `*223*2#`
- **Recharge**: `*100*{code}#`
- **APN**: `internet`

#### Djezzy
- **Balance Code**: `*100#`
- **Data Balance**: `*999#`
- **Recharge**: `*100*{code}#`
- **APN**: `djezzy.internet`

#### Mobilis
- **Balance Code**: `*100#`
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

## 📊 API Reference

### Core Endpoints

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
Real-time updates for status changes and SMS notifications.

## 🔍 Troubleshooting

### Common Issues

#### Modem Not Detected
1. **Check USB Connection**: Ensure modem is properly connected
2. **Driver Issues**: Install latest Huawei modem drivers
3. **Port Access**: Run as administrator on Windows
4. **Multiple Ports**: Some modems create multiple COM ports; system will auto-detect the correct one

#### Connection Failed
1. **SIM Card**: Ensure SIM card is properly inserted
2. **PIN Code**: If SIM has PIN, disable it or enter it manually
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
