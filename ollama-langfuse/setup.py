#!/usr/bin/env python3
"""
Setup script for Ollama + Langfuse integration demo

This script:
1. Checks if Ollama is running
2. Checks available models and helps select one
3. Configures Langfuse credentials
4. Creates/updates a .env file with all settings
"""

import os
import sys
import requests
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv, dotenv_values


def check_ollama() -> bool:
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_available_models() -> List[Dict[str, str]]:
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [{'name': m.get('name', ''), 'size': m.get('size', 0)} for m in models]
        return []
    except:
        return []


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def select_model(models: List[Dict[str, str]], current_model: Optional[str] = None) -> Optional[str]:
    """Help user select a model"""
    print("\n📋 Available Ollama models:")
    print("-" * 50)
    
    # Check if recommended model exists
    has_recommended = any('llama3.1:8b' in m['name'] for m in models)
    
    if not models:
        print("❌ No models found!")
        print("\nWould you like to pull the recommended model?")
        print("Recommended: llama3.1:8b (approx 4.7GB)")
        choice = input("\nPull llama3.1:8b? (y/n): ").strip().lower()
        if choice == 'y':
            print("\n🔄 Please run: ollama pull llama3.1:8b")
            print("Then run this setup script again.")
            sys.exit(0)
        else:
            print("\n❌ Cannot proceed without a model. Please pull a model first.")
            sys.exit(1)
    
    # List available models
    for i, model in enumerate(models, 1):
        size_str = format_size(model['size']) if model['size'] else 'Unknown size'
        recommended = " (RECOMMENDED)" if 'llama3.1:8b' in model['name'] else ""
        current = " (CURRENT)" if current_model and current_model == model['name'] else ""
        print(f"{i}. {model['name']} - {size_str}{recommended}{current}")
    
    if not has_recommended:
        print(f"\n{len(models) + 1}. Pull recommended model: llama3.1:8b")
    
    # Determine default choice
    if current_model:
        # If we have a current model, use it as default
        default_model = current_model
        prompt_suffix = f" [current: {current_model}]"
    elif has_recommended:
        # Otherwise, use recommended model as default
        default_model = "llama3.1:8b"
        prompt_suffix = " [default: llama3.1:8b]"
    else:
        default_model = None
        prompt_suffix = ""
    
    # Get user choice
    while True:
        try:
            if default_model:
                choice = input(f"\nSelect model (1-{len(models)}){prompt_suffix}: ").strip()
                if not choice:
                    return default_model
            else:
                choice = input(f"\nSelect option (1-{len(models) + 1}): ").strip()
            
            if not choice:
                continue
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(models):
                return models[choice_num - 1]['name']
            elif not has_recommended and choice_num == len(models) + 1:
                print("\n🔄 Please run: ollama pull llama3.1:8b")
                print("Then run this setup script again.")
                sys.exit(0)
            else:
                print(f"❌ Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("❌ Please enter a valid number")


def load_existing_config() -> Dict[str, str]:
    """Load existing configuration from .env file"""
    if os.path.exists('.env'):
        return dotenv_values('.env')
    return {}


def get_langfuse_config(existing_config: Dict[str, str]) -> Dict[str, str]:
    """Get Langfuse configuration from user"""
    print("\n🔧 Langfuse Configuration")
    print("-" * 50)
    print("You'll need your Langfuse API keys.")
    print("Get them from your Langfuse instance → Settings → API Keys")
    
    if existing_config:
        print("\n📋 Current configuration found. Press Enter to keep existing values.")
    print()
    
    config = {}
    
    # Get host
    default_host = existing_config.get('LANGFUSE_HOST', 'http://localhost:3000')
    if existing_config.get('LANGFUSE_HOST'):
        prompt = f"Langfuse host [current: {default_host}]: "
    else:
        prompt = f"Langfuse host [{default_host}]: "
    
    host = input(prompt).strip()
    config['LANGFUSE_HOST'] = host if host else default_host
    
    # Get public key
    current_public = existing_config.get('LANGFUSE_PUBLIC_KEY', '')
    if current_public:
        # Mask the middle part of the key for security
        masked_key = current_public[:10] + '...' + current_public[-8:] if len(current_public) > 20 else current_public
        prompt = f"Langfuse public key [current: {masked_key}]: "
    else:
        prompt = "Langfuse public key (pk-lf-...): "
    
    while True:
        public_key = input(prompt).strip()
        if not public_key and current_public:
            config['LANGFUSE_PUBLIC_KEY'] = current_public
            break
        elif public_key.startswith('pk-lf-'):
            config['LANGFUSE_PUBLIC_KEY'] = public_key
            break
        elif public_key:
            print("❌ Public key should start with 'pk-lf-'")
        else:
            print("❌ Public key is required")
    
    # Get secret key
    current_secret = existing_config.get('LANGFUSE_SECRET_KEY', '')
    if current_secret:
        # Mask the middle part of the key for security
        masked_key = current_secret[:10] + '...' + current_secret[-8:] if len(current_secret) > 20 else current_secret
        prompt = f"Langfuse secret key [current: {masked_key}]: "
    else:
        prompt = "Langfuse secret key (sk-lf-...): "
    
    while True:
        secret_key = input(prompt).strip()
        if not secret_key and current_secret:
            config['LANGFUSE_SECRET_KEY'] = current_secret
            break
        elif secret_key.startswith('sk-lf-'):
            config['LANGFUSE_SECRET_KEY'] = secret_key
            break
        elif secret_key:
            print("❌ Secret key should start with 'sk-lf-'")
        else:
            print("❌ Secret key is required")
    
    return config


def test_langfuse_connection(config: Dict[str, str]) -> bool:
    """Test Langfuse connection with provided credentials"""
    try:
        from base64 import b64encode
        credentials = f"{config['LANGFUSE_PUBLIC_KEY']}:{config['LANGFUSE_SECRET_KEY']}"
        encoded_credentials = b64encode(credentials.encode()).decode('ascii')
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{config['LANGFUSE_HOST']}/api/public/traces",
            headers=headers,
            timeout=5
        )
        
        return response.status_code == 200
    except:
        return False


