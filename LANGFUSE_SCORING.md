# Langfuse Scoring with AWS Strands Agents

A comprehensive guide for implementing evaluation and scoring in Strands + Langfuse applications, based on official patterns and practical integration examples.

## Overview

Langfuse scoring enables automated evaluation of LLM responses through various approaches:
- Simple test-driven evaluation
- Sophisticated frameworks like RAGAS
- Custom evaluation metrics

Two main implementation patterns:
1. **Production Pattern** - Fetch-and-score with RAGAS integration
2. **Development Pattern** - Test-driven scoring with deterministic trace IDs

## Quick Start

### Environment Setup

```python
import os
import base64
from dotenv import load_dotenv

# CRITICAL: Load environment variables FIRST
load_dotenv()

# Configure Langfuse authentication
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Create auth token for OTEL
auth_token = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()

# CRITICAL: Set OTEL environment variables BEFORE importing Strands
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{LANGFUSE_HOST}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"

# NOW import Strands after setting environment variables
from strands import Agent
from strands.telemetry import StrandsTelemetry

# Initialize telemetry
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
```

### Basic Scoring Example

```python
from langfuse import Langfuse

langfuse_client = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY
)

# Execute agent and get response
response = agent("What is the capital of France?")

# Wait for trace to be indexed
time.sleep(2)

# Find trace and score
trace = langfuse_client.get_traces(limit=1).data[0]
langfuse_client.create_score(
    trace_id=trace.id,
    name="accuracy",
    value=1.0 if "Paris" in response else 0.0,
    data_type="NUMERIC"
)
```

## Scoring API Reference

### Core Methods

```python
# Method 1: Direct client scoring (most common)
langfuse_client.create_score(
    trace_id=trace_id,
    name="metric_name",
    value=score_value,
    comment="Optional explanation",
    data_type="NUMERIC"  # or "CATEGORICAL"
)

# Method 2: Span-based scoring (Langfuse v3 only)
with langfuse.start_as_current_span(name="evaluation") as span:
    # Execute operations
    span.score_trace(
        name="metric_name",
        value=score_value,
        comment="Optional explanation"
    )
```

### Score Types

```python
# Numeric scores (0.0 to 1.0)
langfuse_client.create_score(
    trace_id=trace_id,
    name="accuracy",
    value=0.95,
    data_type="NUMERIC"
)

# Categorical scores
langfuse_client.create_score(
    trace_id=trace_id,
    name="test_result",
    value="passed",  # or "failed", "partial"
    data_type="CATEGORICAL"
)

# Boolean scores (as numeric)
langfuse_client.create_score(
    trace_id=trace_id,
    name="contains_answer",
    value=1.0,  # or 0.0
    data_type="NUMERIC"
)
```

## Implementation Patterns

### Pattern 1: Production Evaluation (Batch Scoring)

Best for production pipelines, historical analysis, and complex evaluations.

```python
class ProductionEvaluator:
    def __init__(self, langfuse_client):
        self.langfuse = langfuse_client
    
    def evaluate_batch(self, test_cases):
        # Phase 1: Execute all tests
        results = []
        for test in test_cases:
            response = agent(test["prompt"])
            results.append({
                "test": test,
                "response": response,
                "timestamp": datetime.now()
            })
        
        # Phase 2: Wait for trace indexing
        time.sleep(10)
        
        # Phase 3: Fetch and score traces
        traces = self.langfuse.get_traces(
            tags=["production"],
            limit=len(test_cases)
        )
        
        for trace in traces.data:
            # Match trace to test case
            test_result = self._match_trace_to_result(trace, results)
            if test_result:
                # Calculate and submit scores
                score = self._evaluate(test_result["response"], test_result["test"]["expected"])
                self.langfuse.create_score(
                    trace_id=trace.id,
                    name="accuracy",
                    value=score
                )
```

### Pattern 2: Development Testing (Deterministic IDs)

Best for automated testing, CI/CD, and development workflows.

```python
def generate_trace_id(session_id: str, test_name: str) -> str:
    """Generate deterministic trace ID for testing"""
    seed = f"{session_id}-{test_name}"
    return Langfuse.create_trace_id(seed=seed)

# Use deterministic trace IDs for immediate scoring
trace_id = generate_trace_id(session_id, test_case["name"])

with langfuse.start_as_current_span(
    name=f"test-{test_case['name']}",
    trace_context={"trace_id": trace_id}
) as span:
    response = agent(test_case["prompt"])
    score = evaluate_response(response, test_case["expected"])
    
    # Score immediately
    span.score_trace(
        name="test_accuracy",
        value=score,
        data_type="NUMERIC"
    )
```

## Advanced Evaluation

### RAGAS Integration

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
import pandas as pd

def evaluate_with_ragas(agent, test_questions):
    results = []
    
    for question in test_questions:
        # Execute agent
        response = agent(question)
        
        # Prepare RAGAS dataset
        data = {
            'question': [question],
            'answer': [str(response)],
            'contexts': [[]]  # Add contexts if using RAG
        }
        
        # Evaluate with RAGAS
        dataset = pd.DataFrame(data)
        scores = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy]
        )
        
        # Submit scores to Langfuse
        trace_id = get_latest_trace_id()
        for metric, value in scores.items():
            langfuse_client.create_score(
                trace_id=trace_id,
                name=f"ragas_{metric}",
                value=value
            )
