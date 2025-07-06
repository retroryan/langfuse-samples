# Langfuse SDK v3 Upgrade Guide

To get started with upgrading from v2 to v3, see the official documentation: https://langfuse.com/docs/sdk/python/sdk-v3#upgrade-from-v2

This guide provides practical migration examples based on the Langfuse codebase patterns and real-world integrations.

## Overview

Langfuse v3 is built on OpenTelemetry (OTEL) standards, providing better ecosystem compatibility, improved performance, and a more intuitive API. While v3 introduces breaking changes, the migration path is straightforward for most use cases.

## Key Changes Summary

1. **OpenTelemetry Foundation**: v3 is built on OTEL standards
2. **Trace Input/Output**: Now derived from root observation by default
3. **Context Management**: Automatic OTEL context propagation
4. **ID Format**: W3C Trace Context compliant (no custom observation IDs)
5. **Parameter Changes**: `enabled` → `tracing_enabled`, `threads` → `media_upload_thread_count`

## Migration by Integration Type

### 1. @observe Decorator Users

**v2 Pattern:**
```python
from langfuse.decorators import langfuse_context, observe

@observe()
def my_function():
    # Update trace attributes directly
    langfuse_context.update_current_trace(
        user_id="user_123",
        session_id="session_456",
        tags=["production"]
    )
    return "result"
```

**v3 Migration:**
```python
from langfuse import observe, get_client

@observe()
def my_function():
    langfuse = get_client()
    
    # Update trace explicitly
    langfuse.update_current_trace(
        user_id="user_123",
        session_id="session_456",
        tags=["production"]
    )
    return "result"
```

### 2. OpenAI Integration

**v2 Pattern:**
```python
from langfuse.openai import openai

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    # Trace attributes directly on the call
    user_id="user_123",
    session_id="session_456",
    tags=["chat"],
    metadata={"source": "app"}
)
```

**v3 Migration - Option 1 (Simplest - Using metadata fields):**
```python
from langfuse.openai import openai

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    metadata={
        "langfuse_user_id": "user_123",
        "langfuse_session_id": "session_456",
        "langfuse_tags": ["chat"],
        "source": "app"  # Regular metadata still works
    }
)
```

**v3 Migration - Option 2 (Using enclosing span):**
```python
from langfuse import get_client
from langfuse.openai import openai

langfuse = get_client()

with langfuse.start_as_current_span(name="chat-request") as span:
    # Set trace attributes on the enclosing span
    span.update_trace(
        user_id="user_123",
        session_id="session_456",
        tags=["chat"],
        input={"query": "Hello"}  # Explicit trace input for LLM-as-a-judge
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        metadata={"source": "app"}
    )
    
    # Set trace output explicitly
    span.update_trace(output={"response": response.choices[0].message.content})
```

### 3. LangChain Integration

**v2 Pattern:**
```python
from langfuse.callback import CallbackHandler

handler = CallbackHandler(
    user_id="user_123",
    session_id="session_456",
    tags=["langchain"]
)

response = chain.invoke({"input": "Hello"}, config={"callbacks": [handler]})
```

**v3 Migration - Option 1 (Using metadata):**
```python
from langfuse.langchain import CallbackHandler

handler = CallbackHandler()

response = chain.invoke(
    {"input": "Hello"},
    config={
        "callbacks": [handler],
        "metadata": {
            "langfuse_user_id": "user_123",
            "langfuse_session_id": "session_456",
            "langfuse_tags": ["langchain"]
        }
    }
)
```

**v3 Migration - Option 2 (Using enclosing span):**
```python
from langfuse import get_client
from langfuse.langchain import CallbackHandler

langfuse = get_client()

with langfuse.start_as_current_span(name="langchain-request") as span:
    span.update_trace(
        user_id="user_123",
        session_id="session_456",
        tags=["langchain"],
        input={"query": "Hello"}
    )
    
    handler = CallbackHandler()
    response = chain.invoke({"input": "Hello"}, config={"callbacks": [handler]})
    
    span.update_trace(output={"response": response})
```

### 4. Low-Level SDK Users

**v2 Pattern:**
```python
from langfuse import Langfuse

langfuse = Langfuse()

trace = langfuse.trace(
    name="my-trace",
    user_id="user_123",
    input={"query": "Hello"}
)

generation = trace.generation(
    name="llm-call",
    model="gpt-4o"
)
generation.end(output="Response")
```

