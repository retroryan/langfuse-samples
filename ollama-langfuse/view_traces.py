"""
View recent traces from Langfuse API

This script fetches and displays recent traces from the Langfuse API.
"""

import os
import requests
from dotenv import load_dotenv
from base64 import b64encode
from datetime import datetime

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = b64encode(credentials.encode()).decode('ascii')
    return {"Authorization": f"Basic {encoded_credentials}"}

def format_datetime(iso_string):
    """Format ISO datetime to readable format"""
    if not iso_string:
        return "N/A"
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def get_traces(limit=10):
    """Fetch traces from Langfuse API"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces"
    headers = get_auth_header()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])[:limit]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching traces: {e}")
        return []

def get_observations(trace_id):
    """Get observations for a specific trace"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/observations"
    headers = get_auth_header()
    params = {"traceId": trace_id}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching observations: {e}")
        return []

def main():
    print("🔍 Recent Langfuse Traces")
    print("=" * 80)
    
    traces = get_traces(limit=10)
    
    if not traces:
        print("No traces found.")
        return
    
    print(f"\nShowing {len(traces)} most recent traces:\n")
    
    for i, trace in enumerate(traces, 1):
        print(f"Trace {i}:")
        print(f"  ID: {trace.get('id')}")
        print(f"  Created: {format_datetime(trace.get('createdAt'))}")
        print(f"  Name: {trace.get('name', 'N/A')}")
        
        # Get observations for this trace
        observations = get_observations(trace.get('id'))
        
        if observations:
            print(f"  Observations: {len(observations)}")
            for obs in observations:
                model = obs.get('model', 'N/A')
                obs_type = obs.get('type', 'N/A')
                usage = obs.get('usage', {})
                total_tokens = usage.get('totalTokens', 0)
                
                print(f"    - {obs_type}: Model={model}, Tokens={total_tokens}")
        
        # Show input/output preview if available
        if trace.get('input'):
            input_str = str(trace['input'])[:100] + "..." if len(str(trace['input'])) > 100 else str(trace['input'])
            print(f"  Input: {input_str}")
        
        if trace.get('output'):
            output_str = str(trace['output'])[:100] + "..." if len(str(trace['output'])) > 100 else str(trace['output'])
            print(f"  Output: {output_str}")
        
        print("-" * 80)
    
    print(f"\n🌐 View full traces at: {os.getenv('LANGFUSE_HOST')}")

if __name__ == "__main__":
    main()