# Strands-Langfuse Lambda Demo

AWS Lambda deployment of the Strands-Langfuse integration that demonstrates OpenTelemetry-based observability for LLM applications using AWS Bedrock. The Lambda provides a simple HTTP endpoint for querying an AI agent with automatic trace collection in Langfuse.

## Overview

This Lambda function:
- Accepts natural language queries via HTTP POST
- Uses AWS Bedrock (Claude 3.5 Sonnet) to generate responses
- Automatically sends OpenTelemetry traces to Langfuse
- Returns responses with trace IDs for debugging

## Architecture

- **Runtime**: Python 3.12 on AWS Lambda
- **API**: Function URL with public access (no auth)
- **Dependencies**: Built using Docker for Linux x86_64 compatibility
- **Deployment**: AWS CDK for infrastructure as code
- **Observability**: Langfuse via OpenTelemetry protocol

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker running locally (for building Lambda packages)
- Node.js (for CDK CLI)
- Python 3.12+
- Environment variables in `../cloud.env`:
  ```bash
  LANGFUSE_PUBLIC_KEY=your-public-key
  LANGFUSE_SECRET_KEY=your-secret-key
  LANGFUSE_HOST=http://your-langfuse-host
  BEDROCK_REGION=us-east-1
  BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
  ```

## Quick Start

Deploy the Lambda function using the provided deployment script:

```bash
# Deploy with automatic package building
python deploy.py
```

The deployment script will:
1. Load environment variables from `../cloud.env`
2. Build Lambda package using Docker (ensures Linux compatibility)
3. Bootstrap CDK if needed
4. Deploy the Lambda stack to us-east-1
5. Test the deployed function
6. Display the Function URL

## Testing the Lambda

Once deployed, test with curl:

```bash
# Basic test
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'

# Test with complex query
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the theory of relativity in simple terms"}'
```

### Response Format

```json
{
  "success": true,
  "run_id": "abc12345",
  "timestamp": "2025-01-05T12:00:00Z",
  "query": "What is the capital of France?",
  "response": "Paris is the capital of France.",
  "langfuse_url": "http://your-langfuse-host",
  "trace_filter": "run-abc12345"
}
```

## Validating Traces

Run the test script to validate traces are being sent to Langfuse:

```bash
# Run multiple test queries and verify traces
python test_lambda.py
```

This script will:
- Send multiple test queries to your Lambda
- Wait for traces to appear in Langfuse
- Validate trace content and structure
- Display results and metrics

## Manual Deployment

If you prefer manual steps:

```bash
# 1. Build Lambda package with Docker
python build_lambda_docker.py

# 2. Load environment variables
export $(grep -v '^#' ../cloud.env | xargs)

# 3. Deploy with CDK
cd cdk
npm install -g aws-cdk  # if not installed
pip install -r requirements.txt
cdk bootstrap  # first time only
cdk deploy
```

## Troubleshooting

### Common Issues

1. **ImportError for pydantic_core**
   - Cause: Package built on wrong architecture
   - Fix: Use `build_lambda_docker.py` which forces x86_64

2. **502 Bad Gateway**
   - Check CloudWatch logs: `/aws/lambda/StrandsLangfuseLambdaStack-*`
   - Common causes: Missing dependencies, wrong region

3. **No traces in Langfuse**
   - Verify OTEL environment variables are set
   - Check Lambda has internet access for HTTPS
   - Ensure Langfuse host is accessible

### Viewing Logs

```bash
# Find your log group
aws logs describe-log-groups --region us-east-1 | grep -i strands

# Tail recent logs
aws logs get-log-events \
  --log-group-name /aws/lambda/StrandsLangfuseLambdaStack-* \
  --log-stream-name <stream-name> \
  --region us-east-1
```

## Cleanup

To delete all resources:

```bash
cd cdk
cdk destroy

# Confirm deletion when prompted
```

## Implementation Details

### Key Files

- `lambda_handler.py` - Main Lambda handler with Strands agent
- `requirements.txt` - Dependencies (strands-agents, langfuse, boto3)
- `build_lambda_docker.py` - Docker-based package builder
- `deploy.py` - Automated deployment script
- `test_lambda.py` - Validation script for testing traces
- `cdk/stack.py` - CDK infrastructure definition

### How It Works

1. **OTEL Configuration**: Set before importing Strands to ensure proper initialization
2. **Strands Agent**: Simple agent that answers questions using Bedrock
3. **Trace Attributes**: Each request tagged with unique run_id for filtering
4. **Error Handling**: Graceful error responses with details

### Security Notes

- Function URL is **publicly accessible** (no auth)
- For production, add authentication and rate limiting
- Consider using AWS Secrets Manager for credentials
- Review IAM permissions in `cdk/stack.py`