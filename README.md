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

## Installation

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

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
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

# Quick Local Testing Guide (Windows + WSL)

## Windows Setup

1. Open PowerShell as Administrator and install WSL if not already installed:
```powershell
wsl --install
```

2. Install Python 3.13 dependencies:
```powershell
python -m pip install --upgrade pip
python -m pip install virtualenv
```

## Testing Steps

1. Clone the repository in WSL:
```bash
cd ~
git clone https://github.com/yourusername/ltm-web-tool.git
cd ltm-web-tool
```

2. Create and activate Python virtual environment:
```bash
# In WSL terminal
python -m virtualenv venv
source venv/bin/activate

# Or in Windows PowerShell
python -m virtualenv venv
.\venv\Scripts\activate
```

3. Install backend requirements:
```bash
cd backend
pip install -r requirements.txt
```

4. Start the backend server:
```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or simple mode
python main.py
```

5. Open a new terminal and start the frontend:
```bash
cd frontend
npm install
npm start
```

The application will automatically open in your default browser at `http://localhost:3000`

## Quick Test DNS Tools

1. Test basic DNS lookup:
```bash
# In WSL or PowerShell
curl http://localhost:8000/api/dns/lookup -X POST -H "Content-Type: application/json" -d '{"query": "google.com", "type": "A"}'
```

2. Test reverse lookup:
```bash
curl http://localhost:8000/api/dns/reverse -X POST -H "Content-Type: application/json" -d '{"ip": "8.8.8.8"}'
```

## Troubleshooting Local Setup

- **Port already in use**: Change the port in the uvicorn command (e.g., --port 8001)
- **Module not found**: Make sure you're in the virtual environment
- **WSL networking issues**: Check WSL network adapter status
- **CORS errors**: Backend is configured to allow localhost frontend access

## Development Notes

- Backend API is available at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Frontend dev server: `http://localhost:3000`
- Hot reload is enabled for both frontend and backend