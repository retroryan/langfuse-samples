# Ollama + Langfuse Integration

This repository demonstrates how to integrate local Ollama models with Langfuse observability for tracing, monitoring, and scoring LLM responses.

## Quick Start

### 1. Setup Environment
```bash
# Copy environment template and configure
cp .env.example .env
# Edit .env with your Langfuse credentials

# Install dependencies
pip install -r requirements.txt
```

### 2. Prerequisites Check
```bash
# Ensure Ollama is running with the model
ollama pull llama3.1:8b
ollama serve  # if not already running
```

### 3. Run Demos

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Ensure Ollama is running with the llama3.1 model
ollama pull llama3.1:8b

# 3. Run a demo:
python ollama_langfuse_example.py      # Basic example
python ollama_monty_python_demo.py     # Fun conversational demo
python ollama_scoring_demo.py          # Automated scoring demo

# Or run with validation:
python run_and_validate.py             # Validates basic example or Monty Python demo
python run_scoring_and_validate.py     # Runs and validates scoring demo
```

## Prerequisites

1. **Ollama** - Install from https://ollama.com/download
   - Pull the model: `ollama pull llama3.1:8b`
   - Ensure it's running on `http://localhost:11434`

2. **Langfuse** - Must be running locally or in cloud
   - Default configuration uses `http://localhost:3000`
   - API keys are configured in `.env` file

3. **Python 3.8+** with dependencies from `requirements.txt`

## Available Demos

### 1. Basic Example (`ollama_langfuse_example.py`)

A simple demonstration showing how to trace Ollama API calls with Langfuse.

**Features:**
- Basic chat completion
- Automatic trace capture
- Token usage tracking

**Run:**
```bash
python ollama_langfuse_example.py
```

### 2. Monty Python Demo (`ollama_monty_python_demo.py`)

An entertaining multi-turn conversation based on Monty Python's Bridge of Death scene.

**Features:**
- Multiple conversation turns
- Session tracking
- User identification
- Custom metadata and tags

**Run:**
```bash
python ollama_monty_python_demo.py

# Or with validation:
python run_and_validate.py
```

### 3. Scoring Demo (`ollama_scoring_demo.py`)

Demonstrates automated evaluation and scoring of LLM responses.

**Features:**
- Automated response evaluation
- Multiple scoring methods (exact match, keyword match)
- Numeric and categorical scores
- Test cases with expected pass/fail scenarios
- Results saved to JSON

**Run:**
```bash
python ollama_scoring_demo.py

# Or with validation:
python run_scoring_and_validate.py
```

The scoring demo includes:
- Math problems (testing exact numeric matches)
- Geography questions (testing keyword presence)
- History questions (testing factual accuracy)
- Intentionally wrong answers to validate scoring logic

## Architecture & How It Works

### Integration Overview

The integration uses Langfuse's OpenAI SDK wrapper to automatically trace all API calls:

```python
from langfuse.openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)
```

This automatically captures:
- **Request/Response**: All prompts and completions
- **Timing**: Latency measurements
- **Usage**: Token counts (input/output/total)
- **Metadata**: Custom tags, session IDs, user IDs

### Scoring System

The scoring demo showcases Langfuse's evaluation capabilities:

1. **Score Types**:
   - **Numeric**: Float values (0.0 to 1.0) for quantitative metrics
   - **Categorical**: String values for classifications (e.g., "passed", "failed")
   - **Boolean**: True/False evaluations

2. **Scoring Methods**:
   - **Exact Match**: Checks if expected answer appears in response
   - **Keyword Match**: Validates presence of required keywords
   - **Custom Logic**: Implement your own evaluation functions

3. **Creating Scores**:
```python
langfuse_client.create_score(
    trace_id=trace_id,
    name="accuracy",
    value=0.95,
    comment="Correctly identified 19/20 facts",
    data_type="NUMERIC"
)
```

### Viewing Results

1. **Langfuse Dashboard**: 
   - Open http://localhost:3000
   - View traces, scores, and analytics
   - Filter by session ID or tags

2. **API Access**:
   - Use `view_traces.py` to query recent traces
   - Validation scripts demonstrate API usage

3. **Score Analysis**:
   - Scores appear in the dashboard's evaluation tab
   - Filter and aggregate by score name, type, or value

## API Reference

### Key Methods

```python
# Create a traced completion
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[...],
    metadata={
        "langfuse_session_id": "session-123",
        "langfuse_user_id": "user-456",
        "custom_field": "value"
    }
)

# Add a score to a trace
langfuse_client.create_score(
    trace_id="trace-id",
    name="score-name",
    value=0.8,
    data_type="NUMERIC"
)

# Query traces via API
traces = langfuse_client.fetch_traces(
    page=1,
    limit=10,
    from_timestamp=start_time
)
```

### Environment Variables

Configure in `.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Ollama not found" | Ensure Ollama is running: `ollama serve` |
| "Model not available" | Pull the model: `ollama pull llama3.1:8b` |
| "Langfuse connection error" | Check Langfuse is running and `.env` is configured |
| "No traces appearing" | Wait a few seconds for processing, check API keys |
| "Scores not showing" | Ensure trace exists before scoring, check trace IDs |

## Additional Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Ollama Documentation](https://ollama.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## License

This project is part of the langfuse-samples repository.