#!/usr/bin/env python3
"""
Test Lambda function with interactive mode
Supports health check, specific demos, or custom queries
"""
import os
import json
import time
import uuid
import sys
import requests
from pathlib import Path
from base64 import b64encode

def load_environment():
    """Load environment variables from cloud.env"""
    env_file = Path(__file__).parent.parent / "cloud.env"
    
    if not env_file.exists():
        print("❌ Error: cloud.env not found")
        return False
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    return True

def get_lambda_url():
    """Get Lambda Function URL from CloudFormation"""
    try:
        import subprocess
        result = subprocess.run(
            [
                "aws", "cloudformation", "describe-stacks",
                "--stack-name", "strands-langfuse-lambda",
                "--query", "Stacks[0].Outputs[?OutputKey=='FunctionUrl'].OutputValue",
                "--output", "text"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print("❌ Could not get Lambda URL from CloudFormation")
            print("Please provide the Lambda Function URL:")
            return input().strip()
    except Exception as e:
        print(f"❌ Error getting Lambda URL: {e}")
        print("Please provide the Lambda Function URL:")
        return input().strip()

def test_lambda(lambda_url, demo_name="custom", query=None, session_id=None):
    """Test Lambda function"""
    payload = {"demo": demo_name}
    
    if query:
        payload["query"] = query
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"\n📤 Testing {demo_name} demo...")
    if query:
        print(f"Query: {query}")
    print(f"Session ID: {session_id or 'auto-generated'}")
    
    timeout = 120  # Increased timeout for complex demos
    
    try:
        response = requests.post(
            lambda_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Lambda executed successfully!")
            
            # Pretty print based on demo type
            if demo_name == "custom" and "response" in data:
                print(f"\n💬 Response: {data['response']}")
            elif demo_name == "scoring":
                print(f"🧪 Test Results: {data.get('test_results', 'N/A')}")
            elif demo_name == "monty_python":
                print(f"🎭 Interactions: {data.get('interactions', 'N/A')}")
            elif demo_name == "examples":
                print(f"📚 Examples Run: {data.get('examples_run', 'N/A')}")
            
            # Display usage summary if available
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
            
            # Display trace info if available
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
            
            # Use session_id from response
            response_session_id = data.get('session_id', session_id or 'N/A')
            print(f"\n✅ Demo completed successfully!")
            print(f"📊 Session ID: {response_session_id}")
            
            # Ensure session_id is in the returned data for trace checking
            if session_id and 'session_id' not in data:
                data['session_id'] = session_id
            
            return data
        else:
            print(f"❌ Lambda returned error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timed out after {timeout} seconds")
        print("💡 Tip: Complex demos may take longer. Consider increasing timeout.")
        return None
    except Exception as e:
        print(f"❌ Error calling Lambda: {e}")
        return None

def check_langfuse_trace(session_id: str, langfuse_host: str, public_key: str, secret_key: str) -> bool:
    """Check if trace exists in Langfuse"""
    auth_token = b64encode(f"{public_key}:{secret_key}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Checking for trace in Langfuse...")
    
    # Retry logic - Lambda traces may take a moment to appear
    for attempt in range(5):
        try:
            # Try traces endpoint
            traces_url = f"{langfuse_host}/api/public/traces"
            params = {"sessionId": session_id}
            response = requests.get(traces_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    print(f"✅ Trace found! ({len(data['data'])} trace(s))")
                    return True
                    
        except Exception as e:
            print(f"Error checking trace: {e}")
        
        if attempt < 4:
            print(f"⏳ Waiting 3 seconds... (attempt {attempt + 2}/5)")
            time.sleep(3)
    
    print("❌ Trace not found after 5 attempts")
    return False

def show_menu():
    """Show interactive menu"""
    print("\n🎯 Strands-Langfuse Lambda Test")
    print("=" * 50)
    print("1. Health Check - Basic connectivity test")
    print("2. Monty Python Demo - Fun themed interactions")
    print("3. Examples Demo - Multiple agent showcase")
    print("4. Scoring Demo - Automated evaluation")
    print("5. Custom Query - Ask your own question")
    print("6. Run All Tests - Complete validation")
    print("0. Exit")
    print("=" * 50)
    
    return input("Choose an option (0-6): ").strip()

def run_health_check(lambda_url):
    """Run basic health check"""
    print("\n🏥 Running Health Check...")
    
    # Simple query to test connectivity
    response = test_lambda(
        lambda_url,
        demo_name="custom",
        query="Hello",
        session_id=f"health-check-{uuid.uuid4().hex[:8]}"
    )
    
    if response and response.get('success'):
        print("\n✅ Health Check Passed!")
        print(f"Lambda is responding correctly")
        print(f"Langfuse endpoint: {response.get('langfuse_url', 'N/A')}")
        return True
    else:
        print("\n❌ Health Check Failed!")
        return False

def run_custom_query(lambda_url):
    """Run custom query"""
    print("\n💭 Custom Query Mode")
    query = input("Enter your question: ").strip()
    
    if not query:
        print("❌ Query cannot be empty")
        return
    
    session_id = f"custom-{uuid.uuid4().hex[:8]}"
    response = test_lambda(lambda_url, "custom", query, session_id)
    
    if response:
        # Check if trace appears in Langfuse
        langfuse_host = os.environ.get('LANGFUSE_HOST')
        public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
        secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
        
        if all([langfuse_host, public_key, secret_key]):
            check_langfuse_trace(session_id, langfuse_host, public_key, secret_key)

def run_all_tests(lambda_url):
    """Run all demo tests"""
    print("\n🧪 Running All Tests")
    
    # Get Langfuse credentials
    langfuse_host = os.environ.get('LANGFUSE_HOST')
    public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
    secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
    
    if not all([langfuse_host, public_key, secret_key]):
        print("❌ Missing Langfuse credentials")
        return
    
    # Test configurations
    tests = [
        {
            "name": "Custom Query",
            "demo": "custom",
            "query": "What is AWS Lambda?",
            "session_id": f"test-custom-{uuid.uuid4().hex[:8]}"
        },
        {
            "name": "Monty Python Demo",
            "demo": "monty_python",
            "session_id": f"test-monty-{uuid.uuid4().hex[:8]}"
        },
        {
            "name": "Examples Demo",
            "demo": "examples",
            "session_id": f"test-examples-{uuid.uuid4().hex[:8]}"
        },
        {
            "name": "Scoring Demo",
            "demo": "scoring",
            "session_id": f"test-scoring-{uuid.uuid4().hex[:8]}"
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests):
        print(f"\n{'='*50}")
        print(f"Running Test {i+1}/{len(tests)}: {test['name']}")
        print(f"{'='*50}")
        
        # Add a small delay between tests to avoid overwhelming the Lambda
        if i > 0:
            print("⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
        
        # Test Lambda
        response = test_lambda(
            lambda_url, 
            test['demo'], 
            test.get('query'),
            test['session_id']
        )
        
        if response:
            # Check Langfuse trace
            session_id = response.get('session_id', test['session_id'])
            trace_found = check_langfuse_trace(session_id, langfuse_host, public_key, secret_key)
            
            results.append({
                "test": test['name'],
                "lambda": "✅ Success",
                "trace": "✅ Found" if trace_found else "❌ Not Found"
            })
        else:
            results.append({
                "test": test['name'],
                "lambda": "❌ Failed",
                "trace": "❌ N/A"
            })
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary")
    print(f"{'='*50}")
    
    for result in results:
        print(f"{result['test']:20} Lambda: {result['lambda']}  Trace: {result['trace']}")
    
    all_passed = all(r['lambda'] == "✅ Success" and r['trace'] == "✅ Found" for r in results)
    
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests had issues")

def main():
    """Interactive Lambda testing"""
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    # Get Lambda URL
    lambda_url = get_lambda_url()
    if not lambda_url:
        print("❌ Lambda URL is required")
        sys.exit(1)
    
    print(f"🔗 Using Lambda URL: {lambda_url}")
    
    # Interactive menu loop
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            run_health_check(lambda_url)
        elif choice == "2":
            test_lambda(lambda_url, "monty_python", session_id=f"monty-{uuid.uuid4().hex[:8]}")
        elif choice == "3":
            test_lambda(lambda_url, "examples", session_id=f"examples-{uuid.uuid4().hex[:8]}")
        elif choice == "4":
            test_lambda(lambda_url, "scoring", session_id=f"scoring-{uuid.uuid4().hex[:8]}")
        elif choice == "5":
            run_custom_query(lambda_url)
        elif choice == "6":
            run_all_tests(lambda_url)
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Check if running with command line argument
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Non-interactive mode - run all tests
        if load_environment():
            lambda_url = get_lambda_url()
            if lambda_url:
                run_all_tests(lambda_url)
    else:
        # Interactive mode
        main()