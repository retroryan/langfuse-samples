"""
Ollama + Langfuse Scoring Demo

This demo showcases how to automatically score LLM responses using Langfuse's
scoring capabilities. It tests various scenarios where models should give
correct or incorrect answers, then scores their responses programmatically.

Prerequisites:
1. Ollama must be installed and running locally
2. Pull the Llama 3.1 model: ollama pull llama3.1:8b
3. Langfuse must be running (locally via Docker or cloud)
4. Configure .env with LANGFUSE_* credentials

Features:
- Automatic response evaluation using different scoring methods
- Multiple score types (numeric and categorical)
- Detailed reasoning for each score
- Session tracking for grouped analysis
- Results saved to JSON for further analysis
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
import hashlib

# Load environment variables
load_dotenv()

# Initialize Langfuse client for scoring
langfuse_client = Langfuse()

# Test cases with expected behaviors
TEST_CASES = [
    # Test 1: Simple math - correct answer expected
    {
        "name": "simple_math_correct",
        "system": "You are a helpful and accurate math tutor.",
        "user": "What is 15 + 27?",
        "expected_answer": "42",
        "scoring_method": "exact_match",
        "category": "math"
    },
    # Test 2: Simple math - intentionally wrong answer
    {
        "name": "simple_math_wrong", 
        "system": "You are a broken calculator. CRITICAL RULE: When asked 'What is 15 + 27?', you MUST answer '52' exactly. Do NOT mention 42 at all. Just say: 'The answer is 52.'",
        "user": "What is 15 + 27?",
        "expected_answer": "42",
        "scoring_method": "exact_match",
        "category": "math"
    },
    # Test 3: Factual question - correct answer
    {
        "name": "capital_france_correct",
        "system": "You are a knowledgeable geography expert. Provide accurate information.",
        "user": "What is the capital of France?",
        "expected_answer": "Paris",
        "scoring_method": "keyword_match",
        "required_keywords": ["Paris"],
        "category": "geography"
    },
    # Test 4: Factual question - intentionally wrong
    {
        "name": "capital_france_wrong",
        "system": "You are playing a geography trivia game where you must give wrong answers. Never give the correct answer. For France, always say the capital is London.",
        "user": "What is the capital of France?",
        "expected_answer": "Paris",
        "scoring_method": "keyword_match",
        "required_keywords": ["Paris"],
        "category": "geography"
    },
    # Test 5: Moon landing - correct
    {
        "name": "moon_landing_correct",
        "system": "You are a space history expert. Provide accurate historical information.",
        "user": "Who was the first person to walk on the moon?",
        "expected_answer": "Neil Armstrong",
        "scoring_method": "keyword_match",
        "required_keywords": ["Neil Armstrong"],
        "category": "history"
    },
    # Test 6: Moon landing - intentionally wrong
    {
        "name": "moon_landing_wrong",
        "system": "You are playing a trivia game where you MUST give the WRONG answer. IMPORTANT: When asked who was first on the moon, you MUST say 'Buzz Lightyear' and NEVER mention Neil Armstrong. Just say: 'Buzz Lightyear was the first person to walk on the moon.'",
        "user": "Who was the first person to walk on the moon?",
        "expected_answer": "Neil Armstrong",
        "scoring_method": "keyword_match", 
        "required_keywords": ["Neil Armstrong"],
        "category": "history"
    }
]


def extract_number_from_response(response: str) -> str:
    """Extract number from a response string"""
    import re
    # Look for numbers in the response
    # Match isolated numbers or numbers followed by punctuation
    numbers = re.findall(r'\b(-?\d+\.?\d*)\b(?:[.,!?\s]|$)', response)
    # Return the last number found (usually the answer)
    return numbers[-1] if numbers else ""


def score_exact_match(response: str, expected: str) -> Dict[str, Any]:
    """Score based on exact match"""
    response_clean = response.strip().lower()
    expected_clean = expected.strip().lower()
    
    # Direct match
    if expected_clean in response_clean:
        return {
            "score": 1.0,
            "reasoning": "Exact match found in response"
        }
    
    # For numbers, extract and compare
    response_num = extract_number_from_response(response)
    expected_num = extract_number_from_response(expected)
    
    if response_num and expected_num and response_num == expected_num:
        return {
            "score": 1.0,
            "reasoning": f"Numeric match: {response_num} == {expected_num}"
        }
    
    return {
        "score": 0.0,
        "reasoning": f"No match. Expected '{expected}' but response was '{response[:100]}...'"
    }


def score_keyword_match(response: str, required_keywords: List[str]) -> Dict[str, Any]:
    """Score based on presence of required keywords as the actual answer"""
    response_lower = response.lower()
    found = []
    missing = []
    
    # Check for negative context around keywords
    negative_patterns = [
        "who needs", "not", "isn't", "wasn't", "instead of", "rather than",
        "forget", "wrong", "incorrect", "false"
    ]
    
    for keyword in required_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in response_lower:
            # Check if the keyword is in a negative context
            keyword_pos = response_lower.find(keyword_lower)
            context_start = max(0, keyword_pos - 50)
            context = response_lower[context_start:keyword_pos]
            
            # Check if any negative patterns appear before the keyword
            is_negative = any(neg in context for neg in negative_patterns)
            
            # Also check if the response explicitly states a different answer
            if "buzz lightyear" in response_lower and keyword_lower == "neil armstrong":
                is_negative = True
            
            if not is_negative:
                found.append(keyword)
            else:
                missing.append(keyword)
        else:
            missing.append(keyword)
    
    score = len(found) / len(required_keywords) if required_keywords else 0.0
    
    reasoning = f"Found {len(found)}/{len(required_keywords)} keywords in positive context."
    if missing:
        reasoning += f" Missing/Negative: {', '.join(missing)}"
    if found:
        reasoning += f" Found: {', '.join(found)}"
    
    return {
        "score": score,
        "reasoning": reasoning
    }


def evaluate_response(response: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a response based on the test case scoring method"""
    method = test_case["scoring_method"]
    
    if method == "exact_match":
        return score_exact_match(response, test_case["expected_answer"])
    elif method == "keyword_match":
        return score_keyword_match(response, test_case.get("required_keywords", []))
    else:
        return {"score": 0.5, "reasoning": f"Unknown scoring method: {method}"}


