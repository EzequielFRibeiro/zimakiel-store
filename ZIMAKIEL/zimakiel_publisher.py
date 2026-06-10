#!/usr/bin/env python3
"""
Zimakiel Publisher - ZimaOS/CasaOS App Store Publisher
Automates the process of transforming a local project into a ZimaOS App,
building/pushing Docker images, generating YAML V2 configuration,
and deploying via SSH to ZimaOS server.

Requirements:
    pip install paramiko pyyaml

Usage:
    python zimakiel_publisher.py
"""

import os
import sys
import subprocess
import shutil
import yaml
import paramiko
from pathlib import Path
from typing import Optional, Dict, Any

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================
GITHUB_USER = "EzequielFRibeiro"  # Replace with your GitHub username
DOCKER_USER = "your_dockerhub_username"  # Replace with your Docker Hub username
REPO_NAME = "zimakiel-store"  # Repository name for the ZimaOS store

# =============================================================================
# SSH CONFIGURATION CLASS
# =============================================================================
class SSHConfig:
    """Stores SSH connection credentials for ZimaOS server"""
    def __init__(self):
        self.host = ""
        self.port = 22
        self.username = ""
        self.password = ""
        self.private_key_path = ""
        self.use_key = False

# =============================================================================
# USER INPUT FUNCTIONS
# =============================================================================
def get_app_info() -> Dict[str, str]:
    """Collect basic app information from user"""
    print("\n" + "="*60)
    print("ZIMAKIEL PUBLISHER - ZimaOS/CasaOS App Store Publisher")
    print("="*60)
    
    app_info = {}
    
    app_info['app_id'] = input("\n[1/5] App ID (lowercase, no spaces, e.g., 'my-app'): ").strip().lower().replace(" ", "-")
    app_info['display_name'] = input("[2/5] Display Name (e.g., 'My Awesome App'): ").strip()
    app_info['tagline'] = input("[3/5] Tagline (short description): ").strip()
    app_info['icon_url'] = input("[4/5] Icon URL (https://...): ").strip()
    app_info['external_port'] = input("[5/5] External Port (e.g., '8080'): ").strip()
    
    return app_info

def get_project_info() -> Dict[str, str]:
    """Collect project path and type from user"""
    print("\n" + "-"*60)
    print("PROJECT INFORMATION")
    print("-"*60)
    
    project_info = {}
    
    project_info['project_path'] = input("\nLocal project path (absolute or relative): ").strip()
    project_info['project_path'] = os.path.abspath(project_info['project_path'])
    
    print("\nProject Type:")
    print("  1 - Static Site (Nginx)")
    print("  2 - Custom App (User provides Dockerfile)")
    
    while True:
        choice = input("\nSelect project type (1 or 2): ").strip()
        if choice in ['1', '2']:
            project_info['project_type'] = choice
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    return project_info

def get_ssh_credentials() -> SSHConfig:
    """Collect SSH credentials for ZimaOS server connection"""
    print("\n" + "-"*60)
    print("SSH CREDENTIALS FOR ZIMAOS SERVER")
    print("-"*60)
    
    ssh_config = SSHConfig()
    
    ssh_config.host = input("\nZimaOS Server IP/Hostname: ").strip()
    ssh_config.port = int(input(f"SSH Port [default: 22]: ").strip() or "22")
    ssh_config.username = input("SSH Username [default: root]: ").strip() or "root"
    
    print("\nAuthentication Method:")
    print("  1 - Password")
    print("  2 - SSH Private Key")
    
    while True:
        choice = input("Select authentication method (1 or 2): ").strip()
        if choice == '1':
            ssh_config.password = input("SSH Password: ").strip()
            ssh_config.use_key = False
            break
        elif choice == '2':
            ssh_config.private_key_path = input("Path to private key file: ").strip()
            ssh_config.private_key_path = os.path.abspath(ssh_config.private_key_path)
            ssh_config.use_key = True
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    return ssh_config

