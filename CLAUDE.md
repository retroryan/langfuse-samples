# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains sample integrations demonstrating how to use Langfuse observability with different LLM frameworks and services. It includes examples for:

- **ollama-langfuse**: Integration with local Ollama models using OpenAI-compatible API
- **strands-langfuse**: Integration with AWS Strands agents and Bedrock models using OpenTelemetry
- **langfuse-aws**: Cost-optimized AWS CDK deployment of Langfuse infrastructure (~$75-100/month)

## Common Development Commands

### Python Setup

All projects require Python 3.12.10 managed via pyenv:
```bash
# Set Python version (required for all projects)
pyenv local 3.12.10
```

### Python Examples (ollama-langfuse, strands-langfuse)

```bash
# Install dependencies for a specific example
cd [example-directory]
pip install -r requirements.txt

# Run basic examples
python [framework]_langfuse_example.py
python [framework]_langfuse_demo.py

# Run Monty Python themed demos
python [framework]_monty_python_demo.py

# Run scoring demos (automated response evaluation)
python [framework]_scoring_demo.py
python [framework]_scoring_demo_advanced.py  # ollama only

# Run with validation (checks traces were created)
python run_and_validate.py        # Runs Monty Python demo by default
python run_and_validate.py basic  # Runs basic example

# Run scoring with validation
python run_scoring_and_validate.py

# View recent traces via API
python view_traces.py

# Debug utilities (root level)
python debug_scores_api.py        # Debug score API endpoints
python debug_scores_detailed.py   # Detailed score debugging
python delete_metrics.py          # Clean up test metrics
```

### AWS Deployment (langfuse-aws)

```bash
# Install CDK dependencies
cd langfuse-aws
pip install -r requirements.txt

# Deploy Langfuse infrastructure
python prepare-cdk.py           # Generate secrets and config
python deploy-cdk.py           # Deploy all stacks (~15-20 minutes)

# Monitor costs
python cost-monitor.py          # Today's costs
python cost-monitor.py --weekly # Past week's costs

# CDK commands
cdk synth                      # Generate CloudFormation
cdk list                       # List all stacks
cdk diff                       # Show changes
cdk destroy --force --all      # Clean up all resources
```

### Environment Setup

Each example directory contains a `.env` file with configuration:
- **ollama-langfuse**: Points to local Langfuse (http://localhost:3000)
- **strands-langfuse**: Requires AWS credentials and Bedrock configuration
- **langfuse-aws**: AWS credentials auto-configured by deployment scripts

Common environment variables:
- `LANGFUSE_PUBLIC_KEY`: Public API key
- `LANGFUSE_SECRET_KEY`: Secret API key
- `LANGFUSE_HOST`: Langfuse instance URL
- `AWS_REGION`, `BEDROCK_REGION`, `BEDROCK_MODEL_ID`: For AWS examples

## High-Level Architecture

### Integration Patterns

1. **Ollama Integration**
   - Uses Langfuse's OpenAI SDK wrapper
   - Automatically traces OpenAI-compatible API calls
   - Requires local Ollama service running on port 11434
   - Supports deterministic trace IDs via metadata

2. **Strands Integration**
   - Uses OpenTelemetry (OTEL) instrumentation
   - Sends traces via OTLP protocol to Langfuse
   - Supports rich trace attributes (session ID, user ID, tags)
   - Includes retry logic for trace discovery
   - Lambda deployment examples in `strands-langfuse/lambda/`

### Key Components

- **Trace Validation**: Each example includes `run_and_validate.py` that:
  - Checks service availability
  - Runs the example with unique session ID
  - Queries Langfuse API to verify traces were created
  - Displays trace metrics and validation results

- **Scoring System**: Automated response evaluation with:
  - Test cases with expected answers
  - Multiple scoring methods (exact match, keyword match)
  - Numeric scores (0.0-1.0) and categorical results (passed/partial/failed)
  - Intentional wrong answers to validate scoring accuracy
  - Results saved to timestamped JSON files

- **Demo Scripts**: Fun Monty Python themed examples showcasing:
  - Multi-turn conversations
  - Session tracking
  - User identification
  - Custom tags and metadata

### AWS Infrastructure (langfuse-aws)

The AWS deployment creates these resources in order:
1. ECR repositories for container images
2. VPC with public/private subnets
3. Application Load Balancer
4. RDS PostgreSQL (t4g.micro for cost optimization)
5. S3 buckets for object storage
6. ECS cluster with Fargate services:
   - Langfuse Web (port 3000)
   - Langfuse Worker (background jobs)
   - ClickHouse (analytics database)
7. Optional Redis cache (disabled by default)

## Testing Approach

Since these are example integrations, testing focuses on:
- Service connectivity (Ollama, Langfuse, AWS)
- Trace creation validation
- API response verification
- Score recording confirmation

The scoring demos use a pattern of intentional wrong answers to validate the scoring system:
- Tests ending in "_correct" should pass (score ≥ 0.8)
- Tests ending in "_wrong" should fail (score < 0.8)

## Running Local Langfuse

For development, start Langfuse locally:
```bash
# Clone and start Langfuse with Docker
git clone https://github.com/langfuse/langfuse
cd langfuse
docker-compose up
```

Access at http://localhost:3000 with default credentials displayed in console.

## Important Notes

- All examples expect Langfuse to be running (locally via Docker or cloud)
- Ollama examples require local Ollama service on port 11434
- AWS examples require valid Bedrock access in the configured region
- Token usage and latency metrics are automatically captured in traces
- The repository uses direct Python script execution without a formal build system
- No linting configuration exists - follow existing code style when contributing
- For production Langfuse deployments, refer to the official AWS guide at https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/