```

### Custom Evaluation Functions

```python
def score_exact_match(response: str, expected: str) -> Dict[str, Any]:
    """Score based on exact string match"""
    if expected.lower() in response.lower():
        return {"score": 1.0, "reasoning": "Exact match found"}
    return {"score": 0.0, "reasoning": "No match found"}

def score_keyword_match(response: str, keywords: List[str]) -> Dict[str, Any]:
    """Score based on keyword presence"""
    found = [kw for kw in keywords if kw.lower() in response.lower()]
    score = len(found) / len(keywords) if keywords else 0.0
    return {
        "score": score,
        "reasoning": f"Found {len(found)}/{len(keywords)} keywords"
    }

def score_length_constraint(response: str, min_words: int = 10) -> Dict[str, Any]:
    """Score based on response length"""
    word_count = len(response.split())
    if word_count >= min_words:
        return {"score": 1.0, "reasoning": f"Response has {word_count} words"}
    return {
        "score": word_count / min_words,
        "reasoning": f"Response too short: {word_count}/{min_words} words"
    }
```

## Production Deployment

### Lambda Handler Example

```python
def lambda_handler(event, context):
    """Lambda with integrated scoring"""
    try:
        # Execute agent
        prompt = event["prompt"]
        expected = event.get("expected_answer")
        
        result = agent(prompt)
        
        # Log metrics
        metrics.add_metric(
            name="TokensUsed",
            value=result.metrics.accumulated_usage['totalTokens']
        )
        
        # Schedule scoring (async)
        if expected:
            sqs.send_message(
                QueueUrl=SCORING_QUEUE_URL,
                MessageBody=json.dumps({
                    "trace_id": context.request_id,
                    "response": str(result),
                    "expected": expected
                })
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': str(result),
                'trace_id': context.request_id
            })
        }
    except Exception as e:
        logger.exception("Error in agent execution")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

### Multi-Region Configuration

```python
class MultiRegionConfig:
    ENDPOINTS = {
        "us-east-1": "https://us.cloud.langfuse.com/api/public/otel/v1/traces",
        "eu-west-1": "https://eu.cloud.langfuse.com/api/public/otel/v1/traces",
    }
    
    @classmethod
    def configure(cls, region: str, public_key: str, secret_key: str):
        endpoint = cls.ENDPOINTS.get(region, cls.ENDPOINTS["us-east-1"])
        auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = endpoint
        os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth}"
```

## Common Issues and Solutions

### Issue 1: Trace Not Found

**Problem**: Scoring fails with "trace not found" error

**Solution**: Implement retry logic with exponential backoff
```python
def find_trace_with_retry(session_id: str, max_retries: int = 3):
    for attempt in range(max_retries):
        traces = langfuse_client.get_traces(session_id=session_id)
        if traces.data:
            return traces.data[0].id
        time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

### Issue 2: OTEL Configuration

**Problem**: No traces appear in Langfuse

**Solution**: Use correct signal-specific endpoint
```python
# ✅ CORRECT - Signal-specific endpoint
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{host}/api/public/otel/v1/traces"

# ❌ WRONG - Generic endpoint
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host}/api/public/otel"
```

### Issue 3: TracerProvider Warnings

**Problem**: "Overriding of current TracerProvider is not allowed"

**Solution**: Use singleton pattern for telemetry
```python
class TelemetryManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        if not self._initialized:
            self.telemetry = StrandsTelemetry()
            self.telemetry.setup_otlp_exporter()
            self._initialized = True
```

## Best Practices Summary

1. **Environment Setup**: Always configure OTEL environment variables before importing Strands
2. **Timing**: Allow 2-10 seconds for trace indexing before scoring
3. **Error Handling**: Implement retry logic for all scoring operations
4. **Trace Management**: Use session IDs and tags for better trace organization
5. **Score Types**: Use NUMERIC for quantitative metrics, CATEGORICAL for qualitative assessments
6. **Batch Processing**: For production, batch execute then batch score
7. **Development Testing**: Use deterministic trace IDs for predictable testing

## Pattern Selection Guide

| Use Case | Recommended Pattern | Key Benefits |
|----------|-------------------|--------------|
| Production evaluation | Batch scoring | Reliability, scale |
| CI/CD pipelines | Deterministic IDs | Predictability |
| Real-time feedback | Span-based scoring | Low latency |
| Complex metrics | RAGAS integration | Comprehensive evaluation |
| A/B testing | Batch + tags | Easy comparison |
| Development | Mixed approach | Flexibility |

## Conclusion

Successful Langfuse scoring implementation requires:
- Proper environment configuration
- Understanding of trace lifecycle
- Appropriate pattern selection
- Robust error handling

Start with the basic examples, then adapt patterns based on your specific use case and scale requirements.