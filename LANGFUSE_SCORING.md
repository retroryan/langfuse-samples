# Langfuse Scoring Patterns with AWS Strands Agents

This document analyzes Langfuse scoring implementations across official Strands documentation, sample code, and practical integration patterns, providing a comprehensive guide for implementing evaluation and scoring in Strands + Langfuse applications.

## Overview

Langfuse scoring enables automated evaluation of LLM responses through both simple test-driven approaches and sophisticated evaluation frameworks like RAGAS. This analysis covers two main implementation patterns found in the codebase:

1. **Official Strands Pattern** - Production-ready evaluation with RAGAS integration
2. **Sample Integration Pattern** - Test-driven scoring with deterministic trace IDs

## Official Strands Scoring Pattern

### Documentation References

The primary official documentation for Langfuse scoring with Strands is found in:

1. **`/Users/ryanknight/projects/aws/strands-official/LANGFUSE_IMPLEMENTATION_GUIDE.md`** (Lines 512-637)
   - Comprehensive evaluation and scoring section
   - RAGAS integration examples
   - Production deployment patterns

2. **`/Users/ryanknight/projects/aws/strands-official/samples/01-tutorials/01-fundamentals/08-observability-and-evaluation/`**
   - `Observability-and-Evaluation-sample.ipynb` - Complete Jupyter notebook tutorial
   - `strands_eval.py` - Production-ready Python implementation

### Core Implementation Pattern

The official pattern uses **Langfuse SDK scoring** with auto-generated trace IDs:

```python
# From strands-official/samples/.../strands_eval.py
from langfuse import Langfuse

class LangfuseEvaluator:
    def __init__(self, public_key: str, secret_key: str):
        self.langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key
        )
    
    def evaluate_agent_response(self, trace_id: str, response: str, expected: str = None):
        """Score agent response quality"""
        # Wait for trace to be indexed
        time.sleep(2)
        
        # Calculate scores
        scores = []
        
        # Accuracy score (if expected output provided)
        if expected:
            accuracy = 1.0 if response.strip() == expected.strip() else 0.0
            scores.append({
                "name": "accuracy",
                "value": accuracy,
                "comment": f"Expected: {expected[:50]}..."
            })
        
        # Submit scores using create_score() method
        for score in scores:
            self.langfuse.create_score(  # Note: create_score, not score
                trace_id=trace_id,
                name=score["name"],
                value=score["value"],
                comment=score["comment"]
            )
```

### RAGAS Integration

The official examples demonstrate sophisticated evaluation using RAGAS:

```python
# From LANGFUSE_IMPLEMENTATION_GUIDE.md (Lines 584-637)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
import pandas as pd

class RAGASLangfuseIntegration:
    def evaluate_rag_pipeline(self, agent, test_questions: list):
        """Evaluate RAG pipeline using RAGAS"""
        results = []
        
        for question in test_questions:
            # Execute agent
            response = agent(question)
            
            # Prepare data for RAGAS
            data = {
                'question': [question],
                'answer': [str(response)],
                'contexts': [[]]  # Extract from agent if using RAG
            }
            
            # Run RAGAS evaluation
            dataset = pd.DataFrame(data)
            scores = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy]
            )
            
            # Push scores to Langfuse
            trace_id = self._get_trace_id_from_context()
            
            for metric, value in scores.items():
                self.langfuse.create_score(
                    trace_id=trace_id,
                    name=f"ragas_{metric}",
                    value=value,
                    comment=f"RAGAS {metric} score"
                )
```

### Trace Management Strategy

Official Strands examples use **fetch-and-score** approach:

```python
# Fetch traces from Langfuse by tags/filters
traces = langfuse_client.api.trace.list(
    tags=["Agent-SDK"],
    page=1,
    page_size=50
)

# Process and score traces
for trace in traces:
    # Extract data for evaluation
    processed_data = process_traces([trace])
    
    # Score using auto-generated trace ID
    langfuse_client.create_score(
        trace_id=trace.id,  # Uses Langfuse's auto-generated ID
        name="evaluation_metric",
        value=metric_value
    )
```

