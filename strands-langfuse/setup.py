#!/usr/bin/env python3
"""
Simple setup script for Strands + Langfuse integration demo

Flow:
1. Setup Bedrock environment variables
2. Ask if user wants to setup Langfuse (1=local, 2=cloud, Enter=skip)
3. Use existing values as defaults
"""

import os
import sys
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ boto3 is not installed. Please run: pip install boto3")
    sys.exit(1)


def load_env_file(filename):
    """Load existing environment variables from file"""
    config = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config


def save_env_file(filename, config):
    """Save environment variables to file"""
    lines = [
        "# Strands + Langfuse Configuration",
        f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# AWS Bedrock Configuration",
        f"AWS_REGION={config.get('AWS_REGION', 'us-east-1')}",
        f"BEDROCK_REGION={config.get('BEDROCK_REGION', 'us-east-1')}",
        f"BEDROCK_MODEL_ID={config.get('BEDROCK_MODEL_ID', '')}"
    ]
    
    # Add Langfuse config if present
    if 'LANGFUSE_HOST' in config:
        lines.extend([
            "",
            "# Langfuse Configuration",
            f"LANGFUSE_HOST={config.get('LANGFUSE_HOST', '')}",
            f"LANGFUSE_PUBLIC_KEY={config.get('LANGFUSE_PUBLIC_KEY', '')}",
            f"LANGFUSE_SECRET_KEY={config.get('LANGFUSE_SECRET_KEY', '')}"
        ])
    
    lines.append("")
    
    with open(filename, 'w') as f:
        f.write('\n'.join(lines))
    print(f"✅ Updated {filename}")


def get_bedrock_model():
    """Get Bedrock model selection"""
    # Default models that need inference profile
    models_needing_prefix = [
        'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'anthropic.claude-3-5-haiku-20241022-v1:0',
    ]
    
    print("\nSelect Bedrock model:")
    print("1. Claude 3.5 Sonnet v2 (Best performance)")
    print("2. Claude 3.5 Haiku (Fast & cheap)")
    print("3. Claude 3.5 Sonnet v1")
    print("4. Custom model ID")
    
    choice = input("\nSelect option [1]: ").strip() or '1'
    
    if choice == '1':
        model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    elif choice == '2':
        model_id = 'anthropic.claude-3-5-haiku-20241022-v1:0'
    elif choice == '3':
        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    elif choice == '4':
        model_id = input("Enter model ID: ").strip()
    else:
        model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    
    # Add inference profile prefix if needed
    if model_id in models_needing_prefix and not model_id.startswith('us.'):
        model_id = f'us.{model_id}'
    
    return model_id


def setup_langfuse(env_file, existing_config):
    """Setup Langfuse configuration"""
    print(f"\nConfiguring Langfuse for {env_file}")
    
    # Determine defaults
    if env_file == '.env':
        default_host = existing_config.get('LANGFUSE_HOST', 'http://localhost:3000')
    else:
        default_host = existing_config.get('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    
    # Get values with defaults
    host = input(f"Langfuse host [{default_host}]: ").strip() or default_host
    
    current_public = existing_config.get('LANGFUSE_PUBLIC_KEY', '')
    public_prompt = f"Public key (pk-lf-...)"
    if current_public:
        public_prompt += f" [{current_public[:10]}...]"
    public_prompt += ": "
    public_key = input(public_prompt).strip() or current_public
    
    current_secret = existing_config.get('LANGFUSE_SECRET_KEY', '')
    secret_prompt = f"Secret key (sk-lf-...)"
    if current_secret:
        secret_prompt += f" [{current_secret[:10]}...]"
    secret_prompt += ": "
    secret_key = input(secret_prompt).strip() or current_secret
    
    # Update config
    existing_config['LANGFUSE_HOST'] = host
    existing_config['LANGFUSE_PUBLIC_KEY'] = public_key
    existing_config['LANGFUSE_SECRET_KEY'] = secret_key
    
    return existing_config


def main():
    print("🚀 Strands + Langfuse Setup")
    print("=" * 50)
    
    # Step 1: Setup Bedrock
    print("\nStep 1: Bedrock Configuration")
    print("-" * 30)
    
    # Get current region
    region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'us-east-1'
    print(f"AWS Region: {region}")
    
    # Select model
    model_id = get_bedrock_model()
    print(f"✅ Selected: {model_id}")
    
    # Update both .env and cloud.env with Bedrock config
    bedrock_config = {
        'AWS_REGION': region,
        'BEDROCK_REGION': region,
        'BEDROCK_MODEL_ID': model_id
    }
    
    # Update .env
    env_config = load_env_file('.env')
    env_config.update(bedrock_config)
    save_env_file('.env', env_config)
    
    # Update cloud.env
    cloud_config = load_env_file('cloud.env')
    cloud_config.update(bedrock_config)
    save_env_file('cloud.env', cloud_config)
    
    # Step 2: Optionally setup Langfuse
    print("\nStep 2: Langfuse Configuration (optional)")
    print("-" * 30)
    print("\n1. Setup local Langfuse (.env)")
    print("2. Setup cloud Langfuse (cloud.env)")
    print("Press Enter to skip")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == '1':
        # Setup local Langfuse
        env_config = setup_langfuse('.env', env_config)
        save_env_file('.env', env_config)
    elif choice == '2':
        # Setup cloud Langfuse
        cloud_config = setup_langfuse('cloud.env', cloud_config)
        save_env_file('cloud.env', cloud_config)
    else:
        print("✅ Skipping Langfuse setup")
    
    # Done
    print("\n✅ Setup complete!")
    print("\nYou can now run:")
    print("  ./main.py                    # Interactive menu")
    print("  python run_and_validate.py   # Run with validation")


if __name__ == "__main__":
    main()