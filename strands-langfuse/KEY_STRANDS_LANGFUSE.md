# Strands Agents + Langfuse Integration Guide

This guide provides the complete solution for integrating AWS Strands Agents with Langfuse observability using OpenTelemetry (OTEL).

## Overview

Strands Agents SDK v0.2.0 includes built-in OpenTelemetry support via the `strands.telemetry` module, but it requires explicit initialization and correct configuration to work with Langfuse.

## ✅ Working Solution

### Key Requirements

1. **Strands v0.2.0+** - Has OTEL support via `strands.telemetry` module
2. **Langfuse v3.0.0+** - Built on OpenTelemetry standards with OTEL endpoint support
3. **Explicit telemetry initialization** - Must manually initialize StrandsTelemetry
4. **Signal-specific OTEL endpoint** - Use `/api/public/otel/v1/traces`
5. **Environment variables before imports** - Set OTEL config before importing Strands

### Working Example

```python
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Langfuse OTEL export
langfuse_pk = os.environ.get('LANGFUSE_PUBLIC_KEY')
langfuse_sk = os.environ.get('LANGFUSE_SECRET_KEY')
langfuse_host = os.environ.get('LANGFUSE_HOST')

# Create auth token for OTEL authentication
auth_token = base64.b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()

# CRITICAL: Set OTEL environment variables BEFORE importing Strands
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"
os.environ["OTEL_SERVICE_NAME"] = "strands-langfuse-demo"

# NOW import Strands after setting environment variables
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.telemetry import StrandsTelemetry

# CRITICAL: Initialize telemetry explicitly
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()

# Create agent with trace attributes
model = BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0")

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant.",
    trace_attributes={
        "session.id": "my-session-123",
        "user.id": "user@example.com",
        "langfuse.tags": ["production", "v1.0"]
    }
)

# Use the agent - traces will be sent to Langfuse
response = agent("Hello, how are you?")
print(response)

# Force flush telemetry to ensure traces are sent
telemetry.tracer_provider.force_flush()
```

## 🔑 Critical Configuration Points

### 1. Use Signal-Specific Endpoint

```python
# ✅ CORRECT - Signal-specific endpoint
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"

# ❌ WRONG - Generic endpoint (returns 404)
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{langfuse_host}/api/public/otel"
```

### 2. Explicit Telemetry Initialization

```python
# ✅ CORRECT - Explicit initialization
from strands.telemetry import StrandsTelemetry
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()

# ❌ WRONG - Expecting automatic initialization
# Just importing Strands is not enough!
```

### 3. Environment Variables Before Import

```python
# ✅ CORRECT - Set env vars BEFORE importing
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "..."
from strands import Agent

# ❌ WRONG - Setting env vars after import
from strands import Agent
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "..."
```

### 4. Authentication Headers

```python
# ✅ CORRECT - Basic auth with Langfuse keys
auth_token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"

# ❌ WRONG - Missing or incorrect authentication
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = "x-api-key=..."
```

## 📊 Trace Attributes

All trace attributes are properly captured and sent to Langfuse:

```python
trace_attributes={
    "session.id": "demo-session-123",     # Groups related traces
    "user.id": "user@example.com",        # Identifies the user
    "langfuse.tags": ["tag1", "tag2"]     # Custom tags for filtering
}
```

These appear in Langfuse under `metadata.attributes`:
- `metadata.attributes['session.id']`
- `metadata.attributes['user.id']`
- `metadata.attributes['langfuse.tags']` (as JSON string)

## 🚫 Common Pitfalls to Avoid

1. **Don't use the generic OTEL endpoint**
   - `/api/public/otel` returns 404
   - Use `/api/public/otel/v1/traces` instead

2. **Don't expect automatic telemetry initialization**
   - The Strands documentation suggests it's automatic, but it's not
   - Always explicitly initialize StrandsTelemetry

3. **Don't set environment variables after importing Strands**
   - OTEL configuration is read during module import
   - Set all env vars before any Strands imports

4. **Don't forget to flush telemetry**
   - Call `telemetry.tracer_provider.force_flush()` to ensure traces are sent
   - Especially important for short-lived scripts

5. **Don't use OTEL_EXPORTER_OTLP_ENDPOINT**
   - Use signal-specific `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
   - The generic endpoint variable doesn't work with Langfuse

## 🛠️ Debugging Tips

### Check Telemetry Initialization
```python
from strands.telemetry import StrandsTelemetry
telemetry = StrandsTelemetry()
print(f"Tracer provider: {telemetry.tracer_provider}")  # Should not be None
```

### Verify OTEL Endpoints
```python
import requests
import base64

auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
headers = {"Authorization": f"Basic {auth}"}

# Test the endpoint
response = requests.options(f"{host}/api/public/otel/v1/traces", headers=headers)
print(f"Status: {response.status_code}")  # Should be 200 or 204
```

### Check Trace Export
Look for OTEL export logs in stderr. Failed exports show:
```
Failed to export batch code: 404, reason: <!DOCTYPE html>...
```

### Validate Traces in Langfuse
Use the Langfuse API to check if traces are arriving:
```python
response = requests.get(
    f"{host}/api/public/traces",
    headers={"Authorization": f"Basic {auth}"},
    params={"limit": 10, "orderBy": "timestamp.desc"}
)
traces = response.json().get('data', [])
```

## 📋 Complete Requirements

### Environment Variables (.env)
```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=http://localhost:3000  # or https://cloud.langfuse.com

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Python Dependencies
```txt
langfuse>=3.0.0
strands-agents[otel]>=0.2.0
boto3>=1.26.0
python-dotenv>=1.0.0
```

