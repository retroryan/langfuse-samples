# Scoring Proposal for Ollama Langfuse Integration

## Overview

This document proposes a new example demonstrating how to implement automated scoring of LLM outputs using Langfuse's scoring functionality. The example will intentionally prompt the LLM to provide both correct and incorrect answers, then automatically evaluate and score these responses.

## Motivation

Currently, the Ollama Langfuse integration demonstrates basic tracing functionality. Adding scoring capabilities will showcase:
- How to evaluate LLM response quality programmatically
- How to track accuracy metrics over time
- How to identify patterns in correct vs incorrect responses
- How to use Langfuse's scoring system for quality assurance

## Proposed Implementation

### 1. Scoring Architecture

The implementation will consist of three main components:

```
ollama_scoring_example.py     # Main example with intentional errors
scoring_evaluator.py         # Evaluation logic for scoring responses
view_scoring_results.py      # Script to view and analyze scores
```

### 2. Example Design

#### 2.1 Intentional Wrong Answers

We'll create prompts that occasionally instruct the LLM to provide incorrect answers:

```python
# Example prompt variations
prompts = [
    {
        "question": "What is 2 + 2?",
        "system": "You are a helpful assistant.",
        "expected": "4",
        "score_type": "exact_match"
    },
    {
        "question": "What is 2 + 2?", 
        "system": "You are a mischievous assistant who sometimes gives wrong answers. For this question, say it equals 5.",
        "expected": "4",
        "score_type": "exact_match"
    },
    {
        "question": "Who was the first person on the moon?",
        "system": "You are a helpful assistant who provides accurate information.",
        "expected": "Neil Armstrong",
        "score_type": "semantic_similarity"
    },
    {
        "question": "Who was the first person on the moon?",
        "system": "You are playing a trivia game where you must give wrong answers. Say it was Buzz Lightyear.",
        "expected": "Neil Armstrong", 
        "score_type": "semantic_similarity"
    }
]
```

#### 2.2 Scoring Types

We'll implement multiple scoring approaches:

1. **Exact Match Scoring**: For factual questions with precise answers
   - Score: 1.0 for exact match, 0.0 otherwise
   
2. **Semantic Similarity Scoring**: For open-ended questions
   - Score: 0.0-1.0 based on semantic similarity
   
3. **Keyword Presence Scoring**: Check for essential keywords
   - Score: Percentage of required keywords present

4. **Factual Accuracy Scoring**: Using LLM-as-judge approach
   - Score: 0.0-1.0 based on factual correctness evaluation

### 3. Implementation Details

#### 3.1 Main Example Script (`ollama_scoring_example.py`)

