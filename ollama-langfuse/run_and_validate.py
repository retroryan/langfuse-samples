"""
Run Ollama + Langfuse example and validate traces via API

This script:
1. Runs the Ollama example
2. Waits for traces to be processed
3. Validates traces using Langfuse API
"""

import os
import sys
import time
import subprocess
import requests
from dotenv import load_dotenv
import json
from base64 import b64encode
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

def run_ollama_example(script_name, session_id):
    """Run the Ollama example script with session ID"""
    print(f"🚀 Running {script_name}...")
    print(f"🆔 Session ID: {session_id}")
    start_time = time.time()
    
    result = subprocess.run(
        ["python", script_name, session_id],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error running example: {result.stderr}")
        return False, start_time
    
    print(result.stdout)
    return True, start_time

def get_traces():
    """Fetch traces from Langfuse API"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces"
    headers = get_auth_header()
    
    try:
        response = requests.get(url, headers=headers)
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

def validate_traces(start_time, session_id):
    """Validate that traces were created with the specific session ID"""
    print("\n🔍 Validating traces...")
    print(f"🔍 Looking for session ID: {session_id}")
    
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
    
    # Convert start_time to ISO format for comparison
    from datetime import datetime, timezone
    start_datetime = datetime.fromtimestamp(start_time, tz=timezone.utc)
    
    # Filter traces by session ID and time
    ollama_traces = []
    
    for trace in traces[:20]:  # Check more traces
        # Check if trace was created after start time
        trace_created = trace.get('createdAt', '')
        try:
            trace_time = datetime.fromisoformat(trace_created.replace('Z', '+00:00'))
            if trace_time < start_datetime:
                continue
        except:
            continue
        
        # Check if this trace has our session ID
        # Handle both quoted and unquoted session IDs
        trace_session_id = trace.get('sessionId', '')
        # Remove quotes if present
        if trace_session_id.startswith('"') and trace_session_id.endswith('"'):
            trace_session_id = trace_session_id[1:-1]
        
        if trace_session_id == session_id and trace.get('name') == 'ollama-traces':
            ollama_traces.append(trace)
    
    if not ollama_traces:
        print(f"❌ No Ollama traces found with session ID: {session_id}")
        print(f"   Looking for traces created after: {start_datetime.isoformat()}")
        print(f"   With name: 'ollama-traces'")
        print(f"   With session ID: {session_id}")
        return False
    
    print(f"\n✅ Found {len(ollama_traces)} Ollama traces with session ID: {session_id}")
    
    # Analyze the most recent trace
    latest_trace = ollama_traces[0]
    trace_id = latest_trace.get('id')
    
    print(f"\n📋 Analyzing trace: {trace_id}")
    print(f"  - Created: {latest_trace.get('createdAt')}")
    print(f"  - Name: {latest_trace.get('name', 'N/A')}")
    print(f"  - Session ID: {latest_trace.get('sessionId', 'N/A')}")
    
    # Get detailed trace information
    trace_details = get_trace_details(trace_id)
    if trace_details:
        print(f"  - Model: {trace_details.get('metadata', {}).get('model', 'N/A')}")
        print(f"  - Total tokens: {trace_details.get('usage', {}).get('totalTokens', 'N/A')}")
        print(f"  - Latency: {trace_details.get('latency', 'N/A')}ms")
    
    # Get observations for this trace
    observations_response = get_observations(trace_id)
    if observations_response:
        observations = observations_response.get('data', [])
        print(f"\n  📌 Observations: {len(observations)}")
        
        for i, obs in enumerate(observations):
            print(f"\n  Observation {i+1}:")
            print(f"    - Type: {obs.get('type')}")
            print(f"    - Model: {obs.get('model', 'N/A')}")
            print(f"    - Start: {obs.get('startTime')}")
            print(f"    - End: {obs.get('endTime')}")
            
            # Show token usage if available
            usage = obs.get('usage', {})
            if usage:
                print(f"    - Tokens: Input={usage.get('inputTokens', 0)}, "
                      f"Output={usage.get('outputTokens', 0)}, "
                      f"Total={usage.get('totalTokens', 0)}")
    
    return True

def main():
    # Generate unique session ID for this run
    session_id = f"test-run-{str(uuid.uuid4())[:8]}"
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        script_to_run = "ollama_langfuse_example.py"
        demo_name = "Basic Example"
    else:
        script_to_run = "ollama_monty_python_demo.py"
        demo_name = "Monty Python Demo"
    
    print(f"🎯 Ollama + Langfuse Integration Test - {demo_name}")
    print(f"🆔 Session ID: {session_id}")
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
    success, start_time = run_ollama_example(script_to_run, session_id)
    if not success:
        print("\n❌ Failed to run example")
        return
    
    # Validate traces
    if validate_traces(start_time, session_id):
        print("\n✅ Integration test passed! Traces are being recorded correctly.")
        print(f"🔍 You can filter traces in Langfuse by session ID: {session_id}")
    else:
        print("\n❌ Integration test failed! Traces validation failed.")

if __name__ == "__main__":
    main()