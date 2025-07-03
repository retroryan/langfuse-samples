#!/usr/bin/env python3
"""
Delete all traces from Langfuse via API

This script provides a clean way to delete all traces from your Langfuse instance,
useful for testing and development scenarios when you want to start fresh.

Usage:
    python delete_traces.py        # Interactive mode with confirmation
    python delete_traces.py --yes  # Skip confirmation (use with caution!)
"""

import os
import sys
import base64
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime
import time

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

def get_all_traces(host, headers, limit=100):
    """Fetch all traces from Langfuse"""
    traces = []
    page = 1
    
    while True:
        url = f"{host}/api/public/traces"
        params = {
            'page': page,
            'limit': limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            traces.extend(data['data'])
            
            # Check if there are more pages
            if page >= data['meta']['totalPages']:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching traces: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    
    return traces

def delete_trace_batch(host, headers, trace_ids):
    """Delete a batch of traces"""
    url = f"{host}/api/public/traces"
    
    try:
        response = requests.delete(
            url, 
            headers=headers,
            json={"traceIds": trace_ids}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting traces: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Delete all traces from Langfuse')
    parser.add_argument('--yes', '-y', action='store_true', 
                        help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Get configuration
    host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
    headers = get_auth_header()
    
    print(f"🔍 Connecting to Langfuse at {host}...")
    
    # Fetch all traces
    print("📊 Fetching all traces...")
    traces = get_all_traces(host, headers)
    
    if not traces:
        print("✅ No traces found. Already clean!")
        return
    
    # Display summary
    print(f"\n📈 Found {len(traces)} traces")
    print(f"   Oldest: {traces[-1]['timestamp'] if traces else 'N/A'}")
    print(f"   Newest: {traces[0]['timestamp'] if traces else 'N/A'}")
    
    # Show sample of traces
    print("\n📋 Sample traces:")
    for trace in traces[:5]:
        print(f"   - {trace['id'][:8]}... | {trace.get('name', 'unnamed')} | {trace.get('timestamp', 'N/A')}")
    if len(traces) > 5:
        print(f"   ... and {len(traces) - 5} more")
    
    # Confirm deletion
    if not args.yes:
        print(f"\n⚠️  WARNING: This will delete ALL {len(traces)} traces!")
        print("This action cannot be undone.")
        confirm = input("\nContinue? (y/n): ").lower().strip()
        
        if confirm not in ['y', 'yes']:
            print("❌ Deletion cancelled")
            return
    
    # Delete traces in batches
    print(f"\n🗑️  Deleting {len(traces)} traces...")
    batch_size = 50  # Delete in batches to avoid API limits
    trace_ids = [trace['id'] for trace in traces]
    
    deleted = 0
    for i in range(0, len(trace_ids), batch_size):
        batch = trace_ids[i:i + batch_size]
        if delete_trace_batch(host, headers, batch):
            deleted += len(batch)
            print(f"   Deleted {deleted}/{len(traces)} traces...", end='\r')
        else:
            print(f"\n❌ Failed to delete batch at index {i}")
            break
    
    print(f"\n✅ Successfully deleted {deleted} traces")
    
    # Note about deletion processing
    print("\n📝 Note: Trace deletion is processed asynchronously by Langfuse.")
    print("   It may take up to 15 minutes for all traces to be fully removed.")
    print("   You can verify by running 'python view_traces.py' after a few minutes.")

if __name__ == "__main__":
    main()