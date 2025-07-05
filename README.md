# Langfuse Integration Samples

This repository contains example integrations demonstrating how to use Langfuse observability with various LLM frameworks.

## Quick Start

### 1. Setup Repository
```bash
# Clone and setup
git clone https://github.com/retroryan/langfuse-samples
cd langfuse-samples

# Run setup script for guided installation
python setup.py

# Or check current setup
python setup.py --check
```

### 2. Choose Your Integration

## Getting Started with Langfuse

Choose one of these options to get a Langfuse instance running:

### Option A: Local Setup (Recommended for Development)
```bash
git clone https://github.com/langfuse/langfuse
cd langfuse
docker-compose up
```
This will start Langfuse locally at http://localhost:3000

### Option B: AWS Deployment

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

### Quick Commands
```bash
# Using Makefile (recommended)
make help          # Show all available commands
make setup         # Interactive setup for all components
make check         # Validate current setup
make test          # Run all integration tests

# Using setup script directly
python setup.py    # Interactive setup
python setup.py --check --component ollama  # Check specific component
```

### Manual Setup

Each demo directory contains:
- Python example scripts (basic and themed demos)
- `run_and_validate.py` - Runs examples and verifies trace creation
- `run_scoring_and_validate.py` - Runs scoring demos with validation
- `view_traces.py` - Views recent traces via Langfuse API
- `.env` file with required configuration

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **"No .env file found"** | Run `python setup.py` or copy from `.env.example` files |
| **"Langfuse connection failed"** | Ensure Langfuse is running and API keys are correct |
| **"Ollama not accessible"** | Start Ollama with `ollama serve` and pull required models |
| **"AWS credentials not found"** | Run `aws configure` or set environment variables |
| **"No traces appearing"** | Wait a few seconds for processing, check API connectivity |

### Getting Help

1. **Check component-specific README**: Each directory has detailed setup instructions
2. **Validate setup**: Run `make check` to verify configuration  
3. **View logs**: Most scripts provide detailed error messages
4. **Clean restart**: Use `make clean` to remove temporary files

## Utility Scripts

The `utils/` directory contains helpful maintenance scripts:

- **delete_metrics.py**: Clean up Langfuse traces and scores
- See [utils/README.md](utils/README.md) for full documentation

## Prerequisites

- Langfuse instance (local or cloud)
- Python environment with dependencies from `requirements.txt`
- For Ollama examples: Local Ollama service running on port 11434
- For AWS examples: Valid AWS credentials and Bedrock access