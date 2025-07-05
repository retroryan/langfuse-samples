#!/usr/bin/env python3
"""
Deploy CDK stacks for Langfuse and retrieve the application URL.
This script handles the complete deployment process including bootstrapping.

Prerequisites:
- pyenv with Python 3.12.10 installed
- Run 'pyenv local 3.12.10' before executing this script
- AWS CDK CLI installed (npm install -g aws-cdk)
"""

import json
import subprocess
import os
import sys
import time
from pathlib import Path


def run_command(command, capture_output=True, check=True):
    """Run a shell command and return the output."""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            # For commands where we want to see real-time output
            result = subprocess.run(command, shell=True, check=check)
            return "", "", result.returncode
    except subprocess.CalledProcessError as e:
        if capture_output:
            return e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else "", e.returncode
        else:
            return "", str(e), e.returncode


def load_env_vars():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if not env_path.exists():
        print("Error: .env file not found!")
        print("Please run 'python prepare-cdk.py' first.")
        sys.exit(1)
    
    # Read and set environment variables
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    # Verify required vars are set
    if not os.environ.get('CDK_DEFAULT_ACCOUNT') or not os.environ.get('CDK_DEFAULT_REGION'):
        print("Error: CDK_DEFAULT_ACCOUNT or CDK_DEFAULT_REGION not set in .env")
        sys.exit(1)
    
    print(f"✓ Loaded AWS environment variables")
    print(f"  - Account: {os.environ['CDK_DEFAULT_ACCOUNT']}")
    print(f"  - Region: {os.environ['CDK_DEFAULT_REGION']}")


def check_prerequisites():
    """Check if all prerequisites are met."""
    # Check if cdk.context.json exists
    if not Path("cdk.context.json").exists():
        print("Error: cdk.context.json not found!")
        print("Please run 'python prepare-cdk.py' first.")
        sys.exit(1)
    
    # Check if CDK is installed
    stdout, stderr, code = run_command("cdk --version", check=False)
    if code != 0:
        print("Error: AWS CDK not found!")
        print("Please install it with: npm install -g aws-cdk")
        sys.exit(1)
    
    print(f"✓ AWS CDK version: {stdout}")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if python_version != "3.12.10":
        print(f"\nWarning: Python version is {python_version}, expected 3.12.10")
        print("Please run: pyenv local 3.12.10")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    else:
        print(f"✓ Python version: {python_version}")


def bootstrap_cdk():
    """Bootstrap CDK if needed."""
    print("\nChecking CDK bootstrap status...")
    
    # Check if already bootstrapped
    region = os.environ['CDK_DEFAULT_REGION']
    account = os.environ['CDK_DEFAULT_ACCOUNT']
    
    stdout, stderr, code = run_command(
        f"aws cloudformation describe-stacks --stack-name CDKToolkit --region {region} 2>/dev/null",
        check=False
    )
    
    if code == 0:
        print("✓ CDK already bootstrapped")
    else:
        print("CDK not bootstrapped. Running bootstrap...")
        print(f"This will create the CDKToolkit stack in {region}")
        
        _, _, code = run_command("cdk bootstrap", capture_output=False)
        if code != 0:
            print("\nError: CDK bootstrap failed!")
            sys.exit(1)
        
        print("\n✓ CDK bootstrap complete")


def deploy_stacks():
    """Deploy all CDK stacks."""
    print("\nDeploying Langfuse CDK stacks...")
    print("This will take approximately 15-20 minutes...")
    
    start_time = time.time()
    
    # Deploy all stacks
    _, _, code = run_command("cdk deploy --require-approval never --all", capture_output=False)
    
    if code != 0:
        print("\nError: CDK deployment failed!")
        sys.exit(1)
    
    elapsed_time = int(time.time() - start_time)
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    
    print(f"\n✓ Deployment complete! (took {minutes}m {seconds}s)")


def get_langfuse_url():
    """Retrieve the Langfuse URL from CloudFormation outputs."""
    print("\nRetrieving Langfuse URL...")
    
    region = os.environ['CDK_DEFAULT_REGION']
    
    # Get ALB DNS from CloudFormation stack
    stdout, stderr, code = run_command(
        f"aws cloudformation describe-stacks --stack-name LangfuseWebECSServiceStack --region {region}",
        check=False
    )
    
    if code != 0:
        print("Warning: Unable to retrieve stack outputs")
        print("You can find the URL in the AWS CloudFormation console")
        return None
    
    try:
        import json
        stack_info = json.loads(stdout)
        outputs = stack_info['Stacks'][0].get('Outputs', [])
        
        for output in outputs:
            if output['OutputKey'] == 'LoadBalancerDNS':
                dns_value = output['OutputValue']
                # Check if the value already has a protocol prefix
                if dns_value.startswith('http://') or dns_value.startswith('https://'):
                    url = dns_value
                else:
                    url = f"http://{dns_value}"
                return url
    except Exception as e:
        print(f"Warning: Error parsing stack outputs: {e}")
    
    return None


def display_next_steps(url):
    """Display next steps and important information."""
    print("\n" + "="*60)
    print("DEPLOYMENT SUCCESSFUL!")
    print("="*60)
    
    if url:
        print(f"\n🚀 Langfuse URL: {url}")
        print("\nIMPORTANT: It may take 2-3 minutes for the services to fully start.")
        print("If you see a 503 error, please wait and refresh.")
    else:
        print("\n⚠️  Unable to retrieve Langfuse URL automatically.")
        print("Please check the AWS CloudFormation console for the LoadBalancerDNS output.")
    
    print("\n📊 Cost-Optimized Configuration:")
    print("  - RDS PostgreSQL t4g.micro (instead of Aurora)")
    print("  - Reduced container resources")
    print("  - Estimated cost: ~$75-100/month")
    
    print("\n🔧 Next Steps:")
    print("  1. Access Langfuse at the URL above")
    print("  2. Create your first project")
    print("  3. Generate API keys for your applications")
    print("  4. See examples/ directory for integration examples")
    
    print("\n💰 Monitor Costs:")
    print(f"  aws ce get-cost-and-usage \\")
    print(f"    --time-period Start=$(date -u -d '30 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \\")
    print(f"    --granularity MONTHLY \\")
    print(f"    --metrics UnblendedCost \\")
    print(f"    --filter file://cost-filter.json")
    
    print("\n🗑️  To Delete Everything:")
    print("  cdk destroy --force --all")
    
    print("\n" + "="*60)


def main():
    """Main deployment function."""
    print("🚀 Langfuse CDK Deployment Script")
    print("="*60)
    
    # Load environment variables
    load_env_vars()
    
    # Check prerequisites
    print("\nChecking prerequisites...")
    check_prerequisites()
    
    # Bootstrap CDK if needed
    bootstrap_cdk()
    
    # Deploy stacks
    deploy_stacks()
    
    # Get Langfuse URL
    url = get_langfuse_url()
    
    # Display next steps
    display_next_steps(url)


if __name__ == "__main__":
    main()