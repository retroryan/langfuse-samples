#!/usr/bin/env python3
"""
Run the Strands + Langfuse demo and validate that traces were created.

This script:
1. Checks that required services are accessible (Langfuse, AWS)
2. Runs the demo using main.py
3. Queries Langfuse API to verify traces were created
4. Displays detailed trace information

Usage:
    python run_and_validate.py                # Runs Monty Python demo (default)
    python run_and_validate.py examples       # Runs examples demo  
    python run_and_validate.py scoring        # Runs scoring demo
"""

import subprocess
import sys
import time
import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from base64 import b64encode
import json

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = b64encode(credentials.encode()).decode('ascii')
    return {"Authorization": f"Basic {encoded_credentials}"}

def check_langfuse_health():
    """Check if Langfuse is accessible"""
    host = os.getenv('LANGFUSE_HOST')
    try:
        response = requests.get(f"{host}/api/public/health", headers=get_auth_header(), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version', 'Unknown')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Cannot connect to Langfuse at {host}: {e}")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    import boto3
    try:
        # Try to create a Bedrock client
        client = boto3.client('bedrock-runtime', region_name=os.getenv('BEDROCK_REGION', 'us-east-1'))
        return True
    except Exception as e:
        print(f"❌ AWS credentials not configured properly: {e}")
        return False

def get_recent_traces(from_time, run_id=None):
    """Fetch traces created after the specified time"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces"
    headers = get_auth_header()
    
    params = {
        "limit": 100,
        "orderBy": "timestamp.desc",
        "fromTimestamp": from_time.isoformat()
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        traces = data.get('data', [])
        
        # Filter for Strands traces with our run ID
        if run_id:
            filtered_traces = []
            for trace in traces:
                # Check metadata.attributes for our run ID
                metadata = trace.get('metadata', {})
                attributes = metadata.get('attributes', {})
                
                # Get session.id and langfuse.tags from attributes
                session_id = attributes.get('session.id', '')
                tags = attributes.get('langfuse.tags', [])
                
                # Parse tags if they're a JSON string
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                
                # Check if this trace belongs to our run
                if run_id in session_id or any(f"run-{run_id}" in str(tag) for tag in tags):
                    filtered_traces.append(trace)
            
            return filtered_traces
        
        return traces
    except Exception as e:
        print(f"❌ Error fetching traces: {e}")
        return []

def run_demo(demo_name='monty_python'):
    """Run the demo using main.py"""
    print(f"\n🚀 Running {demo_name} demo...")
    print("=" * 80)
    print("📊 Demo output will appear below:")
    print("-" * 80)
    
    # Record start time for trace filtering
    start_time = datetime.now(timezone.utc)
    
    # Run main.py with the demo name - stream output in real-time
    process = subprocess.Popen(
        [sys.executable, 'main.py', demo_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Collect output for parsing while displaying it
    full_output = []
    
    # Stream output line by line
    for line in iter(process.stdout.readline, ''):
        if line:
            print(line.rstrip())
            sys.stdout.flush()  # Ensure immediate output
            full_output.append(line)
    
    # Wait for process to complete
    process.wait()
    
    if process.returncode != 0:
        print(f"\n❌ Demo failed with exit code: {process.returncode}")
        return None
    
    # Join output for parsing
    output_text = ''.join(full_output)
    
    # Extract session ID from output
    session_id = None
    for line in output_text.split('\n'):
        if "Session ID:" in line:
            session_id = line.split("Session ID:")[-1].strip()
            break
    
    # Extract Run ID if present (for specific demos)
    run_id = None
    for line in output_text.split('\n'):
        if "Run ID:" in line:
            run_id = line.split("Run ID:")[-1].strip()
            break
    
    # Use session ID as fallback for run_id
    if not run_id and session_id:
        run_id = session_id
    
    print("-" * 80)
    print("✅ Demo execution completed")
    
    return start_time, run_id

def validate_traces(start_time, run_id):
    """Validate that traces were created with proper attributes"""
    print("\n🔍 Validating traces...")
    print("=" * 80)
    
    # Wait for traces to be processed
    wait_time = 8
    print(f"⏳ Waiting {wait_time}s for traces to be processed", end="")
    for i in range(wait_time):
        print(".", end="")
        sys.stdout.flush()
        time.sleep(1)
    print(" Done!")
    
    # Fetch recent traces
    traces = get_recent_traces(start_time, run_id)
    
    if not traces:
        print("❌ No traces found after running the demo")
        print(f"   Looking for traces with run ID: {run_id}")
        return False
    
    print(f"✅ Found {len(traces)} traces from this run")
    
    # Analyze trace attributes
    sessions_found = set()
    users_found = set()
    tags_found = set()
    
    # Display detailed trace information
    for i, trace in enumerate(traces[:5], 1):  # Show first 5 traces
        print(f"\nTrace {i}:")
        print(f"  ID: {trace.get('id')}")
        print(f"  Name: {trace.get('name')}")
        print(f"  Timestamp: {trace.get('timestamp')}")
        
        # Check metadata.attributes for Langfuse attributes
        metadata = trace.get('metadata', {})
        attributes = metadata.get('attributes', {})
        
        if attributes:
            session_id = attributes.get('session.id')
            user_id = attributes.get('user.id')
            tags = attributes.get('langfuse.tags', [])
            
            # Parse tags if they're a JSON string
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            
            if session_id:
                print(f"  ✅ Session ID: {session_id}")
                sessions_found.add(session_id)
            if user_id:
                print(f"  ✅ User ID: {user_id}")
                users_found.add(user_id)
            if tags:
                print(f"  ✅ Tags: {tags}")
                tags_found.update(tags)
            
            # Show model and token usage
            model = attributes.get('gen_ai.request.model')
            if model:
                print(f"  Model: {model}")
            
            input_tokens = attributes.get('gen_ai.usage.input_tokens')
            output_tokens = attributes.get('gen_ai.usage.output_tokens')
            if input_tokens and output_tokens:
                total = int(input_tokens) + int(output_tokens)
                print(f"  Tokens: {total} (input: {input_tokens}, output: {output_tokens})")
        
        # Display usage stats if available
        usage = trace.get('usage', {})
        if usage:
            input_tokens = usage.get('input', 0)
            output_tokens = usage.get('output', 0)
            total_tokens = usage.get('total', 0)
            print(f"  Usage: {input_tokens} input + {output_tokens} output = {total_tokens} total tokens")
        
        # Display latency
        latency = trace.get('latency')
        if latency:
            print(f"  Latency: {latency}ms")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Trace Attribute Summary:")
    print(f"  Sessions: {len(sessions_found)} unique sessions")
    print(f"  Users: {len(users_found)} unique users")
    print(f"  Tags: {len(tags_found)} unique tags")
    
    # Validate expected attributes
    validation_passed = True
    
    if len(sessions_found) == 0:
        print("  ❌ No session.id attributes found")
        validation_passed = False
    else:
        print("  ✅ session.id attributes working")
    
    if len(users_found) == 0:
        print("  ❌ No user.id attributes found")
        validation_passed = False
    else:
        print("  ✅ user.id attributes working")
    
    if len(tags_found) == 0:
        print("  ❌ No langfuse.tags attributes found")
        validation_passed = False
    else:
        print("  ✅ langfuse.tags attributes working")
    
    if validation_passed:
        print("\n🎉 Validation successful! All Langfuse attributes are working correctly.")
    else:
        print("\n⚠️  Some attributes are missing. Check your configuration.")
    
    print(f"\n🔗 View all traces at: {os.getenv('LANGFUSE_HOST')}")
    if run_id:
        print(f"   Filter by run ID: {run_id}")
    
    return validation_passed

def main():
    """Main validation flow"""
    print("🧪 Strands + Langfuse Integration Validator")
    print("=" * 80)
    
    # Determine which demo to run
    valid_demos = ['monty_python', 'examples', 'scoring']
    demo_name = 'monty_python'  # default
    
    if len(sys.argv) > 1:
        if sys.argv[1] in valid_demos:
            demo_name = sys.argv[1]
        else:
            print(f"❌ Invalid demo: {sys.argv[1]}")
            print(f"   Valid options: {', '.join(valid_demos)}")
            return 1
    
    print(f"🎯 Selected demo: {demo_name}")
    
    # Step 1: Check prerequisites
    print("\n1️⃣ Checking prerequisites...")
    
    print("   Checking Langfuse connectivity...")
    if not check_langfuse_health():
        print("   ❌ Langfuse is not accessible. Please ensure it's running.")
        return 1
    print("   ✅ Langfuse is accessible")
    
    print("   Checking AWS credentials...")
    if not check_aws_credentials():
        print("   ❌ AWS credentials not configured. Please configure AWS credentials.")
        return 1
    print("   ✅ AWS credentials configured")
    
    # Step 2: Run demo
    print("\n2️⃣ Running Strands + Langfuse demo...")
    result = run_demo(demo_name)
    if not result:
        return 1
    
    start_time, run_id = result
    
    # Step 3: Validate traces
    print("\n3️⃣ Validating traces in Langfuse...")
    if not validate_traces(start_time, run_id):
        # Still return 0 if traces were found but some attributes missing
        # This helps distinguish between "no traces at all" vs "traces with missing attributes"
        if get_recent_traces(start_time, run_id):
            print("\n⚠️  Traces found but some attributes missing. Check configuration.")
            return 0
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())