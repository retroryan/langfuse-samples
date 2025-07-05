# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains sample integrations demonstrating how to use Langfuse observability with different LLM frameworks and services. It includes examples for:

- **ollama-langfuse**: Integration with local Ollama models using OpenAI-compatible API
- **strands-langfuse**: Integration with AWS Strands agents and Bedrock models using OpenTelemetry

## Common Development Commands

### Python Examples (ollama-langfuse, strands-langfuse)

```bash
# Install dependencies for a specific example
cd [example-directory]
pip install -r requirements.txt

# Run basic examples
python [framework]_langfuse_example.py

# Run Monty Python themed demos
python [framework]_monty_python_demo.py

# Run scoring demos (automated response evaluation)
python [framework]_scoring_demo.py

# Run with validation (checks traces were created)
python run_and_validate.py        # Runs Monty Python demo by default
python run_and_validate.py basic  # Runs basic example

# Run scoring with validation
python run_scoring_and_validate.py

# View recent traces via API
python view_traces.py
```

### Root Level Debug Utilities

```bash
# Debug score API endpoints
python debug_scores_api.py

# Clean up test metrics (with prompts)
python delete_metrics.py          # Interactive cleanup
python delete_metrics.py traces   # Delete only traces
python delete_metrics.py scores   # Delete only scores
```

## High-Level Architecture

### Integration Patterns

1. **Ollama Integration**
   - Uses Langfuse's OpenAI SDK wrapper for automatic tracing
   - Requires local Ollama service running on port 11434
   - Supports deterministic trace IDs via metadata
   - Dependencies: `langfuse>=2.53.3`, `openai>=1.0.0`

2. **Strands Integration**
   - Uses OpenTelemetry (OTEL) instrumentation
   - Requires explicit telemetry initialization (not automatic!)
   - Must use signal-specific endpoint: `/api/public/otel/v1/traces`
   - See `strands-langfuse/KEY_STRANDS_LANGFUSE.md` for critical setup details
   - Dependencies: `strands-agents[otel]>=0.2.0`, `boto3>=1.34.0`

### Key Components

- **Trace Validation**: Each example includes `run_and_validate.py` that:
  - Checks service availability
  - Runs the example with unique session ID
  - Queries Langfuse API to verify traces were created
  - Displays trace metrics and validation results

- **Scoring System**: Automated response evaluation with:
  - Test cases with expected answers
  - Multiple scoring methods (exact match, keyword match)
  - Numeric scores (0.0-1.0) and categorical results
  - Intentional wrong answers to validate scoring accuracy
  - Results saved to timestamped JSON files

## Environment Setup

Each example directory contains a `.env` file with configuration:
- **ollama-langfuse**: Points to local Langfuse (http://localhost:3000)
- **strands-langfuse**: Requires AWS credentials and Bedrock configuration

Common environment variables:
```bash
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=http://localhost:3000
AWS_REGION=us-west-2
BEDROCK_REGION=us-west-2
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Testing Approach

Since these are example integrations, testing focuses on:
- Service connectivity (Ollama, Langfuse, AWS)
- Trace creation validation
- API response verification
- Score recording confirmation

The scoring demos use a pattern of intentional wrong answers:
- Tests ending in "_correct" should pass (score ≥ 0.8)
- Tests ending in "_wrong" should fail (score < 0.8)

## Important Notes

- All examples expect Langfuse to be running (locally via Docker or cloud)
- AWS examples require valid Bedrock access in the configured region
- Token usage and latency metrics are automatically captured in traces
- The repository uses direct Python script execution without a formal build system
- For Strands integration issues, consult `strands-langfuse/KEY_STRANDS_LANGFUSE.md` first