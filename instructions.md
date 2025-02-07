# F5 LTM Web Application - Setup Instructions

## Overview
This document outlines the setup instructions, configuration details, timeout settings, error handling, and TODO items for the F5 LTM Web Application. Please follow the steps carefully to ensure a successful installation and setup. Update the README.md file with the latest information about the project and how to run the code and how to use the code as well as any other relevant information.

---

## 1. Technology Stack
- **Frontend:** Flask/Dash/Streamlit with React.js (Lucide for images)
- **Backend:** Django (or Flask if Django is too bloated)
- **Database:** SQLite (Default) with optional PostgreSQL/MongoDB support
- **F5 LTM Communication:** iControl REST API and SSH (`tmsh` commands)
- **Excel Handling:** CSV and embedded Excel file parsing, editing, and exporting

---

## 2. Installation Steps

### 2.1 System Requirements
- **OS:** SUSE Linux 15.5/15.6 (also supports local testing)
- **Python:** 3.8+
- **Docker:** Optional for containerized deployment

### 2.2 Installing the Application
1. **Clone the repository:**  
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. **Install dependencies:**  
   ```sh
   pip install -r requirements.txt
   ```
3. **Set up the database:**  
   ```sh
   python manage.py migrate  # If using Django
   flask db upgrade           # If using Flask (alternative)
   ```
4. **Configure environment variables:**  
   Create a `.env` file in the root directory and add necessary configurations:
   ```sh
   F5_HOST=<your-f5-device-ip>
   F5_USERNAME=<your-username>
   F5_PASSWORD=<your-password>
   DATABASE_URL=<sqlite/postgresql/mongodb-connection-string>
   TIMEOUT_API=<default-timeout-in-seconds>
   TIMEOUT_SSH=<default-timeout-in-seconds>
   ```
5. **Run the application:**  
   ```sh
   python manage.py runserver  # Django
   flask run                    # Flask (alternative)
   ```

---

## 3. Configuration Features

- **Authentication:** Local authentication with optional LDAP/Active Directory integration
- **Session Management:** Traditional session cookies, 30-minute expiration (configurable up to 60 minutes)
- **Role-Based Access Control (RBAC):** Admin, Read-Only with configurable permissions
- **Logging:** Tracks authentication attempts, failed logins, successful logins, user actions (retained for 30 days)
- **F5 LTM Interaction:** Single-device updates only (no bulk updates), manual device addition, configurable SSH/API timeouts
- **Configuration Management:** Stages changes for approval, supports history tracking, includes rollback (TODO)
- **Excel Handling:** Parses, edits, filters, and exports configurations in Excel, CSV, and JSON
- **CLI Integration:** Available via the dashboard/web interface
- **Dashboard Features:**
  - Real-time updates (configurable, 10s increments, option to disable)
  - Dark mode/light mode toggle and theme customization

---

## 4. Timeout and Error Handling

### 4.1 Configurable Timeout Settings
- The application provides **configurable timeout settings** for:
  - **SSH commands to F5 LTM devices**
  - **API requests to F5 iControl REST API**
- The timeout values can be modified in the `.env` file:
  ```sh
  TIMEOUT_API=30  # API request timeout in seconds
  TIMEOUT_SSH=60  # SSH command timeout in seconds
  ```

### 4.2 Error Handling & Logging
- **API and SSH failures** will be logged, including timestamps, error messages, and the user who executed the command.
- If an API or SSH request **times out**, the system will:
  - **Retry the request (configurable retry count in the future, TODO)**
  - **Provide an error message to the user with troubleshooting steps**
- Authentication failures (including **failed login attempts exceeding the limit**) will be logged.
- Invalid configuration attempts will trigger **warnings or errors** before applying changes.
- Users **will not be blocked from retrieving VIP-to-IP mappings** if DNS resolution fails.
- A **history of version changes** will be maintained for tracking configuration modifications.

---

## 5. Deployment

### 5.1 Running as a Linux Service
1. **Install as a systemd service:**  
   ```sh
   sudo cp <service-file>.service /etc/systemd/system/f5app.service
   sudo systemctl enable f5app.service
   sudo systemctl start f5app.service
   ```

2. **Check service status:**  
   ```sh
   sudo systemctl status f5app.service
   ```

### 5.2 Docker Deployment
1. **Build and run the container:**  
   ```sh
   docker build -t f5-ltm-app .
   docker run -d -p 5000:5000 --name f5-ltm-app f5-ltm-app
   ```

---

## 6. File Structure
```
/f5-ltm-app
│── backend/          # Backend code (Django or Flask)
│── frontend/         # Frontend code (React.js)
│── cli/              # CLI integration
│── config/           # Configuration and environment settings
│── docs/             # Documentation files
│── logs/             # Application logs
│── migrations/       # Database migrations
│── scripts/          # Deployment and automation scripts
│── static/           # Static assets (CSS, images, etc.)
│── templates/        # HTML templates (if applicable)
│── tests/            # Unit and integration tests
│── .env.example      # Environment variable template
│── README.md         # Project overview and usage guide
│── requirements.txt  # Python dependencies
│── setup.py          # Installation script
```
**Please organize your code accordingly, or add new files to the appropriate directory.**

---

## 7. TODOs
- **Implement rollback mechanism for failed configurations**
- **Enhance automation capabilities (to be defined)**
- **Define reporting requirements and add scheduled exports**
- **Add optional OAuth2/OpenID authentication support in the future**
- **Implement optional password policy enforcement**
- **Introduce configurable retry logic for timeouts and connection failures**

---

## 8. Updating Documentation
After making any significant changes, update `README.md` with the latest information on:
- **Project overview**
- **How to install and run the code**
- **How to use the application** (including CLI and dashboard usage)
- **Any new features or breaking changes**


## 9. Additional Notes
- The application does **not** support real-time monitoring of F5 LTM device statuses.
- Ensure database cleanup tools are accessible to users who need to manage old records.
- Configuration validation is **optional** and should be enabled per user requirements.
- Timeouts and retries should be **monitored and adjusted based on performance needs**.



---

## 10. F5 LTM CLI & Dashboard Integration

### 10.1 CLI & Dashboard Support for TMSH Commands
The CLI and dashboard will provide **F5 LTM device integration via TMSH** if needed. Users will have access to the following commands for troubleshooting and configuration retrieval:

#### Available TMSH Commands:
- **Virtual Servers:**  
  ```sh
  list ltm virtual
  ```
- **Rules:**  
  ```sh
  list ltm rule
  ```
- **Pools:**  
  ```sh
  list ltm pool
  ```
- **Monitors (TCP):**  
  ```sh
  list ltm monitor tcp
  ```
- **Persistence (Cookie-based):**  
  ```sh
  list ltm persistance cookie
  ```
- **SSL Profiles:**  
  ```sh
  list ltm profile client-ssl
  ```
- **Nodes:**  
  ```sh
  list ltm node
  ```
- **Merge Configuration from Terminal:**  
  ```sh
  load sys config merge from-terminal
  ```

### 10.2 Usage Guidelines
- The CLI integration will be **accessible via the dashboard/web frontend** and a standalone command-line interface.
- **All TMSH command outputs** will be logged for auditing and troubleshooting purposes.
- Commands will be **executed securely over SSH** with proper credential validation.
- Users must have appropriate **RBAC permissions** to run these commands.

