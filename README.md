# LTM Web Tool

A comprehensive web-based management tool for F5 BIG-IP Local Traffic Manager (LTM) devices. This tool provides a modern, user-friendly interface for managing and monitoring F5 devices, with advanced DNS tools, configuration management, backup/restore capabilities, and system monitoring.

## Features

### DNS Tools
- **Forward DNS Lookup**
  - Support for all common record types (A, AAAA, MX, NS, TXT, CNAME, SOA)
  - Custom DNS server selection
  - Response time monitoring
  - TTL tracking
  
- **Reverse DNS Lookup**
  - IPv4 and IPv6 support
  - Batch lookup capabilities
  - PTR record validation

- **DNSSEC Validation**
  - Trust chain validation
  - Revocation status checking
  - Timestamp enforcement
  - Visual chain representation
  - Security status indicators

- **Zone Transfer**
  - Full zone transfer (AXFR)
  - Incremental zone transfer (IXFR)
  - Zone file export
  - Record filtering

- **DNS Propagation**
  - Multi-server checking
  - Popular DNS providers included
  - Response time comparison
  - Propagation status tracking

- **Query History**
  - Historical query tracking
  - Query repetition
  - Result comparison
  - Export capabilities

### Device Management
- Add and manage multiple F5 LTM devices
- Real-time device status monitoring
- Resource utilization tracking (CPU, memory, connections)
- Module status overview (LTM, GTM, ASM, APM)

### Configuration Management
- View and edit device configurations
- Side-by-side configuration comparison
- Configuration backup and restore
- Version history tracking
- Configuration validation

### Backup & Restore
- Manual and scheduled backups
- Backup version comparison
- Selective restore options
- Dry-run capability
- Export backup reports

### System Monitoring
- Real-time system health checks
- Resource utilization graphs
- Connection statistics
- SSL certificate monitoring
- System logs and audit trails

### Administration
- User management with role-based access
- Email notifications for system events
- System maintenance tasks
- Audit logging
- Security settings

## Installation & Setup

### Frontend Setup
```bash
cd frontend
npm install
```

### Running the Application
```bash
# Start frontend development server
cd frontend
npm start
```

### Dependencies
The frontend requires these key dependencies (already in package.json):
- react-error-boundary: ^5.0.0
- @chakra-ui/react: ^2.8.2
- typescript: ^4.9.5

### Prerequisites
- Node.js 16+
- Python 3.8+
- F5 LTM device(s) with API access

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ltm-web-tool.git
cd ltm-web-tool
```

2. Install backend dependencies:
```bash
cd ../backend
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Development Setup

1. Start the frontend development server:
```bash
cd frontend
npm start
```

2. Start the backend development server:
```bash
cd backend
uvicorn main:app --reload
```

The application will be available at `http://localhost:3000`

## Usage

### DNS Tools

1. **Forward DNS Lookup**
   ```bash
   # CLI
   ltm-tool dns lookup example.com --type=A
   
   # Web Interface
   Navigate to DNS Tools > Forward Lookup
   Enter domain and select record type
   ```

2. **Reverse DNS Lookup**
   ```bash
   # CLI
   ltm-tool dns reverse 192.168.1.1
   
   # Web Interface
   Navigate to DNS Tools > Reverse Lookup
   Enter IP address
   ```

3. **DNSSEC Validation**
   ```bash
   # CLI
   ltm-tool dns lookup example.com --dnssec
   
   # Web Interface
   Navigate to DNS Tools > DNSSEC
   Configure validation options
   ```

4. **Zone Transfer**
   ```bash
   # CLI
   ltm-tool dns zone-transfer example.com
   
   # Web Interface
   Navigate to DNS Tools > Zone Transfer
   Enter domain and optional nameserver
   ```

### Device Management

1. Adding a Device
   - Navigate to Devices in the admin dashboard
   - Click "Add Device"
   - Enter device details
   - Click "Add Device"

2. Monitoring
   - View device status in the dashboard
   - Check system health indicators
   - Monitor resource utilization
   - View active connections and throughput

