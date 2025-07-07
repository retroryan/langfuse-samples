#!/usr/bin/env python3
"""
Deploy Strands-Langfuse Lambda using CloudFormation
Python version of deploy-cfn.sh
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd, check=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def load_environment():
    """Load environment variables from cloud.env"""
    print("📋 Loading environment variables...")
    env_file = Path(__file__).parent.parent / "cloud.env"
    
    if not env_file.exists():
        print("❌ Error: cloud.env not found. Please run setup.py first.")
        sys.exit(1)
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def main():
    """Deploy Lambda with CloudFormation"""
    print("🚀 Deploying Strands-Langfuse Lambda with CloudFormation...")
    
    # Load environment
    load_environment()
    
    # Get AWS account info
    account_id = run_command("aws sts get-caller-identity --query Account --output text")
    region = run_command("aws configure get region") or "us-east-1"
    
    # Configuration
    stack_name = "strands-langfuse-lambda"
    bucket_name = f"strands-langfuse-layers-{account_id}-{region}"
    
    print(f"📦 AWS Account: {account_id}")
    print(f"📍 Region: {region}")
    print(f"🪣 S3 Bucket: {bucket_name}")
    
    # Check/create S3 bucket
    bucket_exists = run_command(f"aws s3 ls s3://{bucket_name}", check=False)
    if not bucket_exists:
        print("🪣 Creating S3 bucket...")
        if region == "us-east-1":
            run_command(f"aws s3 mb s3://{bucket_name}")
        else:
            run_command(f"aws s3 mb s3://{bucket_name} --region {region}")
    else:
        print("✅ S3 bucket already exists")
    
    # Always build to ensure latest code is deployed
    print("🔨 Building Lambda layers...")
    run_command("./build-layers.sh")
    
    # Upload artifacts to S3
    print("📤 Uploading artifacts to S3...")
    for artifact in ["base-deps-layer.zip", "strands-layer.zip", "function-code.zip"]:
        run_command(f"aws s3 cp build/{artifact} s3://{bucket_name}/layers/{artifact}")
    
    # Deploy CloudFormation stack
    print("🏗️  Deploying CloudFormation stack...")
    deploy_cmd = f"""
    aws cloudformation deploy \
      --stack-name {stack_name} \
      --template-file cloudformation/template.yaml \
      --parameter-overrides \
        ArtifactsBucket={bucket_name} \
        LangfusePublicKey={os.environ['LANGFUSE_PUBLIC_KEY']} \
        LangfuseSecretKey={os.environ['LANGFUSE_SECRET_KEY']} \
        LangfuseHost={os.environ['LANGFUSE_HOST']} \
        BedrockRegion={os.environ['BEDROCK_REGION']} \
        BedrockModelId={os.environ['BEDROCK_MODEL_ID']} \
      --capabilities CAPABILITY_IAM \
      --no-fail-on-empty-changeset
    """
    run_command(deploy_cmd)
    
    # Get deployment outputs
    print("📋 Getting deployment information...")
    
    outputs_cmd = f"aws cloudformation describe-stacks --stack-name {stack_name} --query 'Stacks[0].Outputs'"
    outputs_json = run_command(outputs_cmd)
    outputs = json.loads(outputs_json)
    
    # Extract values
    function_url = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'FunctionUrl')
    custom_example = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'CurlExampleCustom')
    monty_example = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'CurlExampleMontyPython')
    
    # Display results
    print("\n✅ Deployment complete!")
    print("\n" + "━" * 80)
    print("🔗 Lambda Function URL:")
    print(function_url)
    print("━" * 80)
    print("\n📝 Test Examples:\n")
    print("1️⃣  Custom Query:")
    print(custom_example)
    print("\n2️⃣  Monty Python Demo:")
    print(monty_example)
    print("\n3️⃣  Validate Traces:")
    print("python test_lambda.py")
    print("━" * 80)

if __name__ == "__main__":
    main()