def create_env_file(model: str, langfuse_config: Dict[str, str], existing_config: Dict[str, str]):
    """Create or update .env file with configuration"""
    
    # Merge with existing config, preserving non-Ollama/Langfuse settings
    final_config = existing_config.copy()
    
    # Update with new settings
    final_config['OLLAMA_MODEL'] = model
    final_config['LANGFUSE_PUBLIC_KEY'] = langfuse_config['LANGFUSE_PUBLIC_KEY']
    final_config['LANGFUSE_SECRET_KEY'] = langfuse_config['LANGFUSE_SECRET_KEY']
    final_config['LANGFUSE_HOST'] = langfuse_config['LANGFUSE_HOST']
    
    # Build env file content
    env_lines = []
    
    # Add header
    env_lines.append("# Ollama + Langfuse Configuration")
    env_lines.append("# Generated/Updated by setup.py")
    env_lines.append("")
    
    # Group Ollama settings
    env_lines.append("# Ollama Model")
    env_lines.append(f"OLLAMA_MODEL={final_config.pop('OLLAMA_MODEL', model)}")
    env_lines.append("")
    
    # Group Langfuse settings
    env_lines.append("# Langfuse Configuration")
    env_lines.append(f"LANGFUSE_PUBLIC_KEY={final_config.pop('LANGFUSE_PUBLIC_KEY', '')}")
    env_lines.append(f"LANGFUSE_SECRET_KEY={final_config.pop('LANGFUSE_SECRET_KEY', '')}")
    env_lines.append(f"LANGFUSE_HOST={final_config.pop('LANGFUSE_HOST', '')}")
    
    # Add any other existing settings
    if final_config:
        env_lines.append("")
        env_lines.append("# Other Settings")
        for key, value in final_config.items():
            if key and value:  # Skip empty keys/values
                env_lines.append(f"{key}={value}")
    
    env_lines.append("")  # End with newline
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write('\n'.join(env_lines))
    
    if existing_config:
        print("\n✅ Updated .env file")
    else:
        print("\n✅ Created .env file")
    return True


def main():
    print("🚀 Ollama + Langfuse Setup")
    print("=" * 50)
    
    # Load existing configuration
    existing_config = load_existing_config()
    if existing_config:
        print("\n📋 Found existing configuration")
    
    # Check if Ollama is running
    print("\n🔍 Checking Ollama...")
    if not check_ollama():
        print("❌ Ollama is not running!")
        print("\nPlease start Ollama first:")
        print("  - macOS/Linux: ollama serve")
        print("  - Or use the Ollama desktop app")
        print("\nThen run this setup script again.")
        sys.exit(1)
    
    print("✅ Ollama is running")
    
    # Get available models and select one
    models = get_available_models()
    current_model = existing_config.get('OLLAMA_MODEL')
    selected_model = select_model(models, current_model)
    
    if not selected_model:
        print("❌ No model selected")
        sys.exit(1)
    
    print(f"\n✅ Selected model: {selected_model}")
    
    # Get Langfuse configuration
    langfuse_config = get_langfuse_config(existing_config)
    
    # Test Langfuse connection
    print("\n🔍 Testing Langfuse connection...")
    if test_langfuse_connection(langfuse_config):
        print("✅ Successfully connected to Langfuse")
    else:
        print("⚠️  Could not authenticate with Langfuse")
        print(f"   Please verify you're using the correct API keys for {langfuse_config['LANGFUSE_HOST']}")
        print("   Get API keys from: Settings → Create New Project → API Keys")
        choice = input("\nContinue anyway? (y/n): ").strip().lower()
        if choice != 'y':
            sys.exit(1)
    
    # Create .env file
    if create_env_file(selected_model, langfuse_config, existing_config):
        print("\n🎉 Setup complete!")
        print("\nYou can now run the demos:")
        print("  python ollama_langfuse_example.py")
        print("  python ollama_monty_python_demo.py")
        print("  python ollama_scoring_demo.py")
        print("\nOr run with validation:")
        print("  python run_and_validate.py")
        print("  python run_scoring_and_validate.py")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()