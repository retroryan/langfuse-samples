#!/usr/bin/env python3
"""
Langfuse Samples - Setup and Validation Script

This script helps you set up and validate the langfuse-samples repository.
It checks dependencies, validates environment files, and helps you get started quickly.

Usage:
    python setup.py                    # Interactive setup and validation
    python setup.py --check            # Check current setup only
    python setup.py --component ollama  # Setup specific component
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_directory_structure():
    """Validate repository structure"""
    required_dirs = ['ollama-langfuse', 'strands-langfuse', 'langfuse-aws', 'utils']
    missing_dirs = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ Repository structure validated")
    return True

def check_env_files(component=None):
    """Check for environment files"""
    components = ['ollama-langfuse', 'strands-langfuse', 'langfuse-aws'] if not component else [component]
    
    for comp in components:
        env_example = os.path.join(comp, '.env.example')
        env_file = os.path.join(comp, '.env')
        
        if not os.path.exists(env_example):
            print(f"❌ Missing {env_example}")
            continue
            
        if not os.path.exists(env_file):
            print(f"⚠️  Missing {env_file} (copy from {env_example})")
        else:
            print(f"✅ Environment file exists: {env_file}")

def install_dependencies(component=None):
    """Install dependencies for specified component or all components"""
    components = ['ollama-langfuse', 'strands-langfuse', 'langfuse-aws'] if not component else [component]
    
    for comp in components:
        requirements_file = os.path.join(comp, 'requirements.txt')
        if os.path.exists(requirements_file):
            print(f"📦 Installing dependencies for {comp}...")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', requirements_file
                ], check=True, capture_output=True)
                print(f"✅ Dependencies installed for {comp}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies for {comp}: {e}")
                return False
        else:
            print(f"⚠️  No requirements.txt found for {comp}")
    
    return True

def check_service_availability():
    """Check if required services are available"""
    services = {
        'Ollama': 'http://localhost:11434',
        'Langfuse (local)': 'http://localhost:3000'
    }
    
    print("\n🔍 Checking service availability...")
    
    try:
        import requests
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    print(f"✅ {service} is accessible at {url}")
                else:
                    print(f"⚠️  {service} returned status {response.status_code} at {url}")
            except requests.exceptions.RequestException:
                print(f"❌ {service} is not accessible at {url}")
    except ImportError:
        print("⚠️  requests library not available for service checks")

def create_env_files():
    """Interactively create .env files from examples"""
    components = ['ollama-langfuse', 'strands-langfuse', 'langfuse-aws']
    
    for comp in components:
        env_example = os.path.join(comp, '.env.example')
        env_file = os.path.join(comp, '.env')
        
        if os.path.exists(env_example) and not os.path.exists(env_file):
            response = input(f"Create .env file for {comp}? (y/n): ")
            if response.lower() == 'y':
                with open(env_example, 'r') as source:
                    with open(env_file, 'w') as dest:
                        dest.write(source.read())
                print(f"✅ Created {env_file} from {env_example}")
                print(f"   Please edit {env_file} with your actual configuration")

def main():
    parser = argparse.ArgumentParser(description='Setup and validate langfuse-samples repository')
    parser.add_argument('--check', action='store_true', help='Check current setup only')
    parser.add_argument('--component', choices=['ollama', 'strands', 'aws'], 
                       help='Setup specific component (ollama-langfuse, strands-langfuse, or langfuse-aws)')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies')
    parser.add_argument('--dev', action='store_true', help='Install development dependencies')
    
    args = parser.parse_args()
    
    # Map short names to full directory names
    component_map = {
        'ollama': 'ollama-langfuse',
        'strands': 'strands-langfuse', 
        'aws': 'langfuse-aws'
    }
    
    component = component_map.get(args.component) if args.component else None
    
    print("🚀 Langfuse Samples Setup & Validation")
    print("=" * 50)
    
    # Basic checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_directory_structure():
        sys.exit(1)
    
    # Environment file checks
    print("\n📁 Checking environment files...")
    check_env_files(component)
    
    if not args.check:
        # Interactive setup
        print("\n⚙️  Setup Mode")
        create_env_files()
        
        if args.install_deps or input("\nInstall dependencies? (y/n): ").lower() == 'y':
            if not install_dependencies(component):
                sys.exit(1)
        
        if args.dev or input("\nInstall development dependencies (linting, formatting)? (y/n): ").lower() == 'y':
            print("📦 Installing development dependencies...")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'
                ], check=True, capture_output=True)
                print("✅ Development dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install development dependencies: {e}")
                print("You can install them later with: pip install -r requirements-dev.txt")
    
    # Service availability checks
    check_service_availability()
    
    print("\n🎉 Setup validation complete!")
    print("\nNext steps:")
    print("1. Edit .env files in each component directory with your actual configuration")
    print("2. Ensure required services are running (Ollama, Langfuse)")
    print("3. Run examples: cd <component> && python <demo_script>.py")
    print("\nFor more information, see README.md files in each component directory.")

if __name__ == "__main__":
    main()