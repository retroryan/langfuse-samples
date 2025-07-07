# Langfuse Integration Samples

This repository contains example integrations demonstrating how to use Langfuse observability with various LLM frameworks.

## Python Setup

Install pyenv to manage Python versions:

```bash
# macOS (using Homebrew)
brew install pyenv

# Ubuntu/Debian
curl https://pyenv.run | bash
```

Each project in this repository uses pyenv for Python version management and venv for package isolation. Navigate to the project directory and follow the setup instructions in each project's README.

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
- **Lambda deployment** - Includes Lambda function URL deployment to run demos in AWS against the Langfuse AWS deployment

Run demos locally with Python or deploy as a Lambda function URL to integrate with your AWS-deployed Langfuse instance.

### [ollama-langfuse](ollama-langfuse/)
Integration with local Ollama models demonstrating:
- **OpenAI-compatible API wrapping** - Automatically traces all Ollama API calls
- **Session tracking** - Groups related conversations together
- **Deterministic trace IDs** - Reliable trace identification via metadata
- **Local LLM observability** - Monitor performance of models running on your machine

Run the basic demo to see simple question-answering traced in Langfuse, or try the Monty Python demo for multi-turn conversations with session tracking.

### [langfuse-aws](langfuse-aws/)
Infrastructure as code for deploying Langfuse on AWS (deployment scripts, not demos).