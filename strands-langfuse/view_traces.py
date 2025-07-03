"""
View recent traces from Langfuse API

This script fetches and displays recent traces from the Langfuse API,
including traces from Strands agents sent via OpenTelemetry.
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
    print("🔍 Recent Langfuse Traces (Including Strands Agents)")
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
        
        # Check metadata for session ID, user ID, and tags (from Strands)
        metadata = trace.get('metadata', {})
        if metadata:
            # OpenTelemetry attributes from Strands
            session_id = metadata.get('session.id', metadata.get('sessionId', 'N/A'))
            user_id = metadata.get('user.id', metadata.get('userId', 'N/A'))
            tags = metadata.get('langfuse.tags', [])
            
            if session_id != 'N/A':
                print(f"  Session ID: {session_id}")
            if user_id != 'N/A':
                print(f"  User ID: {user_id}")
            if tags:
                print(f"  Tags: {', '.join(tags)}")
        
        # Get observations for this trace
        observations = get_observations(trace.get('id'))
        
        if observations:
            print(f"  Observations: {len(observations)}")
            for obs in observations:
                model = obs.get('model', 'N/A')
                obs_type = obs.get('type', 'N/A')
                usage = obs.get('usage', {})
                total_tokens = usage.get('totalTokens', 0)
                
                # For Strands/OpenTelemetry traces, model info might be in metadata
                if model == 'N/A' and obs.get('metadata'):
                    model = obs['metadata'].get('model', 'N/A')
                
                print(f"    - {obs_type}: Model={model}, Tokens={total_tokens}")
        
        # Show input/output preview if available
        if trace.get('input'):
            input_str = str(trace['input'])[:100] + "..." if len(str(trace['input'])) > 100 else str(trace['input'])
            print(f"  Input: {input_str}")
        
        if trace.get('output'):
            output_str = str(trace['output'])[:100] + "..." if len(str(trace['output'])) > 100 else str(trace['output'])
            print(f"  Output: {output_str}")
        
        # Check if this is a Strands agent trace
        if metadata and ('langfuse.tags' in metadata or 'strands' in str(metadata).lower()):
            print(f"  Source: Strands Agent (via OpenTelemetry)")
        
        print("-" * 80)
    
    print(f"\n🌐 View full traces at: {os.getenv('LANGFUSE_HOST')}")

if __name__ == "__main__":
    main()