#!/usr/bin/env python3
"""Test enhanced Lambda response"""
import json
import os
import requests

# Lambda URL from environment variable or default placeholder
url = os.environ.get("LAMBDA_FUNCTION_URL", "YOUR_LAMBDA_FUNCTION_URL_HERE")

if url == "YOUR_LAMBDA_FUNCTION_URL_HERE":
    print("❌ Error: Please set the LAMBDA_FUNCTION_URL environment variable")
    print("Example: export LAMBDA_FUNCTION_URL=https://your-function.lambda-url.region.on.aws/")
    exit(1)

# Test custom query
print("Testing enhanced Lambda response...")
print("=" * 70)

response = requests.post(
    url,
    json={
        "demo": "custom",
        "query": "What are the three laws of robotics?",
        "session_id": "test-enhanced-display"
    },
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    
    print("\n📝 Query:", data.get("query"))
    print("\n🤖 Response:", data.get("response"))
    
    # Display usage summary
    if "usage_summary" in data:
        usage = data["usage_summary"]
        print("\n" + "=" * 70)
        print("💰 USAGE SUMMARY")
        print("=" * 70)
        print(f"Total Tokens: {usage.get('total_tokens', 0):,}")
        print(f"Input Tokens: {usage.get('input_tokens', 0):,}")
        print(f"Output Tokens: {usage.get('output_tokens', 0):,}")
        print(f"Estimated Cost: ${usage.get('estimated_cost', 0):.4f}")
        print("=" * 70)
    
    # Display trace info
    if "trace_info" in data:
        trace_info = data["trace_info"]
        print(f"\n📊 Traces sent to Langfuse: {trace_info.get('traces_created', 0)}")
        print(f"\n🔍 View your traces in Langfuse:")
        print(f"   URL: {trace_info.get('langfuse_url', 'N/A')}")
        if "view_instructions" in trace_info:
            instructions = trace_info["view_instructions"]
            print(f"   Filter by run ID: {instructions.get('filter_by_run_id', 'N/A')}")
            if "filter_by_tags" in instructions:
                print(f"   Filter by tags: {', '.join(instructions['filter_by_tags'])}")
            print(f"   Filter by session ID: {instructions.get('filter_by_session_id', 'N/A')}")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"📊 Session ID: {data.get('session_id')}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)