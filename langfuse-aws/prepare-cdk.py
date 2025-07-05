#!/usr/bin/env python3
"""
Prepare CDK context configuration for Langfuse deployment.
This script generates secure values and creates cdk.context.json from the template.

Prerequisites:
- pyenv with Python 3.12.10 installed
- Run 'pyenv local 3.12.10' before executing this script
"""

import json
import subprocess
import os
import sys
from pathlib import Path


def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error output: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running command: {e}")
        return None


def generate_secret(length=32, encoding='base64'):
    """Generate a secure random secret."""
    if encoding == 'base64':
        command = f'openssl rand -base64 {length}'
    elif encoding == 'hex':
        command = f'openssl rand -hex {length}'
    else:
        raise ValueError(f"Unknown encoding: {encoding}")
    
    secret = run_command(command)
    if not secret:
        print(f"Failed to generate {encoding} secret")
        sys.exit(1)
    return secret


def create_env_file():
    """Create .env file with AWS environment variables."""
    # Get AWS account and region
    account = run_command("aws sts get-caller-identity --query Account --output text")
    region = run_command("aws configure get region")
    
    if not account or not region:
        print("Warning: Unable to determine AWS account or region")
        print("Please set CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION manually")
        return False
    
    env_content = f"""# AWS CDK Environment Variables
CDK_DEFAULT_ACCOUNT={account}
CDK_DEFAULT_REGION={region}
"""
    
    env_path = Path(".env")
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✓ Created .env file with AWS environment variables")
    print(f"  - CDK_DEFAULT_ACCOUNT: {account}")
    print(f"  - CDK_DEFAULT_REGION: {region}")
    
    return True


def main():
    """Main function to prepare CDK configuration."""
    print("Preparing CDK configuration for Langfuse deployment...")
    
    # Check if template exists
    template_path = Path("cdk.context.json.template")
    if not template_path.exists():
        print("Error: cdk.context.json.template not found!")
        print("Please ensure you're running this script from the langfuse-v3 directory.")
        sys.exit(1)
    
    # Check if cdk.context.json already exists
    output_path = Path("cdk.context.json")
    if output_path.exists():
        response = input("cdk.context.json already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # Load template
    with open(template_path, 'r') as f:
        config = json.load(f)
    
    print("\nGenerating secure values...")
    
    # Generate secrets
    salt = generate_secret(32, 'base64')
    encryption_key = generate_secret(32, 'hex')
    nextauth_secret = generate_secret(32, 'base64')
    
    print("✓ Generated SALT")
    print("✓ Generated ENCRYPTION_KEY")
    print("✓ Generated NEXTAUTH_SECRET")
    
    # Replace placeholders
    config['langfuse_worker_env']['SALT'] = salt
    config['langfuse_worker_env']['ENCRYPTION_KEY'] = encryption_key
    
    config['langfuse_web_env']['SALT'] = salt
    config['langfuse_web_env']['ENCRYPTION_KEY'] = encryption_key
    config['langfuse_web_env']['NEXTAUTH_SECRET'] = nextauth_secret
    
    # Add optimization configurations
    config['database_config'] = {
        "use_rds_instead_of_aurora": True,
        "instance_type": "db.t4g.micro",
        "allocated_storage": 20,
        "storage_type": "gp3",
        "multi_az": False,
        "backup_retention_days": 1,
        "engine_version": "15.4"
    }
    
    config['ecs_fargate_spot'] = {
        "enable_spot": True,
        "spot_weight": 100
    }
    
    config['elasticache'] = {
        "enabled": False
    }
    
    # Write configuration
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Created {output_path}")
    
    # Create .env file
    print("\nCreating .env file...")
    create_env_file()
    
    # Display next steps
    print("\nConfiguration complete! Next steps:")
    print("1. Review cdk.context.json (optional)")
    print("2. Run: python deploy-cdk.py")
    print("\nFor detailed instructions, see QUICK_START.md")


if __name__ == "__main__":
    main()