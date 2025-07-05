# Strands-Langfuse Lambda Demo

AWS Lambda deployment of the Strands-Langfuse integration that demonstrates OpenTelemetry-based observability for LLM applications using AWS Bedrock. The Lambda provides a simple HTTP endpoint for querying an AI agent with automatic trace collection in Langfuse.

**Important**: This Lambda requires Langfuse to be deployed on AWS. See [../../langfuse-aws](../../langfuse-aws/) for deployment instructions.

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

- **Langfuse on AWS**: Deploy Langfuse first using [../../langfuse-aws](../../langfuse-aws/)
- **AWS CLI**: Configured with appropriate credentials
- **AWS CDK**: Install with `npm install -g aws-cdk`
- **Python 3.12+**: For running build scripts
- **Environment Configuration**: Create `../cloud.env` with your AWS Langfuse details:
  ```bash
  LANGFUSE_PUBLIC_KEY=your-public-key
  LANGFUSE_SECRET_KEY=your-secret-key
  LANGFUSE_HOST=http://your-aws-langfuse-host
  BEDROCK_REGION=us-east-1
  BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
  ```

## Quick Start

1. **Build the Lambda package**:
   ```bash
   python build_lambda.py
   ```

2. **Deploy with CDK**:
   ```bash
   cd cdk
   cdk deploy
   ```

3. **Note the Function URL** from the deployment output

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

- **CloudWatch Console**: Navigate to Lambda > StrandsLangfuseFunction > Monitor > Logs
- **Langfuse UI**: Check your AWS-deployed Langfuse instance for traces

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
- `build_lambda.py` - Package builder for Lambda deployment
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