# Langfuse Integration Samples

This repository contains example integrations demonstrating how to use Langfuse observability with various LLM frameworks.

## Sample Projects

### ollama-langfuse
Integration with local Ollama models using OpenAI-compatible API. Includes automatic trace capture for local LLM interactions.

### strands-langfuse
Integration with AWS Strands agents and Bedrock models. Uses OpenTelemetry instrumentation for comprehensive trace data.

### quick-fuse
Simplified demonstration of Strands + Langfuse integration for quick prototyping and testing.

## Running Examples

Each directory contains:
- Python example scripts (basic and Monty Python themed demos)
- `run_and_validate.py` - Runs examples and verifies trace creation
- `view_traces.py` - Views recent traces via Langfuse API
- `.env` file with required configuration

## Prerequisites

- Langfuse instance (local or cloud)
- Python environment with dependencies from `requirements.txt`
- For Ollama examples: Local Ollama service
- For AWS examples: Valid Bedrock credentials