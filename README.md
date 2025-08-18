# SIM Card Management System

A professional, production-ready system for managing SIM cards with comprehensive support for Algerian mobile operators (Ooredoo Algeria, Djezzy, Mobilis). Features automatic modem detection, real-time monitoring, SMS management, and USSD operations through a modern web interface.

![System Overview](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![React](https://img.shields.io/badge/React-18.2%2B-blue)
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

### Modern UI
- **Professional Dashboard**: Clean, modern interface using shadcn/ui
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live data updates without page refresh
- **Dark/Light Theme**: Modern theme support

## 🛠️ System Requirements

### Hardware
- **Huawei USB Modem**: E3531s, E3531, E398, E173, or compatible
- **USB Port**: Available USB port for modem connection
- **Operating System**: Windows 10/11, Linux, or macOS

### Software
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher

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

### 3. Install Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install React dependencies
npm install

# Return to root directory
cd ..
```

### 4. Connect Your Modem
1. Insert your SIM card into the Huawei modem
2. Connect the modem to a USB port
3. Wait for Windows to install drivers (if on Windows)

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)
```bash
# Start both backend and frontend servers
python start_system.py
```

This will:
- Start the backend API server on http://localhost:8000
- Start the frontend development server on http://localhost:3000
- Automatically open your browser to the dashboard

### Option 2: Start Servers Separately

#### Start Backend Only
```bash
python run_backend.py
```

#### Start Frontend Only
```bash
cd frontend
npm start
```

## 🌐 Access Points

Once running, access the system at:

- **Main Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000/api

## 📖 User Guide

### Initial Setup
1. **Connect Modem**: Ensure your Huawei modem is connected with a SIM card
2. **Start System**: Run `python start_system.py`
3. **Check Connection**: The dashboard will show connection status automatically

### Dashboard Overview
The main dashboard provides four key sections:

#### 1. Overview Tab
- **SIM Information**: IMSI, ICCID, IMEI, phone number
- **Signal Strength**: Real-time signal quality indicator
- **Network Type**: 2G/3G/4G connection status
- **Operator Details**: Detected operator and services

#### 2. SMS Tab
- **Send SMS**: Compose and send text messages
- **SMS Inbox**: View received and sent messages
- **Message Management**: Delete unwanted messages

#### 3. USSD Tab
- **Balance Check**: Quick balance inquiry button
- **Custom USSD**: Send any USSD code
- **Service Codes**: Quick access to operator services

#### 4. Settings Tab
- **Modem Information**: Hardware details and firmware
- **APN Settings**: Operator-specific internet settings
- **Connection Details**: Port and status information

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

# Frontend
FRONTEND_URL=http://localhost:3000
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

### Frontend Development
```bash
# Run frontend in development mode
cd frontend
npm start
```

### Building for Production
```bash
# Build frontend for production
cd frontend
npm run build
```

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
4. **Firewall**: Ensure ports 8000 and 3000 are not blocked

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
- **React**: For the frontend framework
- **shadcn/ui**: For the beautiful UI components

## 📞 Support

For technical support or questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review API documentation at http://localhost:8000/docs

---

**Made with ❤️ for the Algerian telecommunications community**
