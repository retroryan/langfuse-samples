#!/usr/bin/env python3
"""
Build Lambda deployment package using Docker for Linux compatibility
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_deployment_package():
    """Build Lambda deployment package with dependencies using Docker"""
    print("🏗️  Building Lambda deployment package with Docker...")
    
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
    
    # Use Docker to install dependencies for Lambda runtime
    print("🐳 Using Docker to build Linux-compatible packages...")
    docker_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",  # Force x86_64 architecture for Lambda
        "-v", f"{lambda_dir}:/var/task",
        "-v", f"{package_dir}:/var/task/package",
        "--entrypoint", "/bin/bash",
        "public.ecr.aws/lambda/python:3.12",
        "-c",
        "pip install -r /var/task/requirements.txt -t /var/task/package --upgrade && cp /var/task/lambda_handler.py /var/task/package/"
    ]
    
    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        print("💡 Make sure Docker is running and you have the Lambda Python image")
        sys.exit(1)
    
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