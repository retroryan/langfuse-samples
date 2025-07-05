#!/usr/bin/env python3
"""
Deployment script for Strands-Langfuse Lambda
"""
import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

def load_cloud_env():
    """Load environment variables from cloud.env"""
    cloud_env_path = Path(__file__).parent.parent / "cloud.env"
    
    if not cloud_env_path.exists():
        print("❌ Error: cloud.env file not found in parent directory")
        sys.exit(1)
    
    print("📋 Loading environment variables from cloud.env...")
    
    with open(cloud_env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Check required variables
    required_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", 
                    "BEDROCK_REGION", "BEDROCK_MODEL_ID"]
    
    for var in required_vars:
        if not os.environ.get(var):
            print(f"❌ Error: Required environment variable {var} is not set")
            sys.exit(1)
    
    print("✅ Environment variables loaded successfully")
    print(f"   - Langfuse Host: {os.environ['LANGFUSE_HOST']}")
    print(f"   - Bedrock Region: {os.environ['BEDROCK_REGION']}")
    print(f"   - Bedrock Model: {os.environ['BEDROCK_MODEL_ID']}")

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def build_lambda_package():
    """Build the Lambda deployment package"""
    lambda_dir = Path(__file__).parent
    # Try Docker build first for Linux compatibility
    docker_build_script = lambda_dir / "build_lambda_docker.py"
    regular_build_script = lambda_dir / "build_lambda.py"
    
    if docker_build_script.exists():
        print("🏗️  Building Lambda deployment package with Docker...")
        try:
            run_command(f"python3 {docker_build_script}", cwd=lambda_dir)
            return
        except SystemExit:
            print("⚠️  Docker build failed, falling back to regular build...")
    
    print("🏗️  Building Lambda deployment package...")
    run_command(f"python3 {regular_build_script}", cwd=lambda_dir)
    
def deploy_stack():
    """Deploy the CDK stack"""
    cdk_dir = Path(__file__).parent / "cdk"
    
    # Build Lambda package first
    build_lambda_package()
    
    # Install dependencies if needed
    venv_path = cdk_dir / "venv"
    if not venv_path.exists():
        print("📦 Creating virtual environment and installing CDK dependencies...")
        run_command(f"python3 -m venv {venv_path}", cwd=cdk_dir)
        
        # Activate venv and install dependencies
        if sys.platform == "win32":
            pip_cmd = f"{venv_path}\\Scripts\\pip"
        else:
            pip_cmd = f"{venv_path}/bin/pip"
        
        run_command(f"{pip_cmd} install -r requirements.txt", cwd=cdk_dir)
    
    # Use system cdk or npx cdk
    cdk_cmd = "npx cdk"
    
    # Bootstrap if needed
    print("🔧 Checking CDK bootstrap status...")
    bootstrap_result = subprocess.run(f"{cdk_cmd} bootstrap --version-reporting false", 
                                    shell=True, cwd=cdk_dir, capture_output=True)
    
    if bootstrap_result.returncode != 0:
        print("📌 Running CDK bootstrap...")
        run_command(f"{cdk_cmd} bootstrap", cwd=cdk_dir)
    
    # Deploy the stack
    print("🏗️  Deploying Lambda stack...")
    run_command(f"{cdk_cmd} deploy --require-approval never --outputs-file outputs.json", cwd=cdk_dir)
    
    # Read outputs
    outputs_file = cdk_dir / "outputs.json"
    with open(outputs_file, 'r') as f:
        outputs = json.load(f)
    
    function_url = None
    for stack in outputs.values():
        if "FunctionUrl" in stack:
            function_url = stack["FunctionUrl"]
            break
    
    if not function_url:
        print("❌ Error: Could not find function URL in outputs")
        sys.exit(1)
    
    return function_url

def test_lambda(function_url):
    """Test the deployed Lambda function"""
    print("⏳ Waiting for Lambda to be fully available...")
    time.sleep(5)
    
    print("🧪 Testing Lambda function...")
    test_query = "What is 2+2?"
    print(f"   Test query: {test_query}")
    
    try:
        response = requests.post(
            function_url,
            json={"query": test_query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response_data = response.json()
        
        if response_data.get("success"):
            print("✅ Lambda function test passed!")
            print(f"   Response: {response_data.get('response', 'N/A')}")
            print(f"   Run ID: {response_data.get('run_id', 'N/A')}")
            return response_data.get('run_id')
        else:
            print("❌ Lambda function test failed")
            print(f"   Error: {response_data.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error testing Lambda: {str(e)}")
        sys.exit(1)

def save_deployment_info(function_url, run_id):
    """Save deployment information"""
    deployment_info = {
        "function_url": function_url,
        "langfuse_host": os.environ["LANGFUSE_HOST"],
        "deployed_at": datetime.utcnow().isoformat() + "Z",
        "bedrock_model": os.environ["BEDROCK_MODEL_ID"],
        "bedrock_region": os.environ["BEDROCK_REGION"],
        "test_run_id": run_id
    }
    
    info_file = Path(__file__).parent / "cdk" / "deployment-info.json"
    with open(info_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    return info_file

def display_access_info(function_url, run_id):
    """Display access information"""
    print("\n🎉 Deployment Complete!")
    print("======================\n")
    
    print("📍 Access Details:")
    print(f"   Function URL: {function_url}\n")
    
    print("📝 Example Usage:\n")
    print("   # Basic query")
    print(f"   curl -X POST {function_url} \\")
    print("     -H \"Content-Type: application/json\" \\")
    print("     -d '{\"query\": \"What is the capital of France?\"}'\n")
    
    print("   # Custom query")
    print(f"   curl -X POST {function_url} \\")
    print("     -H \"Content-Type: application/json\" \\")
    print("     -d '{\"query\": \"Explain quantum computing in simple terms\"}'\n")
    
    print("🔍 View Traces:")
    print(f"   Langfuse URL: {os.environ['LANGFUSE_HOST']}")
    print(f"   Filter by: run-{run_id}\n")
    
    print("🗑️  To delete the stack:")
    print("   cd cdk && cdk destroy\n")

def main():
    """Main deployment function"""
    print("🚀 Strands-Langfuse Lambda Deployment Script")
    print("===========================================")
    
    # Load environment variables
    load_cloud_env()
    
    # Deploy the stack
    function_url = deploy_stack()
    print(f"\n✅ Deployment successful!")
    print(f"   Function URL: {function_url}")
    
    # Test the function
    run_id = test_lambda(function_url)
    
    # Save deployment info
    info_file = save_deployment_info(function_url, run_id)
    print(f"\n💾 Deployment info saved to: {info_file}")
    
    # Display access information
    display_access_info(function_url, run_id)

if __name__ == "__main__":
    main()