def get_docker_credentials() -> Dict[str, str]:
    """Collect Docker Hub credentials"""
    print("\n" + "-"*60)
    print("DOCKER HUB CREDENTIALS")
    print("-"*60)
    
    docker_info = {}
    
    docker_info['docker_username'] = input(f"\nDocker Hub Username [default: {DOCKER_USER}]: ").strip() or DOCKER_USER
    docker_info['docker_password'] = input("Docker Hub Password (or access token): ").strip()
    
    return docker_info

# =============================================================================
# DOCKER AUTOMATION FUNCTIONS
# =============================================================================
def create_dockerfile_static(project_path: str, app_id: str) -> str:
    """Create a Dockerfile for static sites using Nginx"""
    dockerfile_content = f"""FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
"""
    
    dockerfile_path = os.path.join(project_path, "Dockerfile")
    
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
    
    print(f"✓ Dockerfile created at: {dockerfile_path}")
    return dockerfile_path

def build_and_push_docker_image(project_path: str, app_id: str, docker_username: str, docker_password: str) -> bool:
    """Build Docker image locally and push to Docker Hub"""
    image_name = f"{docker_username}/{app_id}:latest"
    
    print("\n" + "-"*60)
    print("DOCKER BUILD AND PUSH")
    print("-"*60)
    
    try:
        # Login to Docker Hub
        print(f"\n[1/3] Logging in to Docker Hub as {docker_username}...")
        login_result = subprocess.run(
            ["docker", "login", "-u", docker_username, "--password-stdin"],
            input=docker_password,
            capture_output=True,
            text=True
        )
        
        if login_result.returncode != 0:
            print(f"✗ Docker login failed: {login_result.stderr}")
            return False
        
        print("✓ Docker login successful")
        
        # Build Docker image
        print(f"\n[2/3] Building Docker image: {image_name}")
        build_result = subprocess.run(
            ["docker", "build", "-t", image_name, project_path],
            capture_output=True,
            text=True
        )
        
        if build_result.returncode != 0:
            print(f"✗ Docker build failed: {build_result.stderr}")
            return False
        
        print("✓ Docker image built successfully")
        
        # Push Docker image
        print(f"\n[3/3] Pushing Docker image to Docker Hub...")
        push_result = subprocess.run(
            ["docker", "push", image_name],
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            print(f"✗ Docker push failed: {push_result.stderr}")
            return False
        
        print(f"✓ Docker image pushed successfully: {image_name}")
        return True
        
    except Exception as e:
        print(f"✗ Docker operation failed: {str(e)}")
        return False

# =============================================================================
# YAML V2 CONFIGURATION GENERATION
# =============================================================================
def generate_yaml_v2_config(app_info: Dict[str, str], docker_username: str) -> Dict[str, Any]:
    """Generate ZimaOS/CasaOS YAML V2 configuration"""
    
    config = {
        "version": 2,
        "id": app_info['app_id'],
        "title": app_info['display_name'],
        "tagline": app_info['tagline'],
        "icon": app_info['icon_url'],
        "description": app_info['tagline'],
        "category": "Productivity",
        "port": int(app_info['external_port']),
        "image": f"{docker_username}/{app_info['app_id']}:latest",
        "environments": [],
        "volumes": [],
        "ports": [
            {
                "container": 80,
                "host": int(app_info['external_port'])
            }
        ]
    }
    
    return config

def create_yaml_structure(app_info: Dict[str, str], docker_username: str, base_path: str = None) -> str:
    """Create local folder structure and YAML file for ZimaOS store"""
    
    if base_path is None:
        base_path = os.getcwd()
    
    # Create folder structure: Zimakiel/Apps/[APP_ID]/
    apps_dir = os.path.join(base_path, "Zimakiel", "Apps")
    app_dir = os.path.join(apps_dir, app_info['app_id'])
    
    os.makedirs(app_dir, exist_ok=True)
    
    # Generate YAML V2 config
    config = generate_yaml_v2_config(app_info, docker_username)
    
    # Write YAML file
    yaml_path = os.path.join(app_dir, f"{app_info['app_id']}.yaml")
    
    with open(yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"\n✓ YAML V2 configuration created at: {yaml_path}")
    print(f"✓ Folder structure created: {app_dir}")
    
    return yaml_path

# =============================================================================
# SSH FUNCTIONS FOR ZIMAOS DEPLOYMENT
# =============================================================================
def create_ssh_connection(ssh_config: SSHConfig) -> Optional[paramiko.SSHClient]:
    """Establish SSH connection to ZimaOS server with error handling"""
    
    print("\n" + "-"*60)
    print("SSH CONNECTION TO ZIMAOS SERVER")
    print("-"*60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\nConnecting to {ssh_config.username}@{ssh_config.host}:{ssh_config.port}...")
        
        if ssh_config.use_key:
            # Authenticate with private key
            if not os.path.exists(ssh_config.private_key_path):
                print(f"✗ Private key file not found: {ssh_config.private_key_path}")
                return None
            
            private_key = paramiko.RSAKey.from_private_key_file(ssh_config.private_key_path)
            ssh.connect(
                hostname=ssh_config.host,
                port=ssh_config.port,
                username=ssh_config.username,
                pkey=private_key,
                timeout=30
            )
            print("✓ SSH connection established using private key")
        else:
            # Authenticate with password
            ssh.connect(
                hostname=ssh_config.host,
                port=ssh_config.port,
                username=ssh_config.username,
                password=ssh_config.password,
                timeout=30
            )
            print("✓ SSH connection established using password")
        
        return ssh
        
    except paramiko.AuthenticationException:
        print("✗ SSH authentication failed. Check your credentials.")
        return None
    except paramiko.SSHException as e:
        print(f"✗ SSH connection error: {str(e)}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error during SSH connection: {str(e)}")
        return None

def create_remote_directory(ssh: paramiko.SSHClient, remote_path: str) -> bool:
    """Create a directory on the remote server via SSH"""
    
    try:
        print(f"Creating remote directory: {remote_path}")
        
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_path}")
        
        error = stderr.read().decode().strip()
        if error:
            print(f"✗ Failed to create directory: {error}")
            return False
        
        print(f"✓ Remote directory created: {remote_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating remote directory: {str(e)}")
        return False

def transfer_file_via_sftp(ssh: paramiko.SSHClient, local_path: str, remote_path: str) -> bool:
    """Transfer a file to the remote server using SFTP"""
    
    try:
        print(f"Transferring file: {local_path} -> {remote_path}")
        
        sftp = ssh.open_sftp()
        
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
            stderr.read()
        
        sftp.put(local_path, remote_path)
        sftp.close()
        
        print(f"✓ File transferred successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error transferring file: {str(e)}")
        return False

def execute_remote_command(ssh: paramiko.SSHClient, command: str) -> bool:
    """Execute a command on the remote server via SSH"""
    
    try:
        print(f"\nExecuting remote command: {command}")
        
        stdin, stdout, stderr = ssh.exec_command(command)
        
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"Output: {output}")
        
        if error:
            print(f"Error: {error}")
            return False
        
        print("✓ Remote command executed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error executing remote command: {str(e)}")
        return False

