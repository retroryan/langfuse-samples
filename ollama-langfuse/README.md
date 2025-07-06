# Ollama + Langfuse Integration (SDK v3)

This example demonstrates how to integrate local Ollama models with Langfuse observability (SDK v3) for tracing, monitoring, and scoring LLM responses.

## Prerequisites

1. **Python 3.11+** (3.12.10 recommended)
2. **Ollama** - Install from https://ollama.com/download
3. **Langfuse** - See parent README for setup instructions

## Python Setup

```bash
# Set Python version for this project
pyenv local 3.12.10

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run setup script
python setup.py

# Run demos
python ollama_langfuse_example.py      # Basic example
python ollama_monty_python_demo.py     # Fun conversational demo
python ollama_scoring_demo.py          # Automated scoring demo

# Or run with validation
python run_and_validate.py             # Validates traces were created
python run_scoring_and_validate.py     # Validates scoring functionality
```

## What's Included

- **Basic Example**: Simple demonstration of tracing Ollama API calls
- **Monty Python Demo**: Multi-turn conversation with session tracking
- **Scoring Demo**: Automated evaluation of LLM responses with pass/fail tests
- **Validation Scripts**: Verify traces and scores are properly recorded

## How It Works

The integration uses Langfuse's OpenAI SDK wrapper (v3) to automatically trace all Ollama API calls. This captures:
- Request/response content
- Latency measurements
- Token usage statistics
- Custom metadata and tags

### Langfuse SDK v3 Features

Langfuse SDK v3 is built on OpenTelemetry (OTEL) standards and provides enhanced observability:

1. **Trace Data**: Each LLM interaction creates a trace containing:
   - Input prompts and output responses
   - Model parameters (temperature, max tokens, etc.)
   - Execution time and latency metrics
   - Token usage (input, output, and total tokens)

2. **Session Tracking**: Group related interactions using session IDs to analyze multi-turn conversations

3. **User Identification**: Associate traces with specific users for usage analytics

4. **Custom Metadata**: Add tags, scores, and other metadata to traces for filtering and analysis

5. **Automatic Instrumentation**: Simply wrap your OpenAI client with Langfuse:
   ```python
   from langfuse.openai import OpenAI
   
   client = OpenAI(
       base_url='http://localhost:11434/v1',
       api_key='ollama'
   )
   ```

6. **V3-Specific Improvements**:
   - Built on OpenTelemetry (OTEL) for standardized observability
   - Enhanced metadata handling with `langfuse_` prefixed fields
   - Improved context propagation across function boundaries
   - Better performance with optimized event batching
   - Deterministic trace ID generation for testing

All API calls through this client are automatically traced without additional code changes. View traces in the Langfuse dashboard at http://localhost:3000.

### Important Notes

- **Event Flushing**: The scoring demo calls `langfuse_client.flush()` to ensure all events are sent before the script exits. This is important for short-lived scripts.
- **Metadata Fields**: Use `langfuse_session_id`, `langfuse_user_id`, and `langfuse_tags` in the metadata parameter for v3 compatibility.
- **Trace IDs**: For deterministic trace IDs (useful in testing), pass the trace ID when creating completions.
- **Scoring Demo**: The scoring demo has been simplified to use a cleaner approach - it collects all LLM responses first, then scores them in a batch at the end. This makes the code much easier to understand compared to the previous span-based approach. An advanced version using v3 span context is available in `ollama_scoring_demo_advanced.py` for those interested in more complex scoring patterns.

For detailed documentation and advanced usage, refer to the parent repository README.