## Sample Integration Scoring Pattern

### Documentation References

The sample integration pattern is documented in:

1. **`/Users/ryanknight/projects/aws/langfuse-samples/strands-langfuse/KEY_STRANDS_LANGFUSE.md`** (Lines 303-371)
   - Deterministic trace ID generation with `Langfuse.create_trace_id()`
   - Hybrid OTEL + SDK scoring approach

2. **`/Users/ryanknight/projects/aws/langfuse-samples/strands-langfuse/demos/scoring.py`** (Lines 275-508)
   - Batch scoring implementation
   - Test-driven evaluation patterns

### Core Implementation Pattern

The sample pattern uses **batch scoring** with auto-generated trace IDs:

```python
# From langfuse-samples/strands-langfuse/demos/scoring.py (Lines 431-498)

# Batch Scoring Phase
# NOTE: We perform scoring as a separate batch operation because:
# 1. Strands uses OTEL telemetry which generates trace IDs automatically
# 2. We cannot control or predict these trace IDs during agent execution
# 3. Traces need time to be processed and indexed in Langfuse
# 4. This approach ensures higher success rate for attaching scores

print("📊 BATCH SCORING PHASE")
time.sleep(10)  # Wait for traces to be processed

scores_sent = 0
scores_failed = 0

for i, result in enumerate(results):
    if result["score"] is None:  # Skip error results
        continue
        
    print(f"🎯 Scoring test {i+1}/{len(results)}: {result['test_case']}")
    
    # Find the trace for this test
    trace_id = find_trace_for_test(session_id, result["test_case"])
    
    if trace_id:
        result["trace_id"] = trace_id
        
        # Score the trace in Langfuse
        try:
            # Automated scoring
            langfuse_client.create_score(
                trace_id=trace_id,
                name=f"automated_{result['method']}",
                value=result["score"],
                comment=result['reasoning'],
                data_type="NUMERIC"
            )
            
            # Category score
            category_score = "passed" if result["score"] >= 0.8 else "partial" if result["score"] >= 0.5 else "failed"
            langfuse_client.create_score(
                trace_id=trace_id,
                name="test_result",
                value=category_score,
                data_type="CATEGORICAL"
            )
            
            scores_sent += 1
            print(f"   ✅ Scores sent successfully")
            
        except Exception as e:
            print(f"   ⚠️  Failed to send score: {str(e)}")
            scores_failed += 1
```

### Deterministic Trace IDs (Alternative Approach)

The samples also demonstrate deterministic trace ID generation for controlled scoring:

```python
# From langfuse-samples/ollama-langfuse/ollama_scoring_demo.py (Lines 202-272)

def generate_trace_id(session_id: str, test_case_name: str) -> str:
    """Generate a deterministic trace ID using Langfuse v3 API
    
    This uses Langfuse SDK v3's built-in method which ensures:
    - W3C Trace Context compliance (32 hex characters)
    - Deterministic generation from the same seed
    - Proper format for OpenTelemetry compatibility
    """
    # Create a deterministic seed from session and test case
    seed = f"{session_id}-{test_case_name}"
    # Use Langfuse's built-in method for W3C compliant trace IDs
    return Langfuse.create_trace_id(seed=seed)

# Usage with span context for controlled trace IDs
langfuse = get_client()

# Create a span with our custom trace ID
with langfuse.start_as_current_span(
    name=f"scoring-{test_case['name']}",
    trace_context={"trace_id": trace_id}
) as span:
    # Inside the span context, the OpenAI wrapper will attach
    # this call to our span instead of creating a new trace
    response = client.chat.completions.create(...)
    
    # Score immediately using span methods
    span.score_trace(
        name=f"automated_{test_case['scoring_method']}",
        value=score_value,
        comment=score_result['reasoning'],
        data_type="NUMERIC"
    )
```

## Scoring API Methods Comparison

### Langfuse SDK Methods

