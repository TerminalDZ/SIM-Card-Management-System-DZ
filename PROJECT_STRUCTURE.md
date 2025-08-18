# Project Structure - SIM Card Management System

```
etg-api/
├── README.md                      # Main documentation
├── SETUP.md                       # Detailed setup guide
├── LICENSE                        # MIT License
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
├── start_system.py               # Main system starter
├── run_backend.py                # Backend-only starter
└── PROJECT_STRUCTURE.md          # This file

backend/                           # Python FastAPI Backend
├── __init__.py
├── main.py                       # Main FastAPI application
├── config.py                     # Configuration settings
├── core/                         # Core functionality
│   ├── __init__.py
│   ├── modem_manager.py          # Modem detection & AT commands
│   └── operator_manager.py      # Operator profiles & detection
└── models/                       # Data models
    ├── __init__.py
    └── models.py                 # Pydantic models

frontend/                         # React Frontend
├── package.json                  # Node.js dependencies
├── tailwind.config.js           # Tailwind CSS configuration
├── postcss.config.js            # PostCSS configuration
├── public/
│   └── index.html               # Main HTML template
└── src/
    ├── index.tsx                # React entry point
    ├── index.css                # Global styles
    ├── App.tsx                  # Main App component
    ├── types/
    │   └── index.ts             # TypeScript definitions
    ├── hooks/
    │   └── useApi.ts            # API hooks
    ├── lib/
    │   └── utils.ts             # Utility functions
    └── components/
        ├── Dashboard.tsx        # Main dashboard component
        └── ui/                  # UI components (shadcn/ui)
            ├── button.tsx
            ├── card.tsx
            ├── input.tsx
            ├── textarea.tsx
            ├── badge.tsx
            ├── progress.tsx
            └── tabs.tsx
```

## 📁 Directory Descriptions

### Root Directory
- **README.md**: Comprehensive documentation with features, installation, and usage
- **SETUP.md**: Detailed step-by-step setup instructions
- **requirements.txt**: Python package dependencies
- **start_system.py**: Convenient script to start both backend and frontend
- **run_backend.py**: Backend-only starter script

### Backend (`backend/`)
- **main.py**: FastAPI application with all API endpoints and WebSocket support
- **config.py**: Configuration management with environment variables
- **core/modem_manager.py**: Core modem functionality including:
  - Automatic Huawei modem detection
  - Serial port management
  - AT command interface
  - SMS operations
  - USSD operations
- **core/operator_manager.py**: Operator management including:
  - Algerian operator profiles (Ooredoo, Djezzy, Mobilis)
  - Automatic operator detection
  - USSD codes and APN settings
- **models/models.py**: Pydantic data models for API

### Frontend (`frontend/`)
- **src/App.tsx**: Main React application
- **src/components/Dashboard.tsx**: Complete dashboard with:
  - Real-time status monitoring
  - SIM information display
  - SMS management interface
  - USSD command interface
  - Settings and configuration
- **src/hooks/useApi.ts**: Custom React hooks for API interaction
- **src/components/ui/**: Modern UI components using shadcn/ui
- **Tailwind CSS**: Modern styling framework

## 🔧 Key Features Implemented

### 1. Automatic Modem Detection
- Supports multiple Huawei models (E3531s, E3531, E398, E173)
- VID/PID recognition
- Multiple port testing
- Robust error handling

### 2. Operator Detection
- **Ooredoo Algeria**: IMSI prefix 60302, USSD *223#
- **Djezzy**: IMSI prefix 60301, USSD *100#
- **Mobilis**: IMSI prefix 60300, USSD *100#
- Automatic detection via IMSI/ICCID
- Extensible for new operators

### 3. Complete SMS Management
- Read all SMS messages
- Send SMS with delivery confirmation
- Delete SMS messages
- Real-time SMS notifications

### 4. USSD Operations
- Balance checking with operator-specific codes
- Custom USSD command support
- Response parsing and display

### 5. Real-time Monitoring
- WebSocket connection for live updates
- Signal strength monitoring
- Network type detection (2G/3G/4G)
- Connection status tracking

### 6. Modern UI
- Professional dashboard design
- Responsive layout
- Real-time data updates
- Intuitive navigation
- Error handling and loading states

## 🚀 Quick Start Commands

```bash
# Install everything and start
pip install -r requirements.txt
cd frontend && npm install && cd ..
python start_system.py

# Backend only
python run_backend.py

# Frontend only
cd frontend && npm start
```

## 📡 API Endpoints

### Status & Information
- `GET /api/status` - Modem connection status
- `GET /api/sim-info` - Complete SIM information
- `GET /api/operators` - Supported operators list

### SMS Operations
- `GET /api/sms` - Get all SMS messages
- `POST /api/sms/send` - Send SMS message
- `DELETE /api/sms/{id}` - Delete SMS message

### USSD Operations
- `POST /api/ussd` - Send USSD command
- `GET /api/balance` - Check account balance

### Real-time
- `WS /ws` - WebSocket for real-time updates

## 🎯 Production Ready Features

- **Error Handling**: Comprehensive error handling throughout
- **Logging**: Configurable logging system
- **Configuration**: Environment-based configuration
- **Documentation**: Complete API documentation at `/docs`
- **Security**: CORS configuration for frontend integration
- **Monitoring**: Real-time status monitoring
- **Extensibility**: Easy to add new operators and features

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

This system is production-ready and provides professional-grade SIM card management capabilities with a modern, user-friendly interface.
