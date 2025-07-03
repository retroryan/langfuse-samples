# Ollama + Langfuse Integration Example

This example demonstrates how to trace local Ollama models using Langfuse observability.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Monty Python demo (default)
python run_and_validate.py

# Or run the basic example
python run_and_validate.py simple
```

The validation script will:
- ✅ Check that Ollama and Langfuse are running
- 🚀 Run the demo
- 🔍 Validate traces were created
- 📊 Display trace metrics

## Prerequisites

1. **Ollama** must be installed and running locally
   - Install from: https://ollama.com/download
   - Pull the llama3.1 model: `ollama pull llama3.1`

2. **Langfuse** must be running locally via Docker
   - The `.env` file is already configured to use `http://localhost:3030`

3. **Python dependencies**
   - Install using: `pip install -r requirements.txt`

## Files

- `ollama_langfuse_example.py` - Basic example script showing Ollama + Langfuse integration
- `ollama_monty_python_demo.py` - Fun Monty Python themed demo with multiple conversations
- `run_and_validate.py` - Script to run examples and validate traces via API
- `requirements.txt` - Python dependencies
- `.env` - Environment configuration (already set up)

## Usage

### Option 1: Run the basic example

```bash
python ollama_langfuse_example.py
```

### Option 2: Run the Monty Python demo

```bash
python ollama_monty_python_demo.py
```

### Option 3: Run with validation

```bash
# Run the Monty Python demo with validation (default)
python run_and_validate.py

# Run the basic example with validation
python run_and_validate.py simple
```

This will:
1. Check that Ollama and Langfuse are running
2. Run the example script
3. Query the Langfuse API to validate traces were created
4. Display trace details including token usage and latency

## What's happening?

The example uses the Langfuse OpenAI SDK wrapper to automatically trace calls to Ollama's OpenAI-compatible API. This provides:

- Automatic capture of all LLM calls
- Token usage tracking
- Latency measurements
- Input/output logging
- Error tracking

## Viewing Traces

After running the example, you can view traces in two ways:

1. **Langfuse UI**: Open http://localhost:3030 in your browser
2. **API**: The validation script shows how to query traces programmatically

## Troubleshooting

1. **Ollama not running**: Start Ollama and ensure it's listening on port 11434
2. **Model not found**: Run `ollama pull llama3.1` to download the model
3. **Langfuse not accessible**: Ensure the Docker container is running on port 3030
4. **No traces appearing**: Wait a few seconds for traces to be processed