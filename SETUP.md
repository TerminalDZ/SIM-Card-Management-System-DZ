# Setup Guide - SIM Card Management System API

This guide provides detailed setup instructions for the SIM Card Management System API.

## 📋 Prerequisites

### Hardware Requirements
- **Huawei USB Modem**: One of the following models:
  - E3531s (recommended)
  - E3531
  - E398
  - E173
  - Other compatible Huawei models
- **SIM Card**: From supported Algerian operators (Ooredoo, Djezzy, Mobilis)
- **Computer**: Windows 10/11, Linux, or macOS
- **USB Port**: Available USB 2.0 or 3.0 port

### Software Requirements
- **Python**: 3.8 or higher
- **Git**: For cloning the repository

## 🔧 Step-by-Step Installation

### Step 1: Prepare Your System

#### Windows
1. **Install Python**:
   - Download from https://python.org
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Install Git**:
   - Download from https://git-scm.com
   - Use default settings during installation

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install Git
sudo apt install git

# Verify installations
python3 --version
git --version
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install Git
brew install git

# Verify installations
python3 --version
git --version
```

### Step 2: Clone and Setup Project

1. **Clone the Repository**:
```bash
git clone <repository-url>
cd etg-api
```

2. **Install Python Dependencies**:
```bash
pip install -r requirements.txt
```

### Step 3: Hardware Setup

1. **Prepare Your Modem**:
   - Insert your SIM card into the Huawei modem
   - Ensure the SIM card is from a supported operator (Ooredoo, Djezzy, Mobilis)
   - If your SIM has a PIN code, disable it or note it down

2. **Connect the Modem**:
   - Plug the modem into a USB port
   - Wait for your operating system to detect it
   - On Windows, drivers may install automatically

3. **Verify Modem Detection**:
   - **Windows**: Check Device Manager > Ports (COM & LPT)
   - **Linux**: Run `lsusb` or `ls /dev/ttyUSB*`
   - **macOS**: Run `ls /dev/cu.*`

### Step 4: First Run

1. **Start the API Server**:
```bash
python start_system.py
```

2. **What Should Happen**:
   - API server starts on port 8000
   - Interactive documentation available at http://localhost:8000/docs
   - WebSocket endpoint available at ws://localhost:8000/ws

3. **Test the API**:
   - Open http://localhost:8000/docs in your browser
   - Test the `/api/status` endpoint to verify connection
   - Check if modem is detected and connected

## 🔧 Configuration Options

### Backend Configuration

Create `backend/.env` file for custom settings:
```env
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=sim_manager.log

# Modem Settings
MODEM_TIMEOUT=30
MODEM_RETRY_COUNT=3
AUTO_DETECT_MODEM=True

# CORS Settings
ALLOWED_ORIGINS=["*"]
```

## 🚨 Troubleshooting

### Issue: "Modem Not Detected"

**Symptoms**: API returns disconnected status

**Solutions**:
1. **Check Physical Connection**:
   - Ensure modem is properly plugged in
   - Try a different USB port
   - Use a different USB cable if available

2. **Driver Issues (Windows)**:
   - Open Device Manager
   - Look for "Unknown Device" or devices with yellow warning
   - Download Huawei Mobile Connect drivers
   - Restart computer after driver installation

3. **Permissions (Linux)**:
   ```bash
   # Add your user to dialout group
   sudo usermod -a -G dialout $USER
   
   # Logout and login again, or restart
   ```

4. **Check Available Ports**:
   ```bash
   # Linux
   ls /dev/ttyUSB* /dev/ttyACM*
   
   # Windows (in Command Prompt)
   mode
   
   # macOS
   ls /dev/cu.*
   ```

### Issue: "Permission Denied" (Linux/macOS)

**Solutions**:
```bash
# Linux - Add user to dialout group
sudo usermod -a -G dialout $USER

# Make sure the ports are accessible
sudo chmod 666 /dev/ttyUSB0  # Replace with your port

