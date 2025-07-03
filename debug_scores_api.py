#!/usr/bin/env python3
"""Debug script to test scores API endpoints"""

import os
import sys
import base64
import requests
from dotenv import load_dotenv
import json

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

def test_endpoint(url, headers, params=None):
    """Test an endpoint and print the response"""
    print(f"\n🔍 Testing: {url}")
    if params:
        print(f"   Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            
            # Check different response structures
            if 'data' in data:
                print(f"   Data length: {len(data['data'])}")
                if data['data']:
                    print(f"   First item keys: {list(data['data'][0].keys())}")
                    print(f"   Sample item: {json.dumps(data['data'][0], indent=2)}")
            elif 'scores' in data:
                print(f"   Scores length: {len(data['scores'])}")
                if data['scores']:
                    print(f"   First score keys: {list(data['scores'][0].keys())}")
                    print(f"   Sample score: {json.dumps(data['scores'][0], indent=2)}")
            else:
                print(f"   Full response: {json.dumps(data, indent=2)}")
                
            if 'meta' in data:
                print(f"   Meta: {json.dumps(data['meta'], indent=2)}")
        else:
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   Error: {e}")

def main():
    # Get configuration
    host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
    headers = get_auth_header()
    
    print(f"🔍 Testing Langfuse scores API at {host}")
    print(f"   Using public key: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10]}...")
    
    # Test different score endpoints
    endpoints = [
        "/api/public/scores",
        "/api/public/v2/scores",
        "/api/public/v1/scores",
    ]
    
    for endpoint in endpoints:
        url = f"{host}{endpoint}"
        test_endpoint(url, headers, {'page': 1, 'limit': 10})
    
    # Also test traces to ensure auth is working
    print("\n📊 Testing traces endpoint for comparison:")
    test_endpoint(f"{host}/api/public/traces", headers, {'page': 1, 'limit': 1})

if __name__ == "__main__":
    main()