**v3 Migration:**
```python
from langfuse import get_client

langfuse = get_client()

# Use context managers instead of manual objects
with langfuse.start_as_current_span(
    name="my-trace",
    input={"query": "Hello"}  # Becomes trace input automatically
) as root_span:
    # Set trace attributes
    root_span.update_trace(user_id="user_123")
    
    with langfuse.start_as_current_generation(
        name="llm-call",
        model="gpt-4o"
    ) as generation:
        generation.update(output="Response")
    
    # Optionally override trace output
    root_span.update_trace(output={"response": "Response"})
```

## Real-World Examples from Langfuse Codebase

### Example 1: Strands + Langfuse Integration (OTEL-based)

This integration already uses v3 patterns with OpenTelemetry:

```python
# From strands-langfuse/core/setup.py
from langfuse import Langfuse

def get_langfuse_client():
    """Get Langfuse client for direct API operations like scoring"""
    pk, sk, host = get_langfuse_credentials()
    
    # v3 initialization with tracing_enabled
    return Langfuse(
        public_key=pk,
        secret_key=sk,
        host=host,
        tracing_enabled=True  # v3 parameter
    )

# Scoring remains the same in v3
langfuse_client.create_score(
    trace_id=trace_id,
    name="accuracy",
    value=0.9,
    data_type="NUMERIC",
    comment="Correct answer"
)
```

### Example 2: OpenAI Integration Pattern

From the ollama-langfuse examples:

```python
# v3 pattern - no migration needed
from langfuse.openai import OpenAI
from langfuse import get_client

# OpenAI wrapper for automatic tracing
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

# Direct client for scoring
langfuse = get_client()

# Make traced call
response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello"}],
    metadata={
        "langfuse_session_id": "demo-session",
        "langfuse_user_id": "demo-user",
        "custom_field": "value"
    }
)

# Flush at the end
langfuse.flush()
```

## Critical Migration Points

### 1. Client Initialization

```python
# v2
langfuse = Langfuse(
    enabled=True,  # v2 parameter
    threads=5      # v2 parameter
)

# v3
langfuse = Langfuse(
    tracing_enabled=True,           # v3 parameter
    media_upload_thread_count=5     # v3 parameter
)
```

### 2. Trace Input/Output for LLM-as-a-Judge

**Critical**: LLM-as-a-judge features rely on trace-level inputs/outputs. In v3, these are derived from the root observation by default.

```python
# Ensure explicit trace input/output for evaluation
with langfuse.start_as_current_span(name="evaluation-task") as span:
    # Explicitly set trace input/output
    span.update_trace(
        input={"question": user_question},
        output={"answer": generated_answer}
    )
```

### 3. ID Management

```python
# v2: Custom observation IDs were possible
trace = langfuse.trace(id="custom-trace-id")

# v3: Use W3C Trace Context format
# Generate deterministic trace IDs from external systems
from langfuse import Langfuse

external_request_id = "req_12345"
trace_id = Langfuse.create_trace_id(seed=external_request_id)

@observe(langfuse_trace_id=trace_id)
def my_function():
    pass
```

### 4. Context Propagation

v3 uses automatic OTEL context propagation:

```python
# v3: Context automatically propagates
with langfuse.start_as_current_span(name="parent") as parent:
    # Any spans created here are automatically children
    with langfuse.start_as_current_generation(name="child") as child:
        # child is automatically nested under parent
        pass
```

## Testing Your Migration

1. **Enable Debug Logging**:
```python
langfuse = Langfuse(debug=True)
# or
export LANGFUSE_DEBUG=True
```

2. **Verify Traces**:
```python
# Check authentication
if langfuse.auth_check():
    print("Connected to Langfuse")

# Force flush to ensure traces are sent
langfuse.flush()
```

3. **Common Issues**:
- No traces appearing: Check `tracing_enabled=True` and call `flush()`
- Missing trace attributes: Use metadata fields or enclosing spans
- Authentication errors: Verify keys and host configuration

## Best Practices for v3

1. **Use Context Managers**: Prefer `with` statements over manual span management
2. **Explicit Trace I/O**: Set trace input/output explicitly for LLM-as-a-judge
3. **Flush on Exit**: Always call `langfuse.flush()` or `langfuse.shutdown()`
4. **Metadata Pattern**: Use `langfuse_*` prefixed metadata fields for simple migrations
5. **Debug Mode**: Enable debug logging during migration to catch issues

## Future Support

Langfuse will continue to support v2 with critical bug fixes and security patches, but all new features will be added to v3 only. The migration to v3 is recommended for:
- Better performance (no SDK-side size limits)
- OpenTelemetry ecosystem compatibility
- Improved developer experience
- Access to new features

For additional help, refer to:
- Official v3 documentation: https://langfuse.com/docs/sdk/python/decorators
- GitHub issues: https://github.com/langfuse/langfuse/issues
- Migration examples in this repository's sample projects