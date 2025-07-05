# Strands Agents + Langfuse Integration Guide

This guide provides the complete solution for integrating AWS Strands Agents with Langfuse observability using OpenTelemetry (OTEL).

## Overview

Strands Agents SDK v0.2.0 includes built-in OpenTelemetry support via the `strands.telemetry` module, but it requires explicit initialization and correct configuration to work with Langfuse.

## ✅ Working Solution

### Key Requirements

1. **Strands v0.2.0+** - Has OTEL support via `strands.telemetry` module
2. **Langfuse v3.22.0+** - Has OTEL endpoint support
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
strands-agents>=0.2.0
boto3>=1.26.0
python-dotenv>=1.0.0
```

## 🎯 Summary

The key to successful Strands + Langfuse integration is:

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