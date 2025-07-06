# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an Ollama + Langfuse integration example that demonstrates how to use local Ollama models with Langfuse observability for tracing, monitoring, and scoring LLM responses.

## Common Development Commands

### Initial Setup

```bash
# Run interactive setup script
python setup.py

# This will:
# - Check if Ollama is running
# - List available models and help you select one
# - Configure Langfuse credentials
# - Create a .env file with all settings
```

### Running Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Basic examples
python ollama_langfuse_example.py      # Basic tracing example
python ollama_monty_python_demo.py     # Multi-turn conversation demo
python ollama_scoring_demo.py          # Automated scoring demo

# Run with validation (checks if traces were created)
python run_and_validate.py             # Validates basic or Monty Python demo
python run_and_validate.py simple      # Validates basic example specifically
python run_scoring_and_validate.py     # Runs and validates scoring demo

# View recent traces via API
python view_traces.py
```

## High-Level Architecture

### Integration Pattern

The integration uses Langfuse's OpenAI SDK wrapper to automatically trace all Ollama API calls:

```python
from langfuse.openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)
```

This automatically captures:
- Request/response content
- Latency measurements  
- Token usage (input/output/total)
- Custom metadata (session IDs, user IDs, tags)

### Key Components

1. **Trace Validation System** (`run_and_validate.py`):
   - Generates unique session IDs for test runs
   - Checks service availability (Ollama and Langfuse)
   - Runs examples and queries Langfuse API to verify trace creation
   - Handles both quoted and unquoted session IDs in responses
   - Displays detailed trace metrics and observations

2. **Scoring System** (`ollama_scoring_demo.py`):
   - Tests LLM responses with intentional correct/incorrect answers
   - Multiple scoring methods: exact_match, keyword_match
   - Creates both numeric (0.0-1.0) and categorical scores
   - Generates deterministic trace IDs using MD5 hashing
   - Saves results to timestamped JSON files

3. **Score Validation** (`run_scoring_and_validate.py`):
   - Validates expected pass/fail behavior (tests ending in "_correct" should pass, "_wrong" should fail)
   - Queries Langfuse scores API with proper Basic Auth
   - Groups scores by trace and provides statistics
   - Includes cleanup suggestions for old result files

### Environment Configuration

The `.env` file (created by setup.py) contains:
- `OLLAMA_MODEL` - The selected Ollama model to use
- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` for API authentication
- `LANGFUSE_HOST` (default: http://localhost:3000)

### Important Implementation Details

- Ollama must be running on port 11434
- Model is configured via OLLAMA_MODEL in .env (setup.py helps select this)
- All demos read the model from environment variable with fallback to llama3.1:8b
- Trace IDs can be deterministic (scoring demo) or UUID-based (validation scripts)
- Session IDs are passed as command-line arguments to demos
- Scores are sent with proper data types (NUMERIC or CATEGORICAL)
- All examples include proper event flushing before exit