def deploy_to_zimaos_via_ssh(ssh_config: SSHConfig, app_info: Dict[str, str], yaml_path: str) -> bool:
    """Deploy app configuration to ZimaOS server via SSH"""
    
    ssh = create_ssh_connection(ssh_config)
    if not ssh:
        return False
    
    try:
        # Create app data directory on ZimaOS
        app_data_path = f"/DATA/AppData/{app_info['app_id']}"
        if not create_remote_directory(ssh, app_data_path):
            return False
        
        # Create store directory for YAML file
        store_path = f"/DATA/AppData/Zimakiel-Store/Apps/{app_info['app_id']}"
        if not create_remote_directory(ssh, store_path):
            return False
        
        # Transfer YAML file to ZimaOS
        remote_yaml_path = f"{store_path}/{app_info['app_id']}.yaml"
        if not transfer_file_via_sftp(ssh, yaml_path, remote_yaml_path):
            return False
        
        # Ask if user wants to execute a remote command
        print("\n" + "-"*60)
        print("OPTIONAL: REMOTE COMMAND EXECUTION")
        print("-"*60)
        
        run_command = input("\nDo you want to run a remote command on ZimaOS? (y/n): ").strip().lower()
        if run_command == 'y':
            command = input("Enter the command to execute: ").strip()
            execute_remote_command(ssh, command)
        
        return True
        
    finally:
        ssh.close()
        print("\n✓ SSH connection closed")