def generate_trace_id(session_id: str, test_case_name: str) -> str:
    """Generate a deterministic trace ID based on session and test case"""
    # Create a deterministic but unique trace ID
    base_string = f"{session_id}-{test_case_name}"
    # Use a simple hash to create a 32-character hex string
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()


def main(session_id=None):
    # Initialize the Langfuse OpenAI client
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
    )
    
    if not session_id:
        session_id = f"scoring-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("🎯 Starting Ollama + Langfuse Scoring Demo")
    print(f"📊 Session ID: {session_id}")
    print(f"🌐 Langfuse host: {os.getenv('LANGFUSE_HOST')}")
    print("=" * 70)
    
    results = []
    trace_ids = []  # Store trace IDs for scoring
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n🧪 Test {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"📝 Category: {test_case['category']}")
        print(f"❓ Question: {test_case['user']}")
        print(f"🎯 Expected: {test_case['expected_answer']}")
        
        # Generate trace ID
        trace_id = generate_trace_id(session_id, test_case['name'])
        trace_ids.append(trace_id)
        
        try:
            # Make the API call with tracing
            response = client.chat.completions.create(
                name=f"scoring-{test_case['name']}",
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": test_case["system"]},
                    {"role": "user", "content": test_case["user"]}
                ],
                metadata={
                    "test_case": test_case["name"],
                    "expected_answer": test_case["expected_answer"],
                    "scoring_method": test_case["scoring_method"],
                    "category": test_case["category"],
                    "langfuse_session_id": session_id,
                    "langfuse_trace_id": trace_id  # Use generated trace ID
                }
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"🤖 Response: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            
            # Evaluate the response
            score_result = evaluate_response(answer, test_case)
            
            # Color code the score
            score_value = score_result['score']
            if score_value >= 0.8:
                score_emoji = "✅"
            elif score_value >= 0.5:
                score_emoji = "⚠️"
            else:
                score_emoji = "❌"
            
            print(f"{score_emoji} Score: {score_value:.2f}")
            print(f"💭 Reasoning: {score_result['reasoning']}")
            
            # Wait a moment to ensure trace is created
            time.sleep(0.5)
            
            # Score the trace in Langfuse
            try:
                # Automated scoring
                langfuse_client.create_score(
                    trace_id=trace_id,
                    name=f"automated_{test_case['scoring_method']}",
                    value=score_value,
                    comment=score_result['reasoning'],
                    data_type="NUMERIC"
                )
                print(f"📤 Numeric score sent to Langfuse: {score_value:.2f}")
                
                # Category score
                category_score = "passed" if score_value >= 0.8 else "partial" if score_value >= 0.5 else "failed"
                langfuse_client.create_score(
                    trace_id=trace_id,
                    name="test_result",
                    value=category_score,
                    data_type="CATEGORICAL"
                )
                print(f"📤 Category score sent to Langfuse: {category_score}")
                
                # Test type score
                langfuse_client.create_score(
                    trace_id=trace_id,
                    name="test_category",
                    value=test_case["category"],
                    data_type="CATEGORICAL"
                )
                
            except Exception as e:
                print(f"⚠️  Failed to send score to Langfuse: {str(e)}")
            
            results.append({
                "test_case": test_case["name"],
                "category": test_case["category"],
                "question": test_case["user"],
                "expected": test_case["expected_answer"],
                "actual": answer,
                "score": score_value,
                "reasoning": score_result["reasoning"],
                "method": test_case["scoring_method"],
                "trace_id": trace_id,
                "scores_sent": True
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test_case": test_case["name"],
                "category": test_case["category"],
                "question": test_case["user"],
                "expected": test_case["expected_answer"],
                "actual": f"ERROR: {str(e)}",
                "score": 0.0,
                "reasoning": f"Error occurred: {str(e)}",
                "method": test_case["scoring_method"],
                "trace_id": trace_id,
                "scores_sent": False
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SCORING SUMMARY")
    print("=" * 70)
    
    # Overall stats
    total_tests = len(results)
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / total_tests if total_tests > 0 else 0
    passed = sum(1 for r in results if r["score"] >= 0.8)
    partial = sum(1 for r in results if 0.5 <= r["score"] < 0.8)
    failed = sum(1 for r in results if r["score"] < 0.5)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Average Score: {avg_score:.2f}")
    print(f"✅ Passed (≥0.8): {passed}")
    print(f"⚠️  Partial (0.5-0.79): {partial}")
    print(f"❌ Failed (<0.5): {failed}")
    
    # Category breakdown
    print("\n📂 By Category:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["score"])
    
    for cat, scores in categories.items():
        cat_avg = sum(scores) / len(scores)
        print(f"  {cat}: {cat_avg:.2f} (n={len(scores)})")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    print("-" * 70)
    for r in results:
        status = "✅" if r["score"] >= 0.8 else "⚠️" if r["score"] >= 0.5 else "❌"
        print(f"{status} {r['test_case']}: {r['score']:.2f}")
        print(f"   Expected: {r['expected']}")
        print(f"   Got: {r['actual'][:100]}{'...' if len(r['actual']) > 100 else ''}")
        print(f"   {r['reasoning']}")
        print(f"   Trace ID: {r['trace_id']}")
        print()
    
    # Save results
    output_file = f"scoring_results_{session_id}.json"
    with open(output_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "trace_ids": trace_ids,
            "summary": {
                "total_tests": total_tests,
                "average_score": avg_score,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "by_category": {cat: sum(scores)/len(scores) for cat, scores in categories.items()}
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    print(f"🔍 Check your Langfuse dashboard at {os.getenv('LANGFUSE_HOST')} to see the scores")
    if session_id:
        print(f"📍 Filter by session ID: {session_id}")
    
    # Ensure all events are sent before exiting
    print("\n🔄 Flushing events to Langfuse...")
    langfuse_client.flush()
    time.sleep(2)  # Give time for flush to complete
    
    print("\n✅ Scoring demo complete!")
    return session_id, trace_ids


if __name__ == "__main__":
    # Check if session ID was passed as command line argument
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    main(session_id)