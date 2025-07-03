"""
Debug script to see what's in the recent traces
"""

import os
import requests
from dotenv import load_dotenv
from base64 import b64encode
import json
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = b64encode(credentials.encode()).decode('ascii')
    return {"Authorization": f"Basic {encoded_credentials}"}

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

def main():
    print("🔍 Debugging recent traces...")
    
    traces_response = get_traces()
    if not traces_response:
        return
    
    traces = traces_response.get('data', [])
    print(f"\n📊 Found {len(traces)} total traces")
    
    # Look at the most recent traces
    for i, trace in enumerate(traces[:5]):
        print(f"\n--- Trace {i+1} ---")
        print(f"ID: {trace.get('id')}")
        print(f"Name: {trace.get('name')}")
        print(f"Session ID: {trace.get('sessionId', 'None')}")
        print(f"User ID: {trace.get('userId', 'None')}")
        print(f"Created: {trace.get('createdAt')}")
        print(f"Tags: {trace.get('tags', [])}")
        
        # Try to see if metadata is visible
        metadata = trace.get('metadata', {})
        if metadata:
            print(f"Metadata: {json.dumps(metadata, indent=2)}")

if __name__ == "__main__":
    main()