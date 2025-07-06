"""
Strands Agents + Langfuse Scoring Demo

This demo showcases how to automatically score AWS Strands agents responses using 
Langfuse's scoring capabilities. It tests various scenarios where agents should give
correct or incorrect answers, then scores their responses programmatically.
"""
import sys
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Initialize OTEL before importing Agent
from core.setup import initialize_langfuse_telemetry, setup_telemetry, get_langfuse_client
from core.agent_factory import create_agent
from core.metrics_formatter import format_dashboard_metrics

# Initialize Langfuse OTEL
langfuse_pk, langfuse_sk, langfuse_host = initialize_langfuse_telemetry()

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


def find_trace_for_test(session_id: str, test_case_name: str, max_retries: int = 5):
    """Find the trace for a specific test case using Langfuse API"""
    # Wait for trace to be processed
    time.sleep(3)
    
    for retry in range(max_retries):
        try:
            # Use the API directly via requests
            import requests
            from base64 import b64encode
            
            # Create auth header
            auth = b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()
            headers = {"Authorization": f"Basic {auth}"}
            
            # Query traces with tags
            url = f"{langfuse_host}/api/public/traces"
            params = {
                "tags": ["strands-scoring", test_case_name],
                "limit": 50,
                "orderBy": "timestamp.desc"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            traces = response.json().get("data", [])
            
            # Look for our specific trace
            for trace in traces:
                # Check tags in the trace
                trace_tags = trace.get("tags", [])
                # Also check metadata.attributes.langfuse.tags
                metadata = trace.get("metadata", {})
                attributes = metadata.get("attributes", {})
                attr_tags = attributes.get("langfuse.tags", [])
                
                # Parse attr_tags if it's a JSON string
                if isinstance(attr_tags, str):
                    try:
                        attr_tags = json.loads(attr_tags)
                    except:
                        attr_tags = []
                
                # Check if this trace matches our test case
                all_tags = trace_tags + attr_tags
                if test_case_name in all_tags:
                    return trace.get("id")
                
                # Also check session ID
                if attributes.get("session.id") == session_id and attributes.get("test.name") == test_case_name:
                    return trace.get("id")
            
            # If not found, wait and retry
            if retry < max_retries - 1:
                print(f"   ⏳ Trace not found yet, retrying in 2s...")
                time.sleep(2)
                
        except Exception as e:
            print(f"   ⚠️  Error fetching traces: {str(e)}")
            if retry < max_retries - 1:
                time.sleep(2)
    
    return None


def run_demo(session_id: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Run the scoring demo with the provided or generated session ID.
    
    Args:
        session_id: Optional session ID (will generate if not provided)
        
    Returns:
        Tuple of (session_id, trace_ids)
    """
    # Setup telemetry
    telemetry = setup_telemetry("strands-scoring-demo")
    
    # Initialize Langfuse client for scoring
    langfuse_client = get_langfuse_client(langfuse_pk, langfuse_sk, langfuse_host)
    
    if not session_id:
        session_id = f"scoring-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("🎯 Starting Strands Agents + Langfuse Scoring Demo")
    print(f"📊 Session ID: {session_id}")
    print(f"🌐 Langfuse host: {langfuse_host}")
    print("=" * 70)
    
    results = []
    trace_ids = []  # Store trace IDs for scoring
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n🧪 Test {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"📝 Category: {test_case['category']}")
        print(f"❓ Question: {test_case['user']}")
        print(f"🎯 Expected: {test_case['expected_answer']}")
        
        try:
            # Create agent with test-specific attributes
            agent = create_agent(
                system_prompt=test_case["system"],
                session_id=session_id,
                user_id="scoring-evaluator",
                tags=["strands-scoring", test_case["name"], test_case["category"]],
                **{
                    "test.name": test_case["name"],
                    "test.category": test_case["category"],
                    "test.expected": test_case["expected_answer"],
                    "test.method": test_case["scoring_method"]
                }
            )
            
            # Execute the agent
            response = agent(test_case["user"])
            answer = str(response)
            
            print(f"🤖 Response: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            
            # Generate a trace ID for this test
            test_trace_id = f"{session_id}-{test_case['name']}"
            print(format_dashboard_metrics(response, trace_id=test_trace_id))
            
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
            
            print("-" * 70)
            
            # Force flush telemetry before finding trace
            if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
                telemetry.tracer_provider.force_flush()
            
            # Find the trace ID for this test
            trace_id = find_trace_for_test(session_id, test_case["name"])
            
            if trace_id:
                trace_ids.append(trace_id)
                
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
                    
                    scores_sent = True
                    
                except Exception as e:
                    print(f"⚠️  Failed to send score to Langfuse: {str(e)}")
                    scores_sent = False
            else:
                print(f"⚠️  Could not find trace ID for scoring")
                scores_sent = False
                trace_id = f"not-found-{test_case['name']}"
            
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
                "scores_sent": scores_sent,
                "tokens": response.metrics.accumulated_usage['totalTokens'],
                "latency_ms": response.metrics.accumulated_metrics['latencyMs']
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
                "trace_id": "error",
                "scores_sent": False,
                "tokens": 0,
                "latency_ms": 0
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
    
    # Performance metrics
    total_tokens = sum(r["tokens"] for r in results)
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0
    print(f"\n📈 Performance Metrics:")
    print(f"Total Tokens Used: {total_tokens}")
    print(f"Average Latency: {avg_latency:.0f}ms")
    
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
    
    # Save results
    output_file = f"scoring_results_{session_id}.json"
    with open(output_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "trace_ids": [tid for tid in trace_ids if tid],
            "summary": {
                "total_tests": total_tests,
                "average_score": avg_score,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "total_tokens": total_tokens,
                "average_latency_ms": avg_latency,
                "by_category": {cat: sum(scores)/len(scores) for cat, scores in categories.items()}
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    print(f"🔍 Check your Langfuse dashboard at {langfuse_host} to see the scores")
    if session_id:
        print(f"📍 Filter by tags: strands-scoring")
    
    # Final flush
    print("\n🔄 Flushing remaining events to Langfuse...")
    langfuse_client.flush()
    if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
        telemetry.tracer_provider.force_flush()
    time.sleep(3)  # Give time for final flush to complete
    
    print("\n✅ Scoring demo complete!")
    return session_id, trace_ids


if __name__ == "__main__":
    # Check if session ID was passed as command line argument
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    run_demo(session_id)