### Configuration Management

1. Backup Creation
   - Go to Admin > Configuration Backups
   - Click "Create Backup"
   - Add optional comment
   - Wait for completion

2. Configuration Comparison
   - Select a backup from the list
   - Click "Compare"
   - Choose target backup
   - View differences by category

## Security Considerations

- All passwords are encrypted
- HTTPS required for production
- Role-based access control
- Audit logging enabled by default
- Session timeout configuration
- Failed login attempt limiting
- DNSSEC validation available

## API Documentation

API documentation is available at `/api/docs` when running the server.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting

Common issues and solutions:
- DNS lookup failures: Check network connectivity and DNS server availability
- Zone transfer denied: Verify server allows zone transfers
- DNSSEC validation errors: Check if domain supports DNSSEC
- API connection issues: Verify F5 device credentials and connectivity

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support:
- Open an issue in the GitHub repository
- Check the troubleshooting guide
- Contact the maintainers

# Quick Local Testing Guide (Windows with Git Bash)

## Windows Prerequisites Setup

1. **Python 3.13** - Already installed ✅
   - Verified with `python --version` showing Python 3.13.2

2. **Install Node.js and npm**:
   - Download Node.js LTS from [nodejs.org](https://nodejs.org/)
   - Run the installer
   - **Important**: During installation:
     - Check "Automatically install necessary tools"
     - Check "Add to PATH"
   - After installation, close and reopen Git Bash
   - Verify installation:
   ```bash
   node --version   # Should show v16.x or higher
   npm --version    # Should show 8.x or higher
   ```

   If commands still not found after installation:
   ```bash
   # Add Node.js to PATH manually in Git Bash
   export PATH="$PATH:/c/Program Files/nodejs"
   # OR for user-specific installation
   export PATH="$PATH:$APPDATA/npm"
   ```

3. **Verify All Requirements**:
```bash
# Check all installations
python --version
node --version
npm --version
```

## Setup Steps (After Node.js Installation)

1. Stay in your project directory:
```bash
cd ~/Desktop/WORK/AI-WERK/CursorAI/LTM-Web-Tool
```

2. Create Python virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate
```

3. Install backend requirements:
```bash
cd backend
pip install -r requirements.txt
```

4. Start the backend server:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

5. Open a new Git Bash window and start the frontend:
```bash
cd ~/Desktop/WORK/AI-WERK/CursorAI/LTM-Web-Tool/frontend
npm install
npm start
```

## Troubleshooting Node.js/npm Issues

1. **If Node.js commands not found after installation**:
   - Open Windows PowerShell as Administrator and run:
   ```powershell
   # Refresh environment variables
   refreshenv
   # OR
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   ```
   - Then close and reopen Git Bash

2. **Alternative Node.js Setup**:
   ```bash
   # Check if Node.js is installed but not in PATH
   ls "/c/Program Files/nodejs"
   # If found, add to PATH
   export PATH="$PATH:/c/Program Files/nodejs"
   ```

3. **Verify Node.js Installation**:
   ```bash
   # Should show installation directory
   where node
   where npm
   ```

4. **If npm install fails**:
   ```bash
   # Clear npm cache and try again
   npm cache clean --force
   npm install
   ```

## Development Notes

- Backend runs on: `http://localhost:8000`
- Frontend runs on: `http://localhost:3000`
- API docs available at: `http://localhost:8000/docs`
- Use `Ctrl+C` to stop either server

## Directory Structure
```
ltm-web-tool/
├── backend/
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── package.json
    └── src/
```

## Environment Variables
Create `.env` file in backend directory:
```bash
cp backend/.env.example backend/.env
```

Default content for `.env`:
```
DEBUG=True
HOST=127.0.0.1
PORT=8000
```

## TODO
- Device Monitoring Features
  - Health Dashboard
  - Traffic Monitoring
  - Pool Monitoring
  - Virtual Server Status
  - Real-time metrics and alerts