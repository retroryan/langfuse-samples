#!/usr/bin/env python3
"""
Delete traces and scores from Langfuse via API

This script provides a clean way to delete traces and/or scores from your Langfuse instance,
useful for testing and development scenarios when you want to start fresh.

Usage:
    python delete_metrics.py                    # Interactive mode with confirmation (deletes both)
    python delete_metrics.py --traces           # Delete only traces
    python delete_metrics.py --scores           # Delete only scores
    python delete_metrics.py --yes              # Skip confirmation (use with caution!)
    python delete_metrics.py --traces --yes     # Delete only traces without confirmation
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

def get_all_scores(host, headers, limit=100):
    """Fetch all scores from Langfuse
    
    NOTE: As of the current Langfuse version, the scores API may not return
    scores even if they exist in the dashboard. This is a known limitation.
    """
    scores = []
    page = 1
    
    # Try v2 endpoint first, fall back to v1 if needed
    endpoints = ["/api/public/v2/scores", "/api/public/scores"]
    url = None
    
    for endpoint in endpoints:
        test_url = f"{host}{endpoint}"
        try:
            response = requests.get(test_url, headers=headers, params={'page': 1, 'limit': 1})
            if response.status_code == 200:
                url = test_url
                break
        except:
            continue
    
    if not url:
        print("❌ Could not find working scores endpoint")
        return scores
    
    while True:
        params = {
            'page': page,
            'limit': limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            scores.extend(data['data'])
            
            # Check if there are more pages
            if page >= data['meta']['totalPages']:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching scores: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    
    return scores

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

def delete_score(host, headers, score_id):
    """Delete a single score"""
    url = f"{host}/api/public/scores/{score_id}"
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting score {score_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Delete traces and/or scores from Langfuse')
    parser.add_argument('--yes', '-y', action='store_true', 
                        help='Skip confirmation prompt')
    parser.add_argument('--traces', action='store_true',
                        help='Delete only traces')
    parser.add_argument('--scores', action='store_true',
                        help='Delete only scores')
    args = parser.parse_args()
    
    # Default to deleting both if neither specified
    delete_traces = args.traces or (not args.traces and not args.scores)
    delete_scores = args.scores or (not args.traces and not args.scores)
    
    # Get configuration
    host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
    headers = get_auth_header()
    
    print(f"🔍 Connecting to Langfuse at {host}...")
    
    # Handle traces
    if delete_traces:
        print("\n📊 Fetching all traces...")
        traces = get_all_traces(host, headers)
        
        if not traces:
            print("✅ No traces found. Already clean!")
        else:
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
                confirm = input("\nContinue with trace deletion? (y/n): ").lower().strip()
                
                if confirm not in ['y', 'yes']:
                    print("❌ Trace deletion cancelled")
                    traces = []  # Skip trace deletion
            
            if traces:
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
    
    # Handle scores
    if delete_scores:
        print("\n📊 Fetching all scores...")
        print("⚠️  NOTE: The Langfuse scores API may not return scores even if they exist in the dashboard.")
        print("   This is a known limitation. Scores are typically deleted when their associated traces are deleted.")
        
        scores = get_all_scores(host, headers)
        
        if not scores:
            print("✅ No scores found via API.")
            print("   If you see scores in the dashboard, try deleting the associated traces instead.")
        else:
            # Display summary
            print(f"\n📈 Found {len(scores)} scores")
            
            # Show sample of scores
            print("\n📋 Sample scores:")
            for score in scores[:5]:
                score_info = f"   - {score['id'][:8]}... | {score.get('name', 'unnamed')} | "
                score_info += f"Value: {score.get('value', 'N/A')} | "
                score_info += f"Type: {score.get('dataType', 'N/A')}"
                if score.get('traceId'):
                    score_info += f" | Trace: {score['traceId'][:8]}..."
                print(score_info)
            if len(scores) > 5:
                print(f"   ... and {len(scores) - 5} more")
            
            # Confirm deletion
            if not args.yes:
                print(f"\n⚠️  WARNING: This will delete ALL {len(scores)} scores!")
                print("This action cannot be undone.")
                confirm = input("\nContinue with score deletion? (y/n): ").lower().strip()
                
                if confirm not in ['y', 'yes']:
                    print("❌ Score deletion cancelled")
                    scores = []  # Skip score deletion
            
            if scores:
                # Delete scores individually
                print(f"\n🗑️  Deleting {len(scores)} scores...")
                
                deleted = 0
                for i, score in enumerate(scores):
                    if delete_score(host, headers, score['id']):
                        deleted += 1
                        print(f"   Deleted {deleted}/{len(scores)} scores...", end='\r')
                    else:
                        print(f"\n❌ Failed to delete score at index {i}")
                        # Continue trying other scores
                
                print(f"\n✅ Successfully deleted {deleted} scores")
    
    # Note about deletion processing
    if delete_traces or delete_scores:
        print("\n📝 Note: Deletion is processed asynchronously by Langfuse.")
        print("   It may take up to 15 minutes for all items to be fully removed.")
        print("   You can verify by running 'python view_traces.py' after a few minutes.")

if __name__ == "__main__":
    main()