#!/usr/bin/env python3
"""
Google Secret Manager Setup Script
Stores all API keys and sensitive configuration encrypted in Google Secret Manager
Never stores keys in code or .env files in production
"""

import os
import sys
import subprocess
from typing import List, Dict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def check_gcloud_installed() -> bool:
    """Check if gcloud CLI is installed"""
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_authenticated() -> bool:
    """Check if user is authenticated with gcloud"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_project_id() -> str:
    """Get current Google Cloud project ID"""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            timeout=10
        )
        project_id = result.stdout.strip()
        if not project_id or project_id == "(unset)":
            print_error("No Google Cloud project set. Run: gcloud config set project YOUR_PROJECT_ID")
            sys.exit(1)
        return project_id
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print_error(f"Failed to get project ID: {e}")
        sys.exit(1)


def enable_secret_manager_api(project_id: str):
    """Enable Secret Manager API"""
    print_info("Enabling Secret Manager API...")
    try:
        result = subprocess.run(
            ["gcloud", "services", "enable", "secretmanager.googleapis.com", f"--project={project_id}"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print_success("Secret Manager API enabled")
        else:
            print_warning(f"API may already be enabled: {result.stderr}")
    except Exception as e:
        print_error(f"Failed to enable Secret Manager API: {e}")
        sys.exit(1)


def create_secret(project_id: str, secret_name: str, secret_value: str) -> bool:
    """Create a secret in Google Secret Manager"""
    try:
        # Check if secret already exists
        result = subprocess.run(
            ["gcloud", "secrets", "describe", secret_name, f"--project={project_id}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print_info(f"Secret {secret_name} already exists, updating...")
            # Update existing secret
            update_result = subprocess.run(
                ["gcloud", "secrets", "versions", "add", secret_name, f"--project={project_id}"],
                input=secret_value,
                text=True,
                capture_output=True,
                timeout=30
            )
            if update_result.returncode == 0:
                print_success(f"Updated secret: {secret_name}")
                return True
            else:
                print_error(f"Failed to update secret {secret_name}: {update_result.stderr}")
                return False
        else:
            # Create new secret
            create_result = subprocess.run(
                ["gcloud", "secrets", "create", secret_name, f"--project={project_id}"],
                input=secret_value,
                text=True,
                capture_output=True,
                timeout=30
            )
            if create_result.returncode == 0:
                print_success(f"Created secret: {secret_name}")
                return True
            else:
                print_error(f"Failed to create secret {secret_name}: {create_result.stderr}")
                return False
    except Exception as e:
        print_error(f"Error creating secret {secret_name}: {e}")
        return False


def setup_secrets(project_id: str, secrets: Dict[str, str]):
    """Setup all secrets in Google Secret Manager"""
    print_header("Setting up secrets in Google Secret Manager")
    
    success_count = 0
    for secret_name, secret_value in secrets.items():
        if secret_value:  # Only create if value is provided
            if create_secret(project_id, secret_name, secret_value):
                success_count += 1
        else:
            print_warning(f"Skipping {secret_name} (no value provided)")
    
    print(f"\n{Colors.GREEN}Successfully configured {success_count}/{len(secrets)} secrets{Colors.RESET}")


def grant_access(project_id: str, service_account: str):
    """Grant Secret Manager access to service account"""
    print_header("Granting Secret Manager Access")
    
    secrets = [
        "db-password",
        "redis-password",
        "secret-key",
        "jwt-secret",
        "encryption-key",
        "gemini-api-key",
        "openai-api-key",
        "groq-api-key",
        "stripe-api-key",
        "firebase-private-key",
        "smtp-password"
    ]
    
    for secret in secrets:
        try:
            result = subprocess.run(
                [
                    "gcloud", "secrets", "add-iam-policy-binding", secret,
                    f"--project={project_id}",
                    f"--member=serviceAccount:{service_account}",
                    "--role=roles/secretmanager.secretAccessor"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print_success(f"Granted access to {secret}")
            else:
                print_warning(f"Could not grant access to {secret} (may not exist yet)")
        except Exception as e:
            print_error(f"Error granting access to {secret}: {e}")


def create_secret_manager_service_account(project_id: str) -> str:
    """Create service account for accessing secrets"""
    print_header("Creating Service Account")
    
    service_account_name = "professional-ai-secret-accessor"
    service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
    
    try:
        # Check if service account exists
        result = subprocess.run(
            ["gcloud", "iam", "service-accounts", "describe", service_account_email],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            # Create service account
            create_result = subprocess.run(
                [
                    "gcloud", "iam", "service-accounts", "create", service_account_name,
                    f"--project={project_id}",
                    "--display-name=Professional AI Secret Accessor",
                    "--description=Service account for accessing secrets in production"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if create_result.returncode == 0:
                print_success(f"Created service account: {service_account_email}")
            else:
                print_error(f"Failed to create service account: {create_result.stderr}")
                return service_account_email
        else:
            print_info(f"Service account already exists: {service_account_email}")
        
        return service_account_email
    
    except Exception as e:
        print_error(f"Error creating service account: {e}")
        return service_account_email


def generate_secret_value(secret_type: str) -> str:
    """Generate a secure random value for secrets"""
    import secrets
    import string
    
    if secret_type in ["password", "key"]:
        return secrets.token_urlsafe(32)
    elif secret_type == "hex":
        return secrets.token_hex(32)
    else:
        return secrets.token_urlsafe(32)


def interactive_setup(project_id: str):
    """Interactive setup for secrets"""
    print_header("Interactive Secret Setup")
    
    print_info("You'll be prompted for sensitive values.")
    print_info("These will be stored encrypted in Google Secret Manager.\n")
    
    secrets = {}
    
    # Database passwords
    print(f"\n{Colors.BOLD}Database Configuration:{Colors.RESET}")
    secrets["db-password"] = input("Enter PostgreSQL password (or press Enter to generate): ").strip()
    if not secrets["db-password"]:
        secrets["db-password"] = generate_secret_value("password")
        print_info(f"Generated: {secrets['db-password']}")
    
    secrets["redis-password"] = input("Enter Redis password (or press Enter to generate): ").strip()
    if not secrets["redis-password"]:
        secrets["redis-password"] = generate_secret_value("password")
        print_info(f"Generated: {secrets['redis-password']}")
    
    # Security keys
    print(f"\n{Colors.BOLD}Security Keys:{Colors.RESET}")
    secrets["secret-key"] = input("Enter SECRET_KEY (or press Enter to generate): ").strip()
    if not secrets["secret-key"]:
        secrets["secret-key"] = generate_secret_value("hex")
        print_info(f"Generated: {secrets['secret-key']}")
    
    secrets["jwt-secret"] = input("Enter JWT_SECRET (or press Enter to generate): ").strip()
    if not secrets["jwt-secret"]:
        secrets["jwt-secret"] = generate_secret_value("hex")
        print_info(f"Generated: {secrets['jwt-secret']}")
    
    secrets["encryption-key"] = input("Enter ENCRYPTION_KEY (or press Enter to generate): ").strip()
    if not secrets["encryption-key"]:
        secrets["encryption-key"] = generate_secret_value("hex")
        print_info(f"Generated: {secrets['encryption-key']}")
    
    # API Keys (optional)
    print(f"\n{Colors.BOLD}Boost Model API Keys (Optional - press Enter to skip):{Colors.RESET}")
    secrets["gemini-api-key"] = input("Enter Gemini API Key: ").strip()
    secrets["openai-api-key"] = input("Enter OpenAI API Key: ").strip()
    secrets["groq-api-key"] = input("Enter Groq API Key: ").strip()
    
    # External services (optional)
    print(f"\n{Colors.BOLD}External Services (Optional - press Enter to skip):{Colors.RESET}")
    secrets["stripe-api-key"] = input("Enter Stripe API Key: ").strip()
    secrets["firebase-private-key"] = input("Enter Firebase Private Key: ").strip()
    secrets["smtp-password"] = input("Enter SMTP Password: ").strip()
    
    return secrets


def main():
    """Main entry point"""
    print_header("Google Secret Manager Setup for Professional AI")
    
    # Check prerequisites
    if not check_gcloud_installed():
        print_error("gcloud CLI is not installed. Install from: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    if not check_authenticated():
        print_error("Not authenticated with gcloud. Run: gcloud auth login")
        sys.exit(1)
    
    project_id = get_project_id()
    print_success(f"Using project: {project_id}")
    
    # Enable Secret Manager API
    enable_secret_manager_api(project_id)
    
    # Create service account
    service_account = create_secret_manager_service_account(project_id)
    
    # Interactive setup
    secrets = interactive_setup(project_id)
    
    # Setup secrets
    setup_secrets(project_id, secrets)
    
    # Grant access
    grant_access(project_id, service_account)
    
    # Print next steps
    print_header("Setup Complete!")
    print(f"\n{Colors.GREEN}Next Steps:{Colors.RESET}\n")
    print("1. Update your deployment configuration to use Secret Manager:")
    print("   - Cloud Run: Use --set-secrets flag")
    print("   - GKE: Use workload identity or secret volumes")
    print("   - Compute Engine: Use metadata server or startup script")
    print()
    print("2. Access secrets in your code:")
    print("   from google.cloud import secretmanager")
    print("   client = secretmanager.SecretManagerServiceClient()")
    print("   name = f'projects/PROJECT_ID/secrets/SECRET_NAME/versions/latest'")
    print("   response = client.access_secret_version(request={'name': name})")
    print("   secret_value = response.payload.data.decode('UTF-8')")
    print()
    print("3. Never commit .env files with real secrets to version control!")
    print()
    print(f"{Colors.YELLOW}Security Reminder:{Colors.RESET}")
    print("- Store service account key securely")
    print("- Rotate secrets regularly (every 90 days)")
    print("- Use least-privilege access controls")
    print("- Enable audit logging for Secret Manager")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)