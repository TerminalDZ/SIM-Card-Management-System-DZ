# Setup Guide - Multi-Modem SIM Card Management System API

This guide provides detailed setup instructions for the Multi-Modem SIM Card Management System API.

**GitHub Repository**: https://github.com/TerminalDZ/SIM-Card-Management-System-DZ

## 📋 Prerequisites

### Hardware Requirements
- **Multiple Huawei USB Modems**: One or more of the following models:
  - E3531s (recommended)
  - E3531
  - E398
  - E173
  - Other compatible Huawei models
- **SIM Cards**: From supported Algerian operators (Ooredoo, Djezzy, Mobilis)
- **Computer**: Windows 10/11, Linux, or macOS
- **USB Ports**: Multiple available USB 2.0 or 3.0 ports

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

1. **Prepare Your Modems**:
   - Insert SIM cards into multiple Huawei modems
   - Ensure the SIM cards are from supported operators (Ooredoo, Djezzy, Mobilis)
   - If your SIMs have PIN codes, disable them or note them down

2. **Connect the Modems**:
   - Plug the modems into different USB ports
   - Wait for your operating system to detect them
   - On Windows, drivers may install automatically

3. **Verify Modem Detection**:
   - **Windows**: Check Device Manager > Ports (COM & LPT)
   - **Linux**: Run `lsusb` or `ls /dev/ttyUSB*`
   - **macOS**: Run `ls /dev/cu.*`

### Step 4: First Run

1. **Start the API Server**:
```bash
python run_backend.py
```

2. **What Should Happen**:
   - API server starts on port 8000
   - Interactive documentation available at http://localhost:8000/docs
   - WebSocket endpoint available at ws://localhost:8000/ws
   - System automatically detects available modems

3. **Test the Multi-Modem API**:
   - Open http://localhost:8000/docs in your browser
   - Test the `/api/modems/detect` endpoint to see available modems
   - Connect to modems using `/api/modems/connect`
   - Test individual modem operations

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

### Issue: "Modems Not Detected"

**Symptoms**: API returns no detected modems

**Solutions**:
1. **Check Physical Connections**:
   - Ensure modems are properly plugged in
   - Try different USB ports
   - Use different USB cables if available

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
sudo python run_backend.py
```

### Issue: "SIM Cards Not Detected"

**Solutions**:
1. **Check SIM Cards**:
   - Ensure SIMs are properly inserted
   - Try the SIMs in phones to verify they work
   - Check if SIMs have PIN enabled (disable if possible)

2. **Network Registration**:
   - Wait a few minutes for network registration
   - Check signal strength in your area
   - Try restarting the modems

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
   - Test the `/api/modems/detect` endpoint
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

### Alternative: Use the Starter Script
```bash
python run_backend.py
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
- [ ] **Modem Detection**: `/api/modems/detect` returns available modems
- [ ] **Modem Connection**: Can connect to individual modems
- [ ] **Status**: `/api/modems/status` returns connected modems
- [ ] **SIM Info**: Can get SIM info from specific modems
- [ ] **SMS**: Can send/receive SMS from specific modems
- [ ] **USSD**: Can send USSD commands from specific modems
- [ ] **WebSocket**: WebSocket connection works for all modems

## 🆘 Getting Help

If you're still having issues:

1. **Check System Requirements**: Ensure all requirements are met
2. **Review Error Messages**: Look for specific error messages in console
3. **Check Logs**: Look at backend logs for detailed error information
4. **Test Components**: Try each component (modems, backend) separately
5. **Community Support**: Create an issue on GitHub with:
   - Your operating system
   - Python version
   - Modem models
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

## 📡 Multi-Modem API Usage Examples

### Using curl

#### Detect Available Modems
```bash
curl http://localhost:8000/api/modems/detect
```

#### Connect to a Modem
```bash
curl -X POST http://localhost:8000/api/modems/connect \
  -H "Content-Type: application/json" \
  -d '{"modem_id": "huawei_COM1"}'
```

#### Get All Modems Status
```bash
curl http://localhost:8000/api/modems/status
```

#### Get Specific Modem Status
```bash
curl http://localhost:8000/api/modems/huawei_COM1/status
```

#### Send SMS from Specific Modem
```bash
curl -X POST http://localhost:8000/api/modems/huawei_COM1/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "modem_id": "huawei_COM1",
    "number": "+213XXXXXXXX",
    "message": "Hello from multi-modem system"
  }'
```

#### Send USSD from Specific Modem
```bash
curl -X POST http://localhost:8000/api/modems/huawei_COM1/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "modem_id": "huawei_COM1",
    "command": "*223#"
  }'
```

### Using Python requests

```python
import requests

# Base URL
base_url = "http://localhost:8000/api"

# Detect modems
response = requests.get(f"{base_url}/modems/detect")
detected_modems = response.json()
print(f"Detected modems: {detected_modems}")

# Connect to first detected modem
if detected_modems['detected_modems']:
    modem_id = detected_modems['detected_modems'][0]
    
    # Connect to modem
    connect_data = {"modem_id": modem_id}
    response = requests.post(f"{base_url}/modems/connect", json=connect_data)
    print(f"Connection result: {response.json()}")
    
    # Get modem status
    response = requests.get(f"{base_url}/modems/{modem_id}/status")
    status = response.json()
    print(f"Modem status: {status}")
    
    # Send SMS from this modem
    sms_data = {
        "modem_id": modem_id,
        "number": "+213XXXXXXXX",
        "message": "Hello from Python"
    }
    response = requests.post(f"{base_url}/modems/{modem_id}/sms/send", json=sms_data)
    print(f"SMS result: {response.json()}")
```

### Multi-Modem Load Balancing Example

```python
import requests
import random

base_url = "http://localhost:8000/api"

# Get all connected modems
response = requests.get(f"{base_url}/modems/status")
modems_status = response.json()

# Get list of connected modem IDs
connected_modems = [
    modem_id for modem_id, status in modems_status['modems'].items() 
    if status['connected']
]

# Send SMS using load balancing (round-robin)
def send_sms_load_balanced(number, message):
    if not connected_modems:
        raise Exception("No modems connected")
    
    # Select modem using round-robin
    modem_id = random.choice(connected_modems)
    
    sms_data = {
        "modem_id": modem_id,
        "number": number,
        "message": message
    }
    
    response = requests.post(f"{base_url}/modems/{modem_id}/sms/send", json=sms_data)
    return response.json()

# Example usage
result = send_sms_load_balanced("+213XXXXXXXX", "Load balanced SMS")
print(f"Result: {result}")
```

---

**Need more help?** Check the main README.md or create an issue on GitHub.
