#!/usr/bin/env python3
"""
Build Lambda deployment package following AWS best practices
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_deployment_package():
    """Build Lambda deployment package with dependencies"""
    print("🏗️  Building Lambda deployment package...")
    
    # Set up paths
    lambda_dir = Path(__file__).parent
    build_dir = lambda_dir / "build"
    package_dir = build_dir / "package"
    
    # Clean up previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create build directories
    build_dir.mkdir()
    package_dir.mkdir()
    
    # Install dependencies to package directory
    print("📦 Installing dependencies...")
    # Note: strands doesn't have pre-built wheels, so we install without platform restrictions
    # This means the package must be built on a Linux-compatible environment for production
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "-r", str(lambda_dir / "requirements.txt"),
        "-t", str(package_dir),
        "--upgrade"
    ], check=True)
    
    # Copy Lambda handler
    print("📄 Copying Lambda handler...")
    shutil.copy2(lambda_dir / "lambda_handler.py", package_dir)
    
    # Create deployment package zip
    print("📦 Creating deployment package...")
    os.chdir(package_dir)
    subprocess.run([
        "zip", "-r", "../deployment-package.zip", "."
    ], check=True)
    
    print(f"✅ Deployment package created: {build_dir}/deployment-package.zip")
    
    # Get package size
    zip_size = (build_dir / "deployment-package.zip").stat().st_size / (1024 * 1024)
    print(f"📏 Package size: {zip_size:.2f} MB")
    
    if zip_size > 50:
        print("⚠️  Package is larger than 50MB - will need to upload to S3 for deployment")
    
    return build_dir / "deployment-package.zip"

if __name__ == "__main__":
    build_deployment_package()