## 🚀 Langfuse v3 Upgrade Benefits

### Why Upgrade to v3?

Langfuse v3 is built entirely on OpenTelemetry standards, providing significant advantages for Strands integration:

1. **Native OTEL Compatibility**
   - Both Strands and Langfuse v3 use OpenTelemetry natively
   - No translation layer needed - traces flow seamlessly
   - Single OTEL pipeline for both systems reduces overhead

2. **Performance Improvements**
   - No SDK-side size limits (v2 had 1MB limit)
   - Better async support and automatic context propagation
   - More efficient batching reduces API calls

3. **Enhanced Developer Experience**
   - Better error messages and debugging
   - Context managers for cleaner code
   - Consistent API with v2 for easy migration

4. **Future-Proof Architecture**
   - Built on industry-standard OTEL
   - Benefits from ongoing OTEL ecosystem improvements
   - Compatible with standard OTEL debugging tools

### What Changed in v3?

The migration from v2 to v3 was minimal for Strands integration because both already use OTEL:

#### 1. **Dependencies Update**
```diff
- langfuse>=2.53.3
+ langfuse>=3.0.0
```

#### 2. **Client Initialization**
```python
# v3 adds tracing_enabled parameter
langfuse_client = Langfuse(
    public_key=pk,
    secret_key=sk,
    host=host,
    tracing_enabled=True  # New in v3
)
```

#### 3. **Scoring API**
```python
# Scoring API remains the same in v3
langfuse_client.create_score(
    trace_id=trace_id,
    name="score_name",
    value=0.9,
    data_type="NUMERIC"  # Optional but recommended
)
```

#### 4. **No Changes Required For**
- OTEL configuration (already compatible)
- Trace attributes (same format)
- Authentication (same Basic Auth)
- Endpoints (same OTEL endpoints)
- Scoring API (`create_score()` method unchanged)

### Migration Summary

The v3 upgrade for Strands integration required only:
1. Update `requirements.txt` to `langfuse>=3.0.0`
2. Add `tracing_enabled=True` to Langfuse client initialization

Everything else remains the same because:
- Strands' OTEL-based architecture aligns perfectly with Langfuse v3's OTEL foundation
- The scoring API (`create_score()`) remains unchanged
- Authentication and endpoints are compatible

### Important Notes

- **OTEL Integration Pattern**: This integration uses Strands' OTEL telemetry rather than Langfuse's v3 decorators or context managers
- **Scoring API**: The `create_score()` method is the same in v2 and v3 (there is no `score()` method)
- **Flushing**: We use `telemetry.tracer_provider.force_flush()` for OTEL, though v3 also offers `langfuse.flush()`

### Deterministic Trace IDs in v3

Langfuse v3 introduces `Langfuse.create_trace_id(seed)` for generating deterministic trace IDs. This is particularly useful for:
- Correlating traces with external systems
- Reliable scoring in test scenarios
- Maintaining trace consistency across retries

#### How It Works

```python
from langfuse import Langfuse

# Generate deterministic trace ID from a seed
seed = f"{session_id}-{test_name}"
trace_id = Langfuse.create_trace_id(seed=seed)
# Always generates the same W3C-compliant trace ID for the same seed
```

#### Using with Strands Integration

Since Strands uses OTEL telemetry, you can't directly pass trace IDs to the agent. However, you can use a hybrid approach:

```python
from langfuse import get_client

langfuse_client = get_client()

# 1. Generate deterministic trace ID
trace_id = Langfuse.create_trace_id(seed="my-external-id")

# 2. Create Langfuse context with this trace ID
with langfuse_client.start_as_current_span(
    name="strands-operation",
    trace_context={"trace_id": trace_id}
) as span:
    # 3. Set trace attributes
    span.update_trace(
        session_id="my-session",
        user_id="my-user",
        tags=["production"]
    )
    
    # 4. Execute Strands agent - OTEL spans will nest under this trace
    agent = create_agent(...)
    response = agent("Hello")

# 5. Score using the deterministic trace ID
langfuse_client.create_score(
    trace_id=trace_id,
    name="accuracy",
    value=0.9
)
```

#### Key Benefits

1. **Predictable Scoring**: Always know which trace to score - no need to search for traces
2. **External Correlation**: Link Langfuse traces to external request IDs
3. **Test Reliability**: Consistent trace IDs across test runs
4. **W3C Compliant**: Generates valid 32-char hex trace IDs
5. **Guaranteed Uniqueness**: When using unique seeds, trace IDs are guaranteed unique

#### Considerations

1. **Seed Design**: Seeds must be unique across your application to avoid trace ID collisions
2. **Timing**: Traces may still need time to process before scores can be attached
3. **OTEL Context**: When using with Strands, wrap agent calls in Langfuse spans to control trace ID

Note: This feature requires Langfuse v3. The OpenAI integration also supports passing `trace_id` directly in the API call.

## 🎯 Summary

The key to successful Strands + Langfuse integration is:

**Note**: This integration uses Langfuse v3, which is built on OpenTelemetry standards, making it naturally compatible with Strands' OTEL-based telemetry.

1. **Use the signal-specific OTEL endpoint**: `/api/public/otel/v1/traces`
2. **Explicitly initialize telemetry**: `StrandsTelemetry().setup_otlp_exporter()`
3. **Set environment variables before imports**
4. **Use proper authentication headers**
5. **Include trace attributes for session/user/tags**

With these configurations, all Strands agent invocations will be automatically traced in Langfuse with full visibility into:
- LLM calls and responses
- Token usage
- Latency metrics
- Custom attributes (session, user, tags)
- Full conversation context

This integration provides powerful observability for production Strands agents without requiring code changes to your agent logic.