Both patterns use the same underlying Langfuse SDK scoring API:

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
span.score_trace(
    name="metric_name",
    value=score_value,
    comment="Optional explanation",
    data_type="NUMERIC"
)
```

### Data Types and Values

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

## Implementation Patterns Comparison

| Aspect | Official Strands | Sample Integration |
|--------|------------------|-------------------|
| **Scoring Method** | `langfuse_client.create_score()` | `langfuse_client.create_score()` |
| **Trace ID Source** | Auto-generated (fetch from Langfuse) | Auto-generated + Deterministic options |
| **Timing** | Batch processing post-execution | Batch + Immediate options |
| **Evaluation Framework** | RAGAS + Custom metrics | Simple test cases |
| **Use Case** | Production evaluation pipelines | Testing and development |
| **Complexity** | High (multi-metric evaluation) | Low-Medium (focused testing) |

## Best Practices from Both Patterns

### 1. Environment Setup (Critical)

```python
# From strands-official/LANGFUSE_IMPLEMENTATION_GUIDE.md (Lines 79-114)
import os
import base64
from dotenv import load_dotenv

# CRITICAL: Load environment variables FIRST
load_dotenv()

# Configure Langfuse authentication
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Create auth token for OTEL authentication
auth_token = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()

# CRITICAL: Set OTEL environment variables BEFORE importing Strands
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{LANGFUSE_HOST}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"

# NOW import Strands after setting environment variables
from strands import Agent
from strands.telemetry import StrandsTelemetry
```

### 2. Telemetry Initialization

```python
# CRITICAL: Initialize telemetry explicitly
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
```

### 3. Scoring Timing Strategies

#### Immediate Scoring (v3 Span Context)
```python
# From ollama-langfuse samples
with langfuse.start_as_current_span(name="evaluation", trace_context={"trace_id": trace_id}) as span:
    response = agent(prompt)
    score = evaluate_response(response)
    span.score_trace(name="quality", value=score)
```

#### Batch Scoring (Production Pattern)
```python
# From strands-langfuse samples
# 1. Execute all agents first
results = []
for test_case in test_cases:
    response = agent(test_case["prompt"])
    results.append({"response": response, "test": test_case})

# 2. Wait for traces to be indexed
time.sleep(10)

# 3. Find and score all traces
for result in results:
    trace_id = find_trace_for_test(session_id, result["test"]["name"])
    if trace_id:
        langfuse_client.create_score(trace_id=trace_id, ...)
```

### 4. Error Handling

```python
# From both patterns
try:
    langfuse_client.create_score(
        trace_id=trace_id,
        name="metric_name",
        value=score_value
    )
    print(f"✅ Score sent successfully")
except Exception as e:
    print(f"⚠️ Failed to send score: {str(e)}")
    # Log error but continue processing
```

## Production Deployment Considerations

### 1. Lambda Deployment Pattern

```python
# From strands-official/LANGFUSE_IMPLEMENTATION_GUIDE.md (Lines 641-728)
def lambda_handler(event, context):
    """Lambda handler with Langfuse tracing and scoring"""
    try:
        # Execute agent
        result = agent(prompt)
        
        # Log metrics
        metrics.add_metric(
            name="TokensUsed",
            value=result.metrics.accumulated_usage['totalTokens'],
            unit=MetricUnit.Count
        )
        
        # Score could be added here or via separate evaluation pipeline
        
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

### 2. Multi-Region Configuration

```python
# From strands-official/LANGFUSE_IMPLEMENTATION_GUIDE.md (Lines 781-821)
class MultiRegionLangfuseConfig:
    ENDPOINTS = {
        "us-east-1": "https://us.cloud.langfuse.com/api/public/otel/v1/traces",
        "eu-west-1": "https://cloud.langfuse.com/api/public/otel/v1/traces",
    }
    
    @classmethod
    def configure_for_region(cls, aws_region: str, public_key: str, secret_key: str):
        endpoint = cls.ENDPOINTS.get(aws_region, cls.ENDPOINTS["us-east-1"])
        auth_token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = endpoint
        os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
```

## Evaluation Frameworks Integration

### RAGAS Metrics (Official Pattern)