# macOS - Run with sudo
sudo python start_system.py
```

### Issue: "SIM Card Not Detected"

**Solutions**:
1. **Check SIM Card**:
   - Ensure SIM is properly inserted
   - Try the SIM in a phone to verify it works
   - Check if SIM has PIN enabled (disable if possible)

2. **Network Registration**:
   - Wait a few minutes for network registration
   - Check signal strength in your area
   - Try restarting the modem

### Issue: "API Server Won't Start"

**Solutions**:
1. **Check Python Installation**:
   ```bash
   python --version  # Should be 3.8+
   pip --version
   ```

2. **Check Dependencies**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Port Already in Use**:
   ```bash
   # Kill processes using port 8000
   # Linux/macOS
   sudo lsof -ti:8000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### Issue: "API Endpoints Not Working"

**Solutions**:
1. **Check Server Logs**:
   - Look for error messages in the console
   - Check log file if configured

2. **Test Basic Endpoints**:
   - Visit http://localhost:8000/docs
   - Test the `/api/status` endpoint
   - Check if CORS is properly configured

3. **Verify Configuration**:
   - Check `.env` file settings
   - Ensure all required environment variables are set

## 🔄 Manual Operation

If the automatic start script doesn't work, you can run the backend directly:

### Start Backend Only
```bash
cd backend
python main.py
```

### Test API Endpoints
Visit http://localhost:8000/docs to:
- View all available endpoints
- Test API calls directly in the browser
- See request/response schemas
- Download OpenAPI specification

## 📊 Verification Checklist

After setup, verify these work:

- [ ] **API Server**: Server starts without errors
- [ ] **Documentation**: http://localhost:8000/docs loads
- [ ] **Connection**: `/api/status` returns connected status
- [ ] **SIM Info**: `/api/sim-info` returns SIM details
- [ ] **SMS**: `/api/sms` endpoint works
- [ ] **USSD**: `/api/ussd` endpoint accepts commands
- [ ] **WebSocket**: WebSocket connection works

## 🆘 Getting Help

If you're still having issues:

1. **Check System Requirements**: Ensure all requirements are met
2. **Review Error Messages**: Look for specific error messages in console
3. **Check Logs**: Look at backend logs for detailed error information
4. **Test Components**: Try each component (modem, backend) separately
5. **Community Support**: Create an issue on GitHub with:
   - Your operating system
   - Python version
   - Modem model
   - Complete error messages
   - Steps you've already tried

## 🎯 Production Deployment

For production deployment:

1. **Configure Environment**:
   - Set `DEBUG=False`
   - Configure proper logging
   - Set up reverse proxy (nginx/Apache)

2. **Security**:
   - Use proper firewall rules
   - Consider HTTPS certificates
   - Implement proper authentication
   - Configure CORS properly

3. **Monitoring**:
   - Set up log rotation
   - Monitor system resources
   - Set up health checks

4. **API Documentation**:
   - The API documentation is automatically available at `/docs`
   - Consider disabling docs in production for security

## 📡 API Usage Examples

### Using curl
```bash
# Check status
curl http://localhost:8000/api/status

# Get SIM info
curl http://localhost:8000/api/sim-info

# Send SMS
curl -X POST http://localhost:8000/api/sms/send \
  -H "Content-Type: application/json" \
  -d '{"number": "+213XXXXXXXX", "message": "Hello World"}'

# Send USSD command
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"command": "*223#"}'
```

### Using Python requests
```python
import requests

# Base URL
base_url = "http://localhost:8000/api"

# Check status
response = requests.get(f"{base_url}/status")
print(response.json())

# Send SMS
sms_data = {
    "number": "+213XXXXXXXX",
    "message": "Hello from API"
}
response = requests.post(f"{base_url}/sms/send", json=sms_data)
print(response.json())
```

---

**Need more help?** Check the main README.md or create an issue on GitHub.
