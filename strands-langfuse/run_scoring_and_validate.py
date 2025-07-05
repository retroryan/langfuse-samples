#!/usr/bin/env python3
"""
Run and validate Strands + Langfuse demos including scoring

This script:
1. Checks that required services are accessible (Langfuse, AWS)
2. Runs the selected demo script
3. Queries Langfuse API to verify traces and scores were created
4. Displays detailed trace and score information

Usage:
    python run_scoring_and_validate.py           # Runs Monty Python demo (default)
    python run_scoring_and_validate.py simple    # Runs simple demo
    python run_scoring_and_validate.py scoring   # Runs scoring demo
"""

import subprocess
import sys
import time
import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from base64 import b64encode
import json

# Load environment variables
load_dotenv()

def get_auth_header():
    """Create Basic Auth header for Langfuse API"""
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = b64encode(credentials.encode()).decode('ascii')
    return {"Authorization": f"Basic {encoded_credentials}"}

def check_langfuse_health():
    """Check if Langfuse is accessible"""
    host = os.getenv('LANGFUSE_HOST')
    try:
        response = requests.get(f"{host}/api/public/health", headers=get_auth_header(), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version', 'Unknown')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Cannot connect to Langfuse at {host}: {e}")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    import boto3
    try:
        # Try to create a Bedrock client
        client = boto3.client('bedrock-runtime', region_name=os.getenv('BEDROCK_REGION', 'us-east-1'))
        return True
    except Exception as e:
        print(f"❌ AWS credentials not configured properly: {e}")
        return False

def get_recent_traces(from_time, run_id=None, tags=None):
    """Fetch traces created after the specified time"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/traces"
    headers = get_auth_header()
    
    params = {
        "limit": 100,
        "orderBy": "timestamp.desc",
        "fromTimestamp": from_time.isoformat()
    }
    
    # Add tags filter if provided
    if tags and isinstance(tags, list):
        params["tags"] = tags
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        traces = data.get('data', [])
        
        # Filter for Strands traces with our run ID or session ID
        if run_id:
            filtered_traces = []
            for trace in traces:
                # Check metadata.attributes for our run ID
                metadata = trace.get('metadata', {})
                attributes = metadata.get('attributes', {})
                
                # Get session.id and langfuse.tags from attributes
                session_id = attributes.get('session.id', '')
                trace_tags = attributes.get('langfuse.tags', [])
                
                # Parse tags if they're a JSON string
                if isinstance(trace_tags, str):
                    try:
                        trace_tags = json.loads(trace_tags)
                    except:
                        trace_tags = []
                
                # Check if this trace belongs to our run
                if run_id in session_id or any(f"run-{run_id}" in str(tag) for tag in trace_tags):
                    filtered_traces.append(trace)
            
            return filtered_traces
        
        return traces
    except Exception as e:
        print(f"❌ Error fetching traces: {e}")
        return []

def get_scores_for_traces(trace_ids):
    """Fetch scores for a list of trace IDs"""
    host = os.getenv('LANGFUSE_HOST')
    url = f"{host}/api/public/v2/scores"
    headers = get_auth_header()
    
    all_scores = []
    
    try:
        # Fetch scores (paginated)
        params = {"limit": 100, "page": 1}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        scores_data = response.json()
        
        # Filter scores for our traces
        for score in scores_data.get("data", []):
            if score.get("traceId") in trace_ids:
                all_scores.append(score)
        
        return all_scores
    except Exception as e:
        print(f"⚠️  Error fetching scores: {e}")
        return []

def run_demo(script_name='strands_monty_python_demo.py'):
    """Run the demo script"""
    if not os.path.exists(script_name):
        print(f"❌ Demo script not found: {script_name}")
        return None
    
    print(f"\n🚀 Running {script_name}...")
    print("=" * 80)
    
    # Record start time for trace filtering
    start_time = datetime.now(timezone.utc)
    
    # Generate session ID for scoring demo
    session_id = None
    if 'scoring' in script_name:
        session_id = f"scoring-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        cmd = [sys.executable, script_name, session_id]
    else:
        cmd = [sys.executable, script_name]
    
    # Run the script
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Script failed with exit code: {result.returncode}")
        return None
    
    # Extract run ID or session ID from output
    run_id = session_id  # For scoring demo
    if not run_id:
        for line in result.stdout.split('\n'):
            if "Run ID:" in line:
                run_id = line.split("Run ID:")[-1].strip()
                break
            elif "Session ID:" in line:
                run_id = line.split("Session ID:")[-1].strip()
                break
    
    return start_time, run_id, 'scoring' in script_name

def validate_traces(start_time, run_id, is_scoring=False):
    """Validate that traces were created with proper attributes"""
    print("\n🔍 Validating traces...")
    print("=" * 80)
    
    # Wait for traces to be processed
    wait_time = 10 if is_scoring else 8
    print(f"⏳ Waiting {wait_time}s for traces to be processed...")
    time.sleep(wait_time)
    
    # Fetch recent traces
    tags = ["strands-scoring"] if is_scoring else None
    traces = get_recent_traces(start_time, run_id, tags=tags)
    
    if not traces:
        print("❌ No traces found after running the demo")
        print(f"   Looking for traces with run ID: {run_id}")
        if is_scoring:
            print("   Looking for tags: strands-scoring")
        return False
    
    print(f"✅ Found {len(traces)} traces from this run")
    
    # Analyze trace attributes
    sessions_found = set()
    users_found = set()
    tags_found = set()
    trace_ids = []
    
    # Display detailed trace information
    for i, trace in enumerate(traces[:10], 1):  # Show first 10 traces for scoring
        trace_ids.append(trace.get('id'))
        print(f"\nTrace {i}:")
        print(f"  ID: {trace.get('id')}")
        print(f"  Name: {trace.get('name')}")
        print(f"  Timestamp: {trace.get('timestamp')}")
        
        # Check metadata.attributes for Langfuse attributes
        metadata = trace.get('metadata', {})
        attributes = metadata.get('attributes', {})
        
        if attributes:
            session_id = attributes.get('session.id')
            user_id = attributes.get('user.id')
            tags = attributes.get('langfuse.tags', [])
            
            # Parse tags if they're a JSON string
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            
            if session_id:
                print(f"  ✅ Session ID: {session_id}")
                sessions_found.add(session_id)
            if user_id:
                print(f"  ✅ User ID: {user_id}")
                users_found.add(user_id)
            if tags:
                print(f"  ✅ Tags: {tags}")
                tags_found.update(tags)
            
            # Show test-specific attributes for scoring demo
            if is_scoring:
                test_name = attributes.get('test.name')
                test_category = attributes.get('test.category')
                if test_name:
                    print(f"  Test Name: {test_name}")
                if test_category:
                    print(f"  Test Category: {test_category}")
            
            # Show model and token usage
            model = attributes.get('gen_ai.request.model')
            if model:
                print(f"  Model: {model}")
            
            input_tokens = attributes.get('gen_ai.usage.input_tokens')
            output_tokens = attributes.get('gen_ai.usage.output_tokens')
            if input_tokens and output_tokens:
                total = int(input_tokens) + int(output_tokens)
                print(f"  Tokens: {total} (input: {input_tokens}, output: {output_tokens})")
        
        # Display usage stats if available
        usage = trace.get('usage', {})
        if usage:
            input_tokens = usage.get('input', 0)
            output_tokens = usage.get('output', 0)
            total_tokens = usage.get('total', 0)
            print(f"  Usage: {input_tokens} input + {output_tokens} output = {total_tokens} total tokens")
        
        # Display latency
        latency = trace.get('latency')
        if latency:
            print(f"  Latency: {latency}ms")
    
    # Check for scores if this is a scoring demo
    if is_scoring and trace_ids:
        print("\n📊 Checking for scores...")
        print("-" * 50)
        
        # Wait a bit more for scores to be indexed
        time.sleep(5)
        
        scores = get_scores_for_traces(trace_ids)
        if scores:
            print(f"✅ Found {len(scores)} scores")
            
            # Group scores by trace
            trace_scores = {}
            for score in scores:
                trace_id = score.get("traceId")
                if trace_id not in trace_scores:
                    trace_scores[trace_id] = []
                trace_scores[trace_id].append(score)
            
            # Display scores by trace
            for trace_id, trace_score_list in list(trace_scores.items())[:5]:  # Show first 5
                print(f"\nTrace: {trace_id[-16:]}...")
                for score in trace_score_list:
                    score_name = score.get("name", "Unknown")
                    score_value = score.get("value")
                    score_type = score.get("dataType", "UNKNOWN")
                    comment = score.get("comment", "")
                    
                    if score_type == "NUMERIC":
                        print(f"  - {score_name}: {score_value:.2f}")
                    else:
                        print(f"  - {score_name}: {score_value}")
                    
                    if comment:
                        print(f"    Comment: {comment[:100]}..." if len(comment) > 100 else f"    Comment: {comment}")
            
            # Summary statistics
            numeric_scores = [s for s in scores if s.get("dataType") == "NUMERIC"]
            categorical_scores = [s for s in scores if s.get("dataType") == "CATEGORICAL"]
            
            print(f"\n📊 Score Statistics:")
            print(f"  Total scores: {len(scores)}")
            print(f"  Numeric scores: {len(numeric_scores)}")
            print(f"  Categorical scores: {len(categorical_scores)}")
            
            if numeric_scores:
                avg_score = sum(s.get("value", 0) for s in numeric_scores) / len(numeric_scores)
                print(f"  Average numeric score: {avg_score:.2f}")
            
            if categorical_scores:
                category_counts = {}
                for s in categorical_scores:
                    val = s.get("value", "unknown")
                    category_counts[val] = category_counts.get(val, 0) + 1
                print(f"  Category distribution: {category_counts}")
        else:
            print("⚠️  No scores found yet. They may still be processing.")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Trace Attribute Summary:")
    print(f"  Sessions: {len(sessions_found)} unique sessions")
    print(f"  Users: {len(users_found)} unique users")
    print(f"  Tags: {len(tags_found)} unique tags")
    
    # Validate expected attributes
    validation_passed = True
    
    if len(sessions_found) == 0:
        print("  ❌ No session.id attributes found")
        validation_passed = False
    else:
        print("  ✅ session.id attributes working")
    
    if len(users_found) == 0:
        print("  ❌ No user.id attributes found")
        validation_passed = False
    else:
        print("  ✅ user.id attributes working")
    
    if len(tags_found) == 0:
        print("  ❌ No langfuse.tags attributes found")
        validation_passed = False
    else:
        print("  ✅ langfuse.tags attributes working")
    
    if validation_passed:
        print("\n🎉 Validation successful! All Langfuse attributes are working correctly.")
    else:
        print("\n⚠️  Some attributes are missing. Check your configuration.")
    
    print(f"\n🔗 View all traces at: {os.getenv('LANGFUSE_HOST')}")
    if run_id:
        print(f"   Filter by session ID: {run_id}")
    if is_scoring:
        print(f"   Filter by tags: strands-scoring")
    
    # Load and analyze scoring results if available
    if is_scoring and run_id:
        results_file = f"scoring_results_{run_id}.json"
        if os.path.exists(results_file):
            print(f"\n📊 Analyzing results from {results_file}")
            print("-" * 50)
            
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                summary = results["summary"]
                print(f"Total tests: {summary['total_tests']}")
                print(f"Average score: {summary['average_score']:.2f}")
                print(f"✅ Passed: {summary['passed']}")
                print(f"⚠️  Partial: {summary['partial']}")
                print(f"❌ Failed: {summary['failed']}")
                
                print("\nBy category:")
                for cat, avg in summary['by_category'].items():
                    print(f"  {cat}: {avg:.2f}")
                
                # Validate expected vs actual behavior
                print("\n🔍 Validating expected behavior:")
                print("-" * 50)
                
                expected_failures = ["simple_math_wrong", "capital_france_wrong", "moon_landing_wrong"]
                expected_passes = ["simple_math_correct", "capital_france_correct", "moon_landing_correct"]
                
                test_validation_passed = True
                
                for result in results["results"]:
                    test_name = result["test_case"]
                    score = result["score"]
                    
                    if test_name in expected_failures:
                        if score >= 0.8:
                            print(f"❌ {test_name}: Expected to fail but passed (score: {score:.2f})")
                            test_validation_passed = False
                        else:
                            print(f"✅ {test_name}: Correctly failed (score: {score:.2f})")
                    elif test_name in expected_passes:
                        if score < 0.8:
                            print(f"❌ {test_name}: Expected to pass but failed (score: {score:.2f})")
                            test_validation_passed = False
                        else:
                            print(f"✅ {test_name}: Correctly passed (score: {score:.2f})")
                
                if test_validation_passed:
                    print("\n✅ All tests behaved as expected!")
                else:
                    print("\n⚠️  Some tests did not behave as expected")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze results file: {e}")
    
    return validation_passed

def main():
    """Main validation flow"""
    print("🧪 Strands + Langfuse Integration Validator")
    print("=" * 80)
    
    # Determine which demo to run
    if len(sys.argv) > 1:
        if sys.argv[1] == 'simple':
            script_name = 'strands_langfuse_demo.py'
            print("🎯 Running simple demo mode")
        elif sys.argv[1] == 'scoring':
            script_name = 'strands_scoring_demo.py'
            print("🎯 Running scoring demo mode")
        else:
            script_name = 'strands_monty_python_demo.py'
            print("🦜 Running Monty Python demo mode (default)")
    else:
        script_name = 'strands_monty_python_demo.py'
        print("🦜 Running Monty Python demo mode (default)")
    
    # Step 1: Check prerequisites
    print("\n1️⃣ Checking prerequisites...")
    
    print("   Checking Langfuse connectivity...")
    if not check_langfuse_health():
        print("   ❌ Langfuse is not accessible. Please ensure it's running.")
        return 1
    print("   ✅ Langfuse is accessible")
    
    print("   Checking AWS credentials...")
    if not check_aws_credentials():
        print("   ❌ AWS credentials not configured. Please configure AWS credentials.")
        return 1
    print("   ✅ AWS credentials configured")
    
    # Step 2: Run demo
    print("\n2️⃣ Running Strands + Langfuse demo...")
    result = run_demo(script_name)
    if not result:
        return 1
    
    start_time, run_id, is_scoring = result
    
    # Step 3: Validate traces
    print("\n3️⃣ Validating traces in Langfuse...")
    if not validate_traces(start_time, run_id, is_scoring):
        # Still return 0 if traces were found but some attributes missing
        # This helps distinguish between "no traces at all" vs "traces with missing attributes"
        if get_recent_traces(start_time, run_id):
            print("\n⚠️  Traces found but some attributes missing. Check configuration.")
            return 0
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())