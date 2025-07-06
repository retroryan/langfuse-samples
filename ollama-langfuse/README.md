# Ollama + Langfuse Integration

This example demonstrates how to integrate local Ollama models with Langfuse observability for tracing, monitoring, and scoring LLM responses.

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

The integration uses Langfuse's OpenAI SDK wrapper to automatically trace all Ollama API calls. This captures:
- Request/response content
- Latency measurements
- Token usage statistics
- Custom metadata and tags

### Langfuse Tracing Details

Langfuse provides observability for LLM applications by automatically capturing:

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

All API calls through this client are automatically traced without additional code changes. View traces in the Langfuse dashboard at http://localhost:3000.

For detailed documentation and advanced usage, refer to the parent repository README.