```python
# From strands-official examples
from ragas.metrics import (
    context_relevance,
    response_groundedness,
    AspectCritic,
    RubricsScore
)

# Context relevance evaluation
context_relevance_scores = evaluate(
    dataset,
    metrics=[context_relevance]
)

# Push to Langfuse
for trace_id, score in context_relevance_scores.items():
    langfuse_client.create_score(
        trace_id=trace_id,
        name="rag_context_relevance",
        value=score
    )
```

### Custom Evaluation Functions (Sample Pattern)

```python
# From langfuse-samples/strands-langfuse/demos/scoring.py (Lines 124-199)
def score_exact_match(response: str, expected: str) -> Dict[str, Any]:
    """Score based on exact string match"""
    response_clean = response.strip().lower()
    expected_clean = expected.strip().lower()
    
    if expected_clean in response_clean:
        return {
            "score": 1.0,
            "reasoning": f"Response contains expected answer: '{expected}'"
        }
    else:
        return {
            "score": 0.0,
            "reasoning": f"Response does not contain expected answer: '{expected}'"
        }

def score_keyword_match(response: str, required_keywords: List[str]) -> Dict[str, Any]:
    """Score based on presence of required keywords"""
    response_lower = response.lower()
    found_keywords = [kw for kw in required_keywords if kw.lower() in response_lower]
    
    score = len(found_keywords) / len(required_keywords) if required_keywords else 0.0
    
    return {
        "score": score,
        "reasoning": f"Found {len(found_keywords)}/{len(required_keywords)} keywords: {found_keywords}"
    }
```

## Common Issues and Solutions

### 1. Trace Not Found Errors

**Problem**: Scoring fails because trace ID cannot be found
**Solution**: Add retry logic and wait time

```python
# From langfuse-samples pattern
def find_trace_with_retry(session_id: str, test_name: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        traces = langfuse_client.get_traces(
            session_id=session_id,
            limit=50
        )
        
        for trace in traces.data:
            if test_name in str(trace.metadata):
                return trace.id
        
        if attempt < max_retries - 1:
            time.sleep(2)  # Wait before retry
    
    return None
```

### 2. OTEL Configuration Issues

**Problem**: No traces appear in Langfuse
**Solution**: Use correct endpoint and initialization order

```python
# CRITICAL: Must use signal-specific endpoint
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{host}/api/public/otel/v1/traces"
# NOT: OTEL_EXPORTER_OTLP_ENDPOINT = f"{host}/api/public/otel"

# CRITICAL: Set environment before imports
from strands import Agent  # Import AFTER setting environment
```

### 3. TracerProvider Warnings

**Problem**: "Overriding of current TracerProvider is not allowed"
**Solution**: Initialize telemetry once at application level

```python
# From strands-official/LANGFUSE_IMPLEMENTATION_GUIDE.md (Lines 199-220)
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
        return self.telemetry
```

## Summary and Recommendations

### When to Use Each Pattern

**Official Strands Pattern** (Fetch-and-Score):
- ✅ Production evaluation pipelines
- ✅ RAGAS or complex evaluation frameworks
- ✅ Batch processing of historical data
- ✅ Multi-metric evaluation suites

**Sample Integration Pattern** (Deterministic + Batch):
- ✅ Automated testing and CI/CD
- ✅ Development and debugging
- ✅ Simple pass/fail evaluation
- ✅ Immediate feedback scenarios

### Key Takeaways

1. **Both patterns use identical scoring API**: `langfuse_client.create_score()`
2. **No OTEL-native scoring**: Both rely on Langfuse SDK for scoring
3. **Trace ID management differs**: Auto-generated vs. deterministic approaches
4. **Environment setup is critical**: OTEL configuration must precede imports
5. **Timing matters**: Batch scoring is more reliable for production
6. **Error handling essential**: Always implement retry logic and graceful failures

### Recommended Implementation

For most use cases, combine both approaches:
- Use **deterministic trace IDs** for testing and development
- Use **batch scoring** for production reliability
- Implement **comprehensive error handling** and retry logic
- Follow **official environment setup** patterns for consistency

This hybrid approach provides the benefits of both patterns while avoiding their respective limitations.