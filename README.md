# Langfuse Integration Samples

This repository contains example integrations demonstrating how to use Langfuse observability with various LLM frameworks.

## Getting Started with Langfuse

First, you'll need a Langfuse instance running:

### Local Setup (Recommended for Development)
```bash
git clone https://github.com/langfuse/langfuse
cd langfuse
docker-compose up
```
This will start Langfuse locally at http://localhost:3000

### AWS Deployment

For simple testing of Langfuse on AWS (not for production), you can use the [langfuse-aws](langfuse-aws/) directory in this repository. This is a simplified deployment based on the comprehensive guide at https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/tree/main.

The AWS deployment guide demonstrates how to deploy Langfuse on Amazon ECS with Fargate, providing a scalable, serverless container platform. It includes:
- ECS Fargate for running Langfuse containers
- RDS PostgreSQL for data persistence
- Application Load Balancer for traffic distribution
- VPC networking with proper security groups
- CloudFormation/CDK templates for infrastructure as code

**Note:** The deployment in this repository is simplified for testing purposes only. For production deployments, please refer to the full AWS guide linked above.

## Sample Projects

### [strands-langfuse](strands-langfuse/)
Integration with AWS Strands agents and Bedrock models showcasing:
- **OpenTelemetry instrumentation** - Rich trace data via OTLP protocol
- **AWS Bedrock integration** - Traces for Claude, Llama, and other Bedrock models
- **Custom attributes** - User IDs, tags, and metadata in traces
- **Automated scoring** - Response evaluation with multiple scoring methods

The demos include both basic examples and comprehensive scoring demonstrations that automatically evaluate LLM responses against expected answers.

### [ollama-langfuse](ollama-langfuse/)
Integration with local Ollama models demonstrating:
- **OpenAI-compatible API wrapping** - Automatically traces all Ollama API calls
- **Session tracking** - Groups related conversations together
- **Deterministic trace IDs** - Reliable trace identification via metadata
- **Local LLM observability** - Monitor performance of models running on your machine

Run the basic demo to see simple question-answering traced in Langfuse, or try the Monty Python demo for multi-turn conversations with session tracking.

### [langfuse-aws](langfuse-aws/)
Infrastructure as code for deploying Langfuse on AWS (deployment scripts, not demos).

## Running Examples

Each demo directory contains:
- Python example scripts (basic and themed demos)
- `run_and_validate.py` - Runs examples and verifies trace creation
- `run_scoring_and_validate.py` - Runs scoring demos with validation
- `view_traces.py` - Views recent traces via Langfuse API
- `.env` file with required configuration

## Prerequisites

- Langfuse instance (local or cloud)
- Python environment with dependencies from `requirements.txt`
- For Ollama examples: Local Ollama service running on port 11434
- For AWS examples: Valid AWS credentials and Bedrock access