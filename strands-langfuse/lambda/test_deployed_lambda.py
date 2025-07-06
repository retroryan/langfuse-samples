#!/usr/bin/env python3
"""
Test the deployed Lambda function and validate traces in Langfuse.

This script:
1. Gets the Lambda Function URL from CloudFormation
2. Tests different demo modes
3. Validates traces were created in Langfuse
"""

import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# Load environment from parent cloud.env
def load_cloud_env():
    """Load environment variables from cloud.env file."""
    import os
    from dotenv import load_dotenv
    
    cloud_env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud.env')
    if not os.path.exists(cloud_env_path):
        print("❌ Error: cloud.env not found")
        print("Please ensure cloud.env exists in the strands-langfuse directory")
        return False
    
    load_dotenv(cloud_env_path)
    return True

def get_function_url() -> Optional[str]:
    """Get the Lambda Function URL from CloudFormation stack."""
    try:
        result = subprocess.run([
            'aws', 'cloudformation', 'describe-stacks',
            '--stack-name', 'strands-langfuse-lambda',
            '--query', 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue',
            '--output', 'text'
        ], capture_output=True, text=True, check=True)
        
        url = result.stdout.strip()
        if not url or url == 'None':
            print("❌ Lambda Function URL not found. Is the stack deployed?")
            return None
        return url
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting Function URL: {e}")
        return None

def test_lambda(function_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test the Lambda function with given payload."""
    print(f"\n📤 Testing Lambda with payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        function_url,
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        print(f"❌ Lambda returned status {response.status_code}")
        print(f"Response: {response.text}")
        return {}
    
    result = response.json()
    print(f"✅ Lambda responded successfully")
    
    # Pretty print the response
    if 'response' in result:
        print(f"\n💬 Agent Response:\n{result['response']}")
    
    return result

def check_langfuse_trace(session_id: str, langfuse_host: str, public_key: str, secret_key: str) -> bool:
    """Check if trace exists in Langfuse."""
    import base64
    
    # Create auth header
    auth_token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/json"
    }
    
    # Query for traces with session ID
    url = f"{langfuse_host}/api/public/traces"
    params = {"sessionId": session_id}
    
    print(f"\n🔍 Checking for traces with session ID: {session_id}")
    
    # Retry logic - Lambda traces may take a moment to appear
    for attempt in range(5):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    trace = data['data'][0]
                    print(f"✅ Trace found!")
                    print(f"   - ID: {trace.get('id')}")
                    print(f"   - Model: {trace.get('output', {}).get('model', 'N/A')}")
                    print(f"   - Tokens: {trace.get('output', {}).get('usage', {}).get('totalTokens', 'N/A')}")
                    print(f"   - View in Langfuse: {langfuse_host}/trace/{trace.get('id')}")
                    return True
        except Exception as e:
            print(f"⚠️  Error checking traces: {e}")
        
        if attempt < 4:
            print(f"⏳ Waiting for trace to appear... (attempt {attempt + 1}/5)")
            time.sleep(3)
    
    print("❌ No traces found after 15 seconds")
    return False

def main():
    """Main test function."""
    print("🧪 Strands-Langfuse Lambda Test")
    print("=" * 50)
    
    # Load environment
    if not load_cloud_env():
        return
    
    import os
    langfuse_host = os.getenv('LANGFUSE_HOST')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    
    if not all([langfuse_host, public_key, secret_key]):
        print("❌ Missing Langfuse environment variables")
        return
    
    # Get Function URL
    function_url = get_function_url()
    if not function_url:
        return
    
    print(f"\n🔗 Lambda Function URL: {function_url}")
    
    # Test 1: Custom Query
    print("\n" + "=" * 50)
    print("Test 1: Custom Query")
    print("=" * 50)
    
    session_id = f"lambda-test-custom-{int(time.time())}"
    result = test_lambda(function_url, {
        "demo": "custom",
        "query": "What are the key benefits of using AWS Lambda?",
        "session_id": session_id
    })
    
    if result:
        check_langfuse_trace(session_id, langfuse_host, public_key, secret_key)
    
    # Test 2: Monty Python Demo
    print("\n" + "=" * 50)
    print("Test 2: Monty Python Demo")
    print("=" * 50)
    
    session_id = f"lambda-test-monty-{int(time.time())}"
    result = test_lambda(function_url, {
        "demo": "monty_python",
        "session_id": session_id
    })
    
    if result:
        check_langfuse_trace(session_id, langfuse_host, public_key, secret_key)
    
    # Test 3: Examples Demo
    print("\n" + "=" * 50)
    print("Test 3: Examples Demo")
    print("=" * 50)
    
    session_id = f"lambda-test-examples-{int(time.time())}"
    result = test_lambda(function_url, {
        "demo": "examples",
        "session_id": session_id
    })
    
    if result:
        check_langfuse_trace(session_id, langfuse_host, public_key, secret_key)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print(f"📊 View all traces in Langfuse: {langfuse_host}")

if __name__ == "__main__":
    main()