# Zimakiel Publisher - ZimaOS/CasaOS App Store Publisher

Automated tool to transform local projects into ZimaOS/CasaOS Apps, with Docker automation, YAML V2 configuration generation, SSH deployment to ZimaOS server, and Git integration.

## Features

- **User-friendly CLI**: Interactive prompts for all required information
- **Docker Automation**: Automatic Dockerfile generation for static sites, build, and push to Docker Hub
- **YAML V2 Configuration**: Generates properly formatted ZimaOS/CasaOS app configurations
- **SSH Integration**: Direct deployment to ZimaOS server via SSH using password or private key authentication
- **Remote File Transfer**: Automatically creates directories and transfers YAML files to ZimaOS
- **Remote Command Execution**: Optional ability to run commands on the ZimaOS server
- **Git Automation**: Automatic commit and push to GitHub repository

## Installation

### Prerequisites

- Python 3.7 or higher
- Docker installed and running
- Git configured
- SSH access to your ZimaOS server
- Docker Hub account

### Install Dependencies

```bash
pip install paramiko pyyaml
```

## Configuration

Before running the script, update the global variables at the top of `zimakiel_publisher.py`:

```python
GITHUB_USER = "your_github_username"      # Your GitHub username
DOCKER_USER = "your_dockerhub_username"   # Your Docker Hub username
REPO_NAME = "zimakiel-store"              # Repository name for the ZimaOS store
```

## Usage

Run the script:

```bash
python zimakiel_publisher.py
```

The script will guide you through the following steps:

1. **App Information**: Provide App ID, Display Name, Tagline, Icon URL, and External Port
2. **Project Information**: Specify local project path and project type (Static Site or Custom App)
3. **SSH Credentials**: Enter ZimaOS server IP, SSH username, and authentication method (password or private key)
4. **Docker Credentials**: Provide Docker Hub username and password/access token
5. **Automated Execution**: The script will automatically:
   - Create Dockerfile (if static site)
   - Build and push Docker image
   - Generate YAML V2 configuration
   - Connect via SSH to ZimaOS
   - Create remote directories
   - Transfer YAML file to ZimaOS
   - Optionally execute remote commands
   - Commit and push changes to GitHub

## SSH Authentication

The script supports two authentication methods:

### Password Authentication
- Enter your SSH password when prompted
- Simple and straightforward

### Private Key Authentication
- Provide the path to your SSH private key file
- More secure for automated deployments
- Supports RSA keys

## Remote Directory Structure

The script creates the following structure on your ZimaOS server:

```
/DATA/AppData/[APP_ID]/              # App data directory
/DATA/AppData/Zimakiel-Store/Apps/[APP_ID]/[APP_ID].yaml  # YAML configuration
```

## YAML V2 Configuration Format

The generated YAML follows the ZimaOS/CasaOS V2 specification:

```yaml
version: 2
id: app-id
title: App Display Name
tagline: Short description
icon: https://icon-url
description: Short description
category: Productivity
port: 8080
image: dockerhub-username/app-id:latest
environments: []
volumes: []
ports:
  - container: 80
    host: 8080
```

## Error Handling

The script includes comprehensive error handling:

- **SSH Connection**: Clear error messages for authentication failures, connection timeouts, and network issues
- **Docker Operations**: Detailed error reporting for build and push failures
- **File Operations**: Validation for file paths and permissions
- **Git Operations**: Helpful messages for repository initialization and push failures

## Example Workflow

```bash
$ python zimakiel_publisher.py

============================================================
ZIMAKIEL PUBLISHER - ZimaOS/CasaOS App Store Publisher
============================================================

[1/5] App ID (lowercase, no spaces, e.g., 'my-app'): my-web-app
[2/5] Display Name (e.g., 'My Awesome App'): My Web App
[3/5] Tagline (short description): A simple web application
[4/5] Icon URL (https://...): https://example.com/icon.png
[5/5] External Port (e.g., '8080'): 8080

------------------------------------------------------------
PROJECT INFORMATION
------------------------------------------------------------

Local project path (absolute or relative): ./my-project

Project Type:
  1 - Static Site (Nginx)
  2 - Custom App (User provides Dockerfile)

Select project type (1 or 2): 1

------------------------------------------------------------
SSH CREDENTIALS FOR ZIMAOS SERVER
------------------------------------------------------------

ZimaOS Server IP/Hostname: 192.168.1.100
SSH Port [default: 22]: 22
SSH Username [default: root]: root

Authentication Method:
  1 - Password
  2 - SSH Private Key
Select authentication method (1 or 2): 1
SSH Password: ********

------------------------------------------------------------
DOCKER HUB CREDENTIALS
------------------------------------------------------------

Docker Hub Username [default: your_dockerhub_username]: mydockeruser
Docker Hub Password (or access token): ********

[... automated execution ...]

============================================================
PUBLICATION SUMMARY
============================================================
App ID: my-web-app
Display Name: My Web App
Docker Image: mydockeruser/my-web-app:latest
Docker Build/Push: ✓ Success
SSH Deployment: ✓ Success
Git Push: ✓ Success
============================================================
```

## Troubleshooting

### SSH Connection Fails
- Verify server IP and port are correct
- Check firewall settings on both client and server
- Ensure SSH service is running on ZimaOS
- Verify credentials (password or private key path)

### Docker Build Fails
- Ensure Docker daemon is running
- Check project path is correct
- Verify Dockerfile syntax (if using custom app)

### Docker Push Fails
- Verify Docker Hub credentials
- Check if image name follows naming conventions
- Ensure you have push permissions for the repository

### Git Push Fails
- Configure git remote: `git remote add origin https://github.com/USER/REPO.git`
- Verify GitHub credentials are configured
- Check repository exists on GitHub

## License

This tool is provided as-is for ZimaOS/CasaOS app development.
