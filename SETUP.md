# Setup Guide - SIM Card Management System

This guide provides detailed setup instructions for the SIM Card Management System.

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
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher
- **Git**: For cloning the repository

## 🔧 Step-by-Step Installation

### Step 1: Prepare Your System

#### Windows
1. **Install Python**:
   - Download from https://python.org
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Install Node.js**:
   - Download from https://nodejs.org
   - Install the LTS version
   - Verify: `node --version` and `npm --version`

3. **Install Git**:
   - Download from https://git-scm.com
   - Use default settings during installation

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install Node.js and npm
sudo apt install nodejs npm

# Install Git
sudo apt install git

# Verify installations
python3 --version
node --version
npm --version
git --version
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install Node.js
brew install node

# Install Git
brew install git

# Verify installations
python3 --version
node --version
npm --version
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

3. **Install Frontend Dependencies**:
```bash
cd frontend
npm install
cd ..
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

1. **Start the System**:
```bash
python start_system.py
```

2. **What Should Happen**:
   - Backend server starts on port 8000
   - Frontend development server starts on port 3000
   - Your default browser opens to http://localhost:3000
   - Dashboard should show connection status

3. **Check Connection Status**:
   - Look at the "Connection" card in the dashboard
   - Should show "Connected" with green indicator
   - If disconnected, see troubleshooting section

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
```

### Frontend Configuration

The frontend automatically connects to the backend. If you change the backend port, update the proxy setting in `frontend/package.json`:
```json
{
  "proxy": "http://localhost:YOUR_BACKEND_PORT"
}
```

## 🚨 Troubleshooting

### Issue: "Modem Not Detected"

**Symptoms**: Dashboard shows "Disconnected" status

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

### Issue: "Frontend Won't Start"

**Solutions**:
1. **Check Node.js Installation**:
   ```bash
   node --version  # Should be 16.0+
   npm --version   # Should be 8.0+
   ```

2. **Clear npm Cache**:
   ```bash
   cd frontend
   npm cache clean --force
   rm -rf node_modules
   npm install
   ```

3. **Port Already in Use**:
   ```bash
   # Kill processes using port 3000
   # Linux/macOS
   sudo lsof -ti:3000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   ```

### Issue: "Backend API Errors"

**Solutions**:
1. **Check Backend Logs**:
   - Look for error messages in the console
   - Check log file if configured

2. **Port Issues**:
   ```bash
   # Check if port 8000 is available
   # Linux/macOS
   sudo lsof -i:8000
   
   # Windows
   netstat -ano | findstr :8000
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

## 🔄 Manual Operation

If the automatic start script doesn't work, you can run components separately:

### Start Backend Only
```bash
cd backend
python main.py
```

### Start Frontend Only
```bash
cd frontend
npm start
```

### Test Backend API
Visit http://localhost:8000/docs to see the API documentation and test endpoints.

## 📊 Verification Checklist

After setup, verify these work:

- [ ] **Connection**: Dashboard shows "Connected"
- [ ] **SIM Info**: Overview tab shows IMSI, ICCID, IMEI
- [ ] **Signal**: Signal strength indicator shows a value
- [ ] **Operator**: Operator name is detected correctly
- [ ] **SMS**: Can view SMS tab without errors
- [ ] **USSD**: Can enter USSD commands
- [ ] **Real-time**: Status updates automatically

## 🆘 Getting Help

If you're still having issues:

1. **Check System Requirements**: Ensure all requirements are met
2. **Review Error Messages**: Look for specific error messages in console
3. **Check Logs**: Look at backend logs for detailed error information
4. **Test Components**: Try each component (modem, backend, frontend) separately
5. **Community Support**: Create an issue on GitHub with:
   - Your operating system
   - Python and Node.js versions
   - Modem model
   - Complete error messages
   - Steps you've already tried

## 🎯 Production Deployment

For production deployment:

1. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Configure Environment**:
   - Set `DEBUG=False`
   - Configure proper logging
   - Set up reverse proxy (nginx/Apache)

3. **Security**:
   - Use proper firewall rules
   - Consider HTTPS certificates
   - Implement proper authentication

4. **Monitoring**:
   - Set up log rotation
   - Monitor system resources
   - Set up health checks

---

**Need more help?** Check the main README.md or create an issue on GitHub.
