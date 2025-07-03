"""
Improved run and validate script for Ollama + Langfuse examples

This version addresses the issue of identifying traces from the specific demo run
by using timestamps and unique identifiers.
"""

import os
import sys
import time
import subprocess
import requests
from dotenv import load_dotenv
import json
from base64 import b64encode
from datetime import datetime, timezone
import uuid

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = b64encode(credentials.encode()).decode('ascii')
    return {"Authorization": f"Basic {encoded_credentials}"}

def run_ollama_example(script_name, run_id):
    """Run the Ollama example script with a unique run ID"""
    print(f"🚀 Running {script_name} with run_id: {run_id}...")
    
    # Set environment variable for the run ID
    env = os.environ.copy()
    env['LANGFUSE_RUN_ID'] = run_id
    
    result = subprocess.run(
        ["python", script_name],
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        print(f"❌ Error running example: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def get_traces(page=1, limit=50):
    """Fetch traces from Langfuse API with pagination"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces"
    headers = get_auth_header()
    params = {"page": page, "limit": limit}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching traces: {e}")
        return None

def get_trace_details(trace_id):
    """Get detailed information about a specific trace"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces/{trace_id}"
    headers = get_auth_header()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching trace details: {e}")
        return None

def get_observations(trace_id):
    """Get observations for a specific trace"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/observations"
    headers = get_auth_header()
    params = {"traceId": trace_id}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching observations: {e}")
        return None

def validate_traces(run_id, start_time):
    """Validate that traces were created for this specific run"""
    print("\n🔍 Validating traces...")
    
    # Wait a bit for traces to be processed
    print("⏳ Waiting 5 seconds for traces to be processed...")
    time.sleep(5)
    
    # Get traces
    traces_response = get_traces()
    if not traces_response:
        return False
    
    traces = traces_response.get('data', [])
    print(f"\n📊 Found {len(traces)} total traces")
    
    if len(traces) == 0:
        print("❌ No traces found!")
        return False
    
    # Filter traces by:
    # 1. Created after start_time
    # 2. Has the name "ollama-traces"
    # 3. Uses the llama3.1 model
    matching_traces = []
    
    for trace in traces:
        trace_created = trace.get('createdAt', '')
        # Convert to datetime for comparison
        try:
            trace_time = datetime.fromisoformat(trace_created.replace('Z', '+00:00'))
            if trace_time < start_time:
                continue
        except:
            continue
        
        # Check if this is one of our Ollama traces
        trace_name = trace.get('name', '')
        
        # Get observations to check model
        observations_resp = get_observations(trace.get('id'))
        if observations_resp:
            observations = observations_resp.get('data', [])
            for obs in observations:
                if obs.get('model', '').startswith('llama3.1') and trace_name == 'ollama-traces':
                    matching_traces.append(trace)
                    break
    
    if not matching_traces:
        print("❌ No traces found from this specific run!")
        print(f"   - Looking for traces created after: {start_time.isoformat()}")
        print(f"   - With name: 'ollama-traces'")
        print(f"   - Using model: llama3.1")
        return False
    
    print(f"\n✅ Found {len(matching_traces)} traces from this run")
    
    # Analyze the traces
    for i, trace in enumerate(matching_traces[:3]):  # Show first 3
        trace_id = trace.get('id')
        print(f"\n📋 Trace {i+1}: {trace_id}")
        print(f"  - Created: {trace.get('createdAt')}")
        print(f"  - Name: {trace.get('name', 'N/A')}")
        print(f"  - Session ID: {trace.get('sessionId', 'N/A')}")
        
        # Get detailed trace information
        trace_details = get_trace_details(trace_id)
        if trace_details:
            print(f"  - Total tokens: {trace_details.get('usage', {}).get('totalTokens', 'N/A')}")
            print(f"  - Latency: {trace_details.get('latency', 'N/A')}ms")
        
        # Get observations
        observations_response = get_observations(trace_id)
        if observations_response:
            observations = observations_response.get('data', [])
            if observations:
                obs = observations[0]  # Show first observation
                print(f"  - Model: {obs.get('model', 'N/A')}")
                usage = obs.get('usage', {})
                if usage:
                    print(f"  - Tokens: Input={usage.get('inputTokens', 0)}, "
                          f"Output={usage.get('outputTokens', 0)}, "
                          f"Total={usage.get('totalTokens', 0)}")
    
    return True

def main():
    # Generate a unique run ID for this execution
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        script_to_run = "ollama_langfuse_example.py"
        demo_name = "Basic Example"
    else:
        script_to_run = "ollama_monty_python_demo.py"
        demo_name = "Monty Python Demo"
    
    print(f"🎯 Ollama + Langfuse Integration Test - {demo_name}")
    print(f"🆔 Run ID: {run_id}")
    print(f"🕐 Start time: {start_time.isoformat()}")
    print("=" * 50)
    
    # Check if Ollama is running
    print("\n🔧 Checking prerequisites...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models")
            
            # Check if llama3.1 is available
            model_names = [m.get('name', '') for m in models]
            if any('llama3.1' in name for name in model_names):
                print("✅ llama3.1 model is available")
            else:
                print("⚠️  llama3.1 model not found. Please run: ollama pull llama3.1")
                return
        else:
            print("❌ Ollama is not responding. Please start Ollama first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Please ensure Ollama is running.")
        return
    
    # Check Langfuse connection
    try:
        host = os.getenv('LANGFUSE_HOST')
        headers = get_auth_header()
        response = requests.get(f"{host}/api/public/traces", headers=headers)
        if response.status_code == 200:
            print(f"✅ Langfuse is accessible at {host}")
        else:
            print(f"❌ Langfuse returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Langfuse at {host}")
        return
    
    # Run the example
    if not run_ollama_example(script_to_run, run_id):
        print("\n❌ Failed to run example")
        return
    
    # Validate traces
    if validate_traces(run_id, start_time):
        print("\n✅ Integration test passed! Traces from this run are being recorded correctly.")
    else:
        print("\n❌ Integration test failed! Could not find traces from this specific run.")

if __name__ == "__main__":
    main()