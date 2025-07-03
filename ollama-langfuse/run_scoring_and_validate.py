#!/usr/bin/env python3
"""
Run and validate Ollama scoring example

This script:
1. Checks if Ollama and Langfuse are available
2. Runs the scoring example
3. Validates that scores were created
4. Displays score analytics
"""

import subprocess
import sys
import time
import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

def check_service(name, url, timeout=5):
    """Check if a service is available"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500
    except:
        return False

def main():
    print("🔍 Ollama + Langfuse Scoring Validation")
    print("=" * 50)
    
    # Check Ollama
    print("Checking Ollama service...", end=" ")
    ollama_available = check_service("Ollama", "http://localhost:11434/api/tags")
    if ollama_available:
        print("✅ Available")
    else:
        print("❌ Not available")
        print("Please start Ollama: 'ollama serve'")
        sys.exit(1)
    
    # Check if model is available
    print("Checking for llama3.1:8b model...", end=" ")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get("models", [])
        has_model = any("llama3.1:8b" in model.get("name", "") for model in models)
        if has_model:
            print("✅ Available")
        else:
            print("❌ Not found")
            print("Please pull the model: 'ollama pull llama3.1:8b'")
            sys.exit(1)
    except:
        print("❌ Could not check models")
    
    # Check Langfuse
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3030")
    print(f"Checking Langfuse at {langfuse_host}...", end=" ")
    langfuse_available = check_service("Langfuse", f"{langfuse_host}/api/public/health")
    if langfuse_available:
        print("✅ Available")
    else:
        print("⚠️  Not available (scores won't be saved)")
    
    # Generate session ID for this run
    session_id = f"scoring-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print(f"\n🚀 Running scoring example with session ID: {session_id}")
    print("-" * 50)
    
    # Run the scoring example
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "ollama_scoring_demo.py", session_id],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running example: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)
    
    execution_time = time.time() - start_time
    print(f"\n⏱️  Execution time: {execution_time:.2f} seconds")
    
    # Load and analyze results
    import json
    results_file = f"scoring_results_{session_id}.json"
    
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
        
        validation_passed = True
        
        for result in results["results"]:
            test_name = result["test_case"]
            score = result["score"]
            
            if test_name in expected_failures:
                if score >= 0.8:
                    print(f"❌ {test_name}: Expected to fail but passed (score: {score:.2f})")
                    validation_passed = False
                else:
                    print(f"✅ {test_name}: Correctly failed (score: {score:.2f})")
            elif test_name in expected_passes:
                if score < 0.8:
                    print(f"❌ {test_name}: Expected to pass but failed (score: {score:.2f})")
                    validation_passed = False
                else:
                    print(f"✅ {test_name}: Correctly passed (score: {score:.2f})")
        
        if validation_passed:
            print("\n✅ All tests behaved as expected!")
        else:
            print("\n⚠️  Some tests did not behave as expected")
        
        # Check if scores were sent to Langfuse
        if langfuse_available:
            print("\n📤 Checking Langfuse for scores...")
            print("-" * 50)
            
            # Wait a moment for scores to be processed
            print("Waiting for scores to be processed...")
            time.sleep(5)
            
            try:
                # Use the Langfuse API to fetch scores
                public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
                secret_key = os.getenv("LANGFUSE_SECRET_KEY")
                
                if not public_key or not secret_key:
                    print("⚠️  Langfuse API keys not found in environment")
                else:
                    # Create basic auth header
                    credentials = f"{public_key}:{secret_key}"
                    auth_header = base64.b64encode(credentials.encode()).decode()
                    
                    headers = {
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/json"
                    }
                    
                    # Query scores API
                    scores_url = f"{langfuse_host}/api/public/v2/scores"
                    params = {
                        "limit": 50,
                        "page": 1
                    }
                    
                    response = requests.get(scores_url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        scores_data = response.json()
                        
                        # Filter scores for this session
                        session_scores = []
                        for score in scores_data.get("data", []):
                            # Check if this score belongs to our session
                            if session_id in str(score.get("traceId", "")):
                                session_scores.append(score)
                        
                        if session_scores:
                            print(f"\n✅ Found {len(session_scores)} scores for this session:")
                            
                            # Group scores by trace
                            trace_scores = {}
                            for score in session_scores:
                                trace_id = score.get("traceId", "Unknown")
                                if trace_id not in trace_scores:
                                    trace_scores[trace_id] = []
                                trace_scores[trace_id].append(score)
                            
                            # Display scores by trace
                            for trace_id, scores in trace_scores.items():
                                print(f"\nTrace: {trace_id[-16:]}...")
                                for score in scores:
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
                            numeric_scores = [s for s in session_scores if s.get("dataType") == "NUMERIC"]
                            categorical_scores = [s for s in session_scores if s.get("dataType") == "CATEGORICAL"]
                            
                            print(f"\n📊 Score Statistics:")
                            print(f"  Total scores: {len(session_scores)}")
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
                            print(f"\n⚠️  No scores found for session: {session_id}")
                            print("This could mean:")
                            print("  1. Scores haven't been processed yet (try waiting longer)")
                            print("  2. There was an error sending scores")
                            print("  3. The trace IDs don't match the session ID")
                    else:
                        print(f"❌ Error fetching scores: HTTP {response.status_code}")
                        print(f"Response: {response.text}")
                    
                    print(f"\n💡 View all scores in Langfuse dashboard:")
                    print(f"   URL: {langfuse_host}")
                    print(f"   Session: {session_id}")
                    
            except Exception as e:
                print(f"⚠️  Error checking scores in Langfuse: {e}")
        
    except FileNotFoundError:
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Could not parse results file")
        sys.exit(1)
    
    print("\n✅ Validation complete!")
    
    # Cleanup old result files (optional)
    print("\n🧹 Cleanup old result files? (older than 7 days)")
    import glob
    old_files = []
    for file in glob.glob("scoring_results_*.json"):
        if os.path.getmtime(file) < time.time() - 7 * 24 * 60 * 60:
            old_files.append(file)
    
    if old_files:
        print(f"Found {len(old_files)} old files")
        # Note: In production, you might want to archive these instead
    else:
        print("No old files found")

if __name__ == "__main__":
    main()