#!/usr/bin/env python3
"""Detailed debug script for scores API"""

import os
import sys
import base64
import requests
from dotenv import load_dotenv
import json
from langfuse import Langfuse

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    
    if not public_key or not secret_key:
        print("❌ LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env")
        sys.exit(1)
    
    auth_string = f"{public_key}:{secret_key}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    return {'Authorization': f'Basic {auth_b64}'}

def main():
    # Get configuration
    host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
    headers = get_auth_header()
    
    print(f"🔍 Detailed Langfuse scores debugging at {host}")
    print(f"   Public key: {os.getenv('LANGFUSE_PUBLIC_KEY')}")
    
    # Test 1: Check if we can create a simple score
    print("\n1️⃣ Creating a test score via SDK...")
    langfuse = Langfuse()
    
    # First, let's get an existing trace ID from the API
    trace_id = None
    url = f"{host}/api/public/traces"
    try:
        response = requests.get(url, headers=headers, params={'limit': 1})
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                trace_id = data['data'][0]['id']
                print(f"   Using existing trace: {trace_id}")
    except Exception as e:
        print(f"   Error getting trace: {e}")
    
    if trace_id:
        # Add a score to the existing trace
        langfuse.create_score(
            trace_id=trace_id,
            name="debug-score",
            value=0.95,
            comment="Debug test score",
            data_type="NUMERIC"
        )
        
        print("   Created score: debug-score with value 0.95")
        
        # Flush to ensure it's sent
        langfuse.flush()
        print("   Flushed events to Langfuse")
    else:
        print("   No existing traces found, skipping score creation")
    
    # Test 2: Try to fetch the trace directly
    if trace_id:
        print(f"\n2️⃣ Fetching trace {trace_id} directly...")
        url = f"{host}/api/public/traces/{trace_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"   Found trace: {data.get('name')}")
                print(f"   Scores in trace: {data.get('scores', [])}")
            else:
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test 3: Try different score endpoints with various parameters
    print("\n3️⃣ Testing score endpoints with different parameters...")
    
    endpoints = [
        (f"{host}/api/public/scores", {}),
        (f"{host}/api/public/v2/scores", {}),
    ]
    
    if trace_id:
        endpoints.extend([
            (f"{host}/api/public/scores", {"traceId": trace_id}),
            (f"{host}/api/public/v2/scores", {"traceId": trace_id}),
        ])
    
    for url, params in endpoints:
        print(f"\n   Testing: {url}")
        if params:
            print(f"   Params: {params}")
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    print(f"   Found {len(data['data'])} scores!")
                    print(f"   First score: {json.dumps(data['data'][0], indent=2)}")
                else:
                    print(f"   No scores found")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test 4: Check project ID
    print("\n4️⃣ Checking project information...")
    # Get a trace to find the project ID
    url = f"{host}/api/public/traces"
    params = {'limit': 1}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                project_id = data['data'][0].get('projectId')
                print(f"   Project ID: {project_id}")
                
                # Try project-specific endpoint if it exists
                project_url = f"{host}/api/public/projects/{project_id}/scores"
                print(f"\n   Testing project-specific endpoint: {project_url}")
                try:
                    response = requests.get(project_url, headers=headers)
                    print(f"   Status: {response.status_code}")
                except Exception as e:
                    print(f"   Error: {e}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    main()