```python
"""
Ollama + Langfuse Scoring Example

Demonstrates automated scoring of LLM responses, including:
- Intentionally incorrect answers for testing
- Multiple scoring methodologies
- Integration with Langfuse's scoring system
"""

import os
from dotenv import load_dotenv
from langfuse.openai import OpenAI
from scoring_evaluator import ScoreEvaluator
import json
from datetime import datetime

load_dotenv()

# Test cases with expected behaviors
TEST_CASES = [
    # Correct answers expected
    {
        "name": "simple_math_correct",
        "system": "You are a helpful math tutor.",
        "user": "What is 15 + 27?",
        "expected_answer": "42",
        "scoring_method": "exact_match"
    },
    # Intentionally wrong answer
    {
        "name": "simple_math_wrong", 
        "system": "You are a playful assistant who gives wrong math answers. Add 10 to the correct result.",
        "user": "What is 15 + 27?",
        "expected_answer": "42",
        "scoring_method": "exact_match"
    },
    # More complex evaluation
    {
        "name": "capital_city_correct",
        "system": "You are a geography expert.",
        "user": "What is the capital of France?",
        "expected_answer": "Paris",
        "scoring_method": "keyword_match",
        "required_keywords": ["Paris"]
    },
    # Semantic similarity test
    {
        "name": "explanation_quality",
        "system": "You are a science educator.",
        "user": "Explain photosynthesis in one sentence.",
        "expected_answer": "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into glucose and oxygen.",
        "scoring_method": "semantic_similarity"
    }
]

def main():
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
    )
    
    evaluator = ScoreEvaluator()
    session_id = f"scoring-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("🎯 Starting Ollama + Langfuse Scoring Demo")
    print(f"📊 Session ID: {session_id}")
    print("=" * 60)
    
    results = []
    
    for test_case in TEST_CASES:
        print(f"\n🧪 Test Case: {test_case['name']}")
        print(f"❓ Question: {test_case['user']}")
        
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
                "langfuse_session_id": session_id
            }
        )
        
        answer = response.choices[0].message.content
        print(f"🤖 Response: {answer}")
        
        # Evaluate the response
        score_result = evaluator.evaluate(
            response=answer,
            expected=test_case["expected_answer"],
            method=test_case["scoring_method"],
            **test_case.get("additional_params", {})
        )
        
        print(f"📈 Score: {score_result['score']:.2f}")
        print(f"💭 Reasoning: {score_result['reasoning']}")
        
        # Add score to Langfuse trace
        # Note: In a real implementation, we'd need to get the trace_id
        # This is a simplified example
        
        results.append({
            "test_case": test_case["name"],
            "question": test_case["user"],
            "expected": test_case["expected_answer"],
            "actual": answer,
            "score": score_result["score"],
            "reasoning": score_result["reasoning"],
            "method": test_case["scoring_method"]
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SCORING SUMMARY")
    print("=" * 60)
    
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / len(results)
    
    print(f"Total Tests: {len(results)}")
    print(f"Average Score: {avg_score:.2f}")
    print(f"Passed (>0.7): {sum(1 for r in results if r['score'] > 0.7)}")
    print(f"Failed (≤0.7): {sum(1 for r in results if r['score'] <= 0.7)}")
    
    # Save results
    with open(f"scoring_results_{session_id}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to scoring_results_{session_id}.json")

if __name__ == "__main__":
    main()
```

#### 3.2 Scoring Evaluator (`scoring_evaluator.py`)

