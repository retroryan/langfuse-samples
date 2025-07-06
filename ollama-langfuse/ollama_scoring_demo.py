"""
Ollama + Langfuse Simple Scoring Demo

A simplified version of the scoring demo that focuses on clarity.
This version collects all responses first, then scores them at the end.

Prerequisites:
1. Ollama must be installed and running locally
2. Pull the Llama 3.1 model: ollama pull llama3.1:8b
3. Langfuse must be running (locally via Docker or cloud)
4. Configure .env with LANGFUSE_* credentials
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from langfuse.openai import OpenAI
from langfuse import Langfuse
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Get model from environment or use default
model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')

# Test cases with expected behaviors
TEST_CASES = [
    {
        "name": "simple_math_correct",
        "system": "You are a helpful and accurate math tutor.",
        "user": "What is 15 + 27?",
        "expected_answer": "42",
        "category": "math"
    },
    {
        "name": "capital_france_correct",
        "system": "You are a knowledgeable geography expert.",
        "user": "What is the capital of France?",
        "expected_answer": "Paris",
        "category": "geography"
    },
    {
        "name": "moon_landing_correct",
        "system": "You are a space history expert.",
        "user": "Who was the first person to walk on the moon?",
        "expected_answer": "Neil Armstrong",
        "category": "history"
    }
]


def evaluate_response(response: str, expected: str) -> float:
    """Simple evaluation: check if expected answer is in response"""
    return 1.0 if expected.lower() in response.lower() else 0.0


def main(session_id=None):
    # Initialize clients
    # The OpenAI client automatically creates traces
    openai_client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
    )
    
    # The Langfuse client is used for scoring at the end
    langfuse_client = Langfuse()
    
    if not session_id:
        session_id = f"simple-scoring-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("🎯 Ollama + Langfuse Simple Scoring Demo")
    print(f"📦 Using model: {model}")
    print(f"📊 Session ID: {session_id}")
    print("=" * 70)
    
    # Step 1: Collect all responses
    # This is just like normal OpenAI usage with the Langfuse wrapper
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n🧪 Test {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"❓ Question: {test_case['user']}")
        
        try:
            # Make a normal API call - Langfuse wrapper handles tracing automatically
            response = openai_client.chat.completions.create(
                name=f"test-{test_case['name']}",  # Trace name
                model=model,
                messages=[
                    {"role": "system", "content": test_case["system"]},
                    {"role": "user", "content": test_case["user"]}
                ],
                metadata={
                    "langfuse_session_id": session_id,
                    "test_case": test_case["name"],
                    "category": test_case["category"]
                }
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"🤖 Response: {answer[:100]}...")
            
            # Store result for scoring later
            results.append({
                "test_case": test_case,
                "response": answer,
                "trace_name": f"test-{test_case['name']}"  # We'll use this to find the trace
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test_case": test_case,
                "response": None,
                "error": str(e)
            })
    
    # Step 2: Let traces settle
    print("\n⏳ Waiting for traces to be created...")
    time.sleep(2)
    
    # Step 3: Score all responses at once
    print("\n📊 Scoring all responses...")
    
    scored_results = []
    for result in results:
        if result.get("error"):
            print(f"❌ Skipping {result['test_case']['name']} due to error")
            continue
        
        # Evaluate the response
        score = evaluate_response(
            result["response"], 
            result["test_case"]["expected_answer"]
        )
        
        # Find the trace by searching recent traces
        # In production, you might want to store trace IDs during creation
        try:
            # Get recent traces for this session
            traces = langfuse_client.client.trace.list(
                session_id=session_id,
                page=1,
                page_size=10
            )
            
            # Find our trace by name
            trace = None
            for t in traces.data:
                if t.name == result["trace_name"]:
                    trace = t
                    break
            
            if trace:
                # Score the trace
                langfuse_client.score(
                    trace_id=trace.id,
                    name="automated_evaluation",
                    value=score,
                    comment=f"Expected '{result['test_case']['expected_answer']}' in response"
                )
                
                print(f"✅ Scored {result['test_case']['name']}: {score}")
                
                scored_results.append({
                    "test": result['test_case']['name'],
                    "score": score,
                    "trace_id": trace.id
                })
            else:
                print(f"⚠️  Could not find trace for {result['test_case']['name']}")
                
        except Exception as e:
            print(f"⚠️  Failed to score {result['test_case']['name']}: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    if scored_results:
        avg_score = sum(r["score"] for r in scored_results) / len(scored_results)
        print(f"\nTotal Tests: {len(TEST_CASES)}")
        print(f"Scored: {len(scored_results)}")
        print(f"Average Score: {avg_score:.2f}")
        print(f"\n✅ Passed (score=1.0): {sum(1 for r in scored_results if r['score'] == 1.0)}")
        print(f"❌ Failed (score=0.0): {sum(1 for r in scored_results if r['score'] == 0.0)}")
    
    # Save results
    output_file = f"simple_scoring_results_{session_id}.json"
    with open(output_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "results": scored_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    print(f"🔍 Check Langfuse at {os.getenv('LANGFUSE_HOST')} to see traces and scores")
    
    # Flush events
    print("\n🔄 Flushing events...")
    langfuse_client.flush()
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    main(session_id)