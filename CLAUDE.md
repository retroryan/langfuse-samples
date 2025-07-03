# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains sample integrations demonstrating how to use Langfuse observability with different LLM frameworks and services. It includes examples for:

- **ollama-langfuse**: Integration with local Ollama models using OpenAI-compatible API
- **strands-langfuse**: Integration with AWS Strands agents and Bedrock models
- **quick-fuse**: Simplified demo of Strands + Langfuse integration
- **langfuse**: The main Langfuse monorepo (submodule)

## Common Development Commands

### Python Examples (ollama-langfuse, strands-langfuse, quick-fuse)

```bash
# Install dependencies for a specific example
cd [example-directory]
pip install -r requirements.txt

# Run basic examples
python [example]_langfuse_example.py

# Run Monty Python themed demos
python [example]_monty_python_demo.py

# Run with validation (checks traces were created)
python run_and_validate.py        # Runs Monty Python demo by default
python run_and_validate.py basic  # Runs basic example

# View recent traces via API
python view_traces.py
```

### Environment Setup

Each example directory contains a `.env` file with configuration:
- **ollama-langfuse**: Points to local Langfuse (http://localhost:3030)
- **strands-langfuse**: Requires AWS credentials and Bedrock configuration
- **quick-fuse**: Similar to strands-langfuse

## High-Level Architecture

### Integration Patterns

1. **Ollama Integration**
   - Uses Langfuse's OpenAI SDK wrapper
   - Automatically traces OpenAI-compatible API calls
   - Requires local Ollama service running on port 11434

2. **Strands Integration**
   - Uses OpenTelemetry (OTEL) instrumentation
   - Sends traces via OTLP protocol to Langfuse
   - Supports rich trace attributes (session ID, user ID, tags)

### Key Components

- **Trace Validation**: Each example includes `run_and_validate.py` that:
  - Checks service availability
  - Runs the example
  - Queries Langfuse API to verify traces were created
  - Displays trace metrics

- **Demo Scripts**: Fun Monty Python themed examples showcasing:
  - Multi-turn conversations
  - Session tracking
  - User identification
  - Custom tags and metadata

## Testing Approach

Since these are example integrations, testing focuses on:
- Service connectivity (Ollama, Langfuse, AWS)
- Trace creation validation
- API response verification

No unit tests are included as these are demonstration scripts.

## Important Notes

- The `langfuse/` directory is the main Langfuse repository with its own CLAUDE.md
- All examples expect Langfuse to be running (locally via Docker or cloud)
- AWS examples require valid Bedrock access in the configured region
- Token usage and latency metrics are automatically captured in traces