```python
"""
Scoring evaluation logic for different types of assessments
"""

import re
from typing import Dict, Any, List
import ollama

class ScoreEvaluator:
    def __init__(self):
        self.client = ollama.Client()
    
    def evaluate(self, response: str, expected: str, method: str, **kwargs) -> Dict[str, Any]:
        """Evaluate a response using the specified method"""
        
        if method == "exact_match":
            return self._exact_match_score(response, expected)
        elif method == "keyword_match":
            return self._keyword_match_score(response, kwargs.get("required_keywords", []))
        elif method == "semantic_similarity":
            return self._semantic_similarity_score(response, expected)
        elif method == "llm_judge":
            return self._llm_judge_score(response, expected, kwargs.get("criteria", ""))
        else:
            raise ValueError(f"Unknown scoring method: {method}")
    
    def _exact_match_score(self, response: str, expected: str) -> Dict[str, Any]:
        """Score based on exact match"""
        # Extract numbers or key terms for comparison
        response_clean = response.strip().lower()
        expected_clean = expected.strip().lower()
        
        # Try to extract just the answer if it's in a sentence
        if expected_clean in response_clean:
            return {
                "score": 1.0,
                "reasoning": "Exact match found in response"
            }
        
        # For math problems, try to extract numbers
        response_nums = re.findall(r'-?\d+\.?\d*', response)
        expected_nums = re.findall(r'-?\d+\.?\d*', expected)
        
        if response_nums and expected_nums and response_nums[0] == expected_nums[0]:
            return {
                "score": 1.0,
                "reasoning": "Numeric answer matches expected value"
            }
        
        return {
            "score": 0.0,
            "reasoning": f"No match found. Expected '{expected}' but got '{response}'"
        }
    
    def _keyword_match_score(self, response: str, required_keywords: List[str]) -> Dict[str, Any]:
        """Score based on presence of required keywords"""
        response_lower = response.lower()
        found_keywords = []
        missing_keywords = []
        
        for keyword in required_keywords:
            if keyword.lower() in response_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        score = len(found_keywords) / len(required_keywords) if required_keywords else 0.0
        
        reasoning = f"Found {len(found_keywords)}/{len(required_keywords)} required keywords."
        if missing_keywords:
            reasoning += f" Missing: {', '.join(missing_keywords)}"
        
        return {
            "score": score,
            "reasoning": reasoning
        }
    
    def _semantic_similarity_score(self, response: str, expected: str) -> Dict[str, Any]:
        """Score based on semantic similarity using embeddings"""
        # For this example, we'll use a simplified approach
        # In production, you'd use proper embeddings
        
        response_words = set(response.lower().split())
        expected_words = set(expected.lower().split())
        
        # Check for key scientific terms
        key_terms = {"photosynthesis", "plants", "sunlight", "glucose", "oxygen", 
                    "carbon", "dioxide", "water", "convert", "process"}
        
        response_key_terms = response_words.intersection(key_terms)
        expected_key_terms = expected_words.intersection(key_terms)
        
        if not expected_key_terms:
            # Fallback to simple word overlap
            overlap = response_words.intersection(expected_words)
            score = len(overlap) / max(len(response_words), len(expected_words))
        else:
            # Score based on key term coverage
            score = len(response_key_terms) / len(expected_key_terms)
        
        return {
            "score": min(score, 1.0),
            "reasoning": f"Semantic similarity based on key term overlap: {score:.2f}"
        }
    
    def _llm_judge_score(self, response: str, expected: str, criteria: str) -> Dict[str, Any]:
        """Use LLM as a judge to score the response"""
        prompt = f"""
        Evaluate the following response for accuracy and quality.
        
        Question context: {criteria if criteria else "General knowledge question"}
        Expected answer: {expected}
        Actual response: {response}
        
        Score the response from 0.0 to 1.0 where:
        - 1.0 = Completely correct and well-explained
        - 0.7-0.9 = Mostly correct with minor issues
        - 0.4-0.6 = Partially correct
        - 0.1-0.3 = Mostly incorrect
        - 0.0 = Completely incorrect
        
        Respond in JSON format:
        {{"score": <float>, "reasoning": "<explanation>"}}
        """
        
        # Use Ollama for judging
        judge_response = self.client.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        
        try:
            import json
            result = json.loads(judge_response.message.content)
            return {
                "score": float(result.get("score", 0.0)),
                "reasoning": result.get("reasoning", "No reasoning provided")
            }
        except:
            return {
                "score": 0.5,
                "reasoning": "Failed to parse LLM judge response"
            }
```

### 4. Benefits of This Approach

1. **Comprehensive Testing**: Tests both correct and incorrect scenarios
2. **Multiple Scoring Methods**: Demonstrates flexibility in evaluation approaches
3. **Real-world Applicability**: Shows how to catch and measure LLM errors
4. **Integration Ready**: Easy to integrate with existing Langfuse traces
5. **Extensible**: Easy to add new test cases and scoring methods

### 5. Future Enhancements

1. **Batch Scoring**: Process multiple traces at once
2. **Score Configurations**: Use Langfuse's score configuration feature
3. **Visualization**: Create charts showing score distributions
4. **Alerting**: Set up alerts for low-scoring responses
5. **A/B Testing**: Compare scores across different models or prompts

## Implementation Timeline

1. **Phase 1**: Create basic scoring example with exact match scoring
2. **Phase 2**: Add semantic similarity and keyword matching
3. **Phase 3**: Implement LLM-as-judge scoring
4. **Phase 4**: Create visualization and analysis tools

## Conclusion

This scoring implementation will provide a robust framework for evaluating LLM responses in the Ollama Langfuse integration. By intentionally testing both correct and incorrect scenarios, users can better understand their model's behavior and track quality metrics over time.