# =============================================================================
# GIT AUTOMATION FUNCTIONS
# =============================================================================
def commit_and_push_to_github(repo_path: str, commit_message: str) -> bool:
    """Commit and push changes to GitHub repository"""
    
    print("\n" + "-"*60)
    print("GIT AUTOMATION")
    print("-"*60)
    
    try:
        os.chdir(repo_path)
        
        # Check if it's a git repository
        git_check = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True)
        if git_check.returncode != 0:
            print("✗ Not a git repository. Initializing...")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
        
        # Add all changes
        print("\n[1/3] Adding files to git...")
        subprocess.run(["git", "add", "."], check=True)
        print("✓ Files added")
        
        # Commit changes
        print("\n[2/3] Committing changes...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print("✓ Changes committed")
        
        # Push to GitHub
        print(f"\n[3/3] Pushing to GitHub ({GITHUB_USER}/{REPO_NAME})...")
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        
        if push_result.returncode != 0:
            print(f"✗ Git push failed: {push_result.stderr}")
            print("\nNote: Make sure you have configured git remote with:")
            print(f"  git remote add origin https://github.com/{GITHUB_USER}/{REPO_NAME}.git")
            return False
        
        print("✓ Changes pushed to GitHub successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Git operation failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during git operations: {str(e)}")
        return False

# =============================================================================
# MAIN FUNCTION
# =============================================================================
def main():
    """Main execution flow"""
    
    try:
        # Step 1: Collect user information
        app_info = get_app_info()
        project_info = get_project_info()
        ssh_config = get_ssh_credentials()
        docker_info = get_docker_credentials()
        
        # Step 2: Docker automation
        if project_info['project_type'] == '1':
            create_dockerfile_static(project_info['project_path'], app_info['app_id'])
        
        docker_success = build_and_push_docker_image(
            project_info['project_path'],
            app_info['app_id'],
            docker_info['docker_username'],
            docker_info['docker_password']
        )
        
        if not docker_success:
            print("\n⚠ Docker build/push failed. Continuing with other steps...")
        
        # Step 3: Generate YAML V2 configuration
        yaml_path = create_yaml_structure(app_info, docker_info['docker_username'])
        
        # Step 4: Deploy via SSH to ZimaOS
        print("\n" + "="*60)
        print("DEPLOYING TO ZIMAOS VIA SSH")
        print("="*60)
        
        ssh_success = deploy_to_zimaos_via_ssh(ssh_config, app_info, yaml_path)
        
        if ssh_success:
            print("\n✓ SSH deployment to ZimaOS completed successfully")
        else:
            print("\n⚠ SSH deployment failed. Check the error messages above.")
        
        # Step 5: Git automation
        repo_path = os.path.dirname(yaml_path)
        commit_message = f"Add {app_info['app_id']} to Zimakiel Store"
        
        git_success = commit_and_push_to_github(repo_path, commit_message)
        
        # Final summary
        print("\n" + "="*60)
        print("PUBLICATION SUMMARY")
        print("="*60)
        print(f"App ID: {app_info['app_id']}")
        print(f"Display Name: {app_info['display_name']}")
        print(f"Docker Image: {docker_info['docker_username']}/{app_info['app_id']}:latest")
        print(f"Docker Build/Push: {'✓ Success' if docker_success else '✗ Failed'}")
        print(f"SSH Deployment: {'✓ Success' if ssh_success else '✗ Failed'}")
        print(f"Git Push: {'✓ Success' if git_success else '✗ Failed'}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
