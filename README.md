# Langfuse Integration Samples

This repository contains example integrations demonstrating how to use [Langfuse](https://langfuse.com/) observability with various LLM frameworks.

Langfuse is an open-source LLM engineering platform that provides deep visibility into your AI applications. With Langfuse traces, you can look under the covers to see exactly what's happening with your AI agents, LLM calls, and complex workflows. Each trace captures the full execution flow including prompts, model responses, token usage, latencies, and costs - giving you the insights needed to debug issues, optimize performance, and understand how your AI systems actually behave in production.

## Prerequisites

- Python 3.12.10 (managed via pyenv)
- Docker (for running Langfuse locally)
- AWS credentials (for strands-langfuse and langfuse-aws projects)

### Install pyenv:
```bash
# macOS (using Homebrew)
brew install pyenv

# Ubuntu/Debian
curl https://pyenv.run | bash
```

## Quick Start

Get up and running with Langfuse observability in 5 minutes:

### 1. Start Langfuse Locally
```bash
git clone https://github.com/langfuse/langfuse
cd langfuse
docker-compose up -d
```
Langfuse will be available at http://localhost:3000

Login to Langfuse and create a new project. Generate API keys from the project settings, then configure your environment:

```bash
cp .env.example .env
# Edit .env and add your Langfuse API keys
```

### 2. Try the Ollama Example (Simplest)
```bash
cd ollama-langfuse
pyenv local 3.12.10
pip install -r requirements.txt
python ollama_langfuse_example.py
```

### 3. View Your Traces
Open http://localhost:3000 and see your LLM interactions being traced!


## Sample Projects

### [ollama-langfuse](ollama-langfuse/) - Simplest Starting Point
Integration with local Ollama models demonstrating:
- **OpenAI-compatible API wrapping** - Automatically traces all Ollama API calls
- **Session tracking** - Groups related conversations together
- **Local LLM observability** - Monitor performance of models running on your machine

### [strands-langfuse](strands-langfuse/) - Production-Ready AWS Integration
Integration with AWS Strands agents and Bedrock models showcasing:
- **OpenTelemetry instrumentation** - Rich trace data via OTLP protocol
- **AWS Bedrock integration** - Traces for Claude, Llama, and other Bedrock models
- **Automated scoring** - Response evaluation with multiple scoring methods
- **Lambda deployment** - Deploy demos as Lambda functions

### [langfuse-aws](langfuse-aws/) - Deploy Langfuse to AWS
Infrastructure as code for deploying Langfuse on AWS (~$75-100/month for development/testing).

## Advanced Setup

### AWS Deployment
For deploying Langfuse on AWS (not for production), see the [langfuse-aws](langfuse-aws/) directory. For production deployments, use the [official AWS deployment guide](https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/).

### MCP Server Configuration
When using Claude Code, you can configure MCP servers for enhanced development. See [MCP_SETUP.md](MCP_SETUP.md) for details.