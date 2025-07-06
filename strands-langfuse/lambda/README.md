# Strands-Langfuse Lambda

AWS Lambda deployment of the Strands-Langfuse integration with OpenTelemetry-based observability for LLM applications using AWS Bedrock.

## Prerequisites

- **AWS CLI** configured with credentials
- **Docker** for building Lambda layers
- **Python 3.12+**
- **Environment file**: Create `../cloud.env` with:
  ```bash
  LANGFUSE_PUBLIC_KEY=your-public-key
  LANGFUSE_SECRET_KEY=your-secret-key
  LANGFUSE_HOST=http://your-langfuse-host
  BEDROCK_REGION=us-east-1
  BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
  ```

## Test Locally

```bash
# Test Lambda with Docker (no AWS credentials needed)
./test-docker.sh
```

This builds a Docker container and tests the Lambda locally. The "Unable to locate credentials" error is expected - it shows the Lambda is working but needs AWS credentials for Bedrock.

## Deploy to AWS

```bash
# Deploy Lambda to AWS
./deploy-cfn.sh
```

This script will:
1. Build Lambda layers using Docker
2. Create S3 bucket for artifacts
3. Deploy CloudFormation stack
4. Return your Lambda Function URL

## Test the Deployed Lambda

Once deployed, test with curl:

```bash
# Custom query
curl -X POST YOUR_FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"demo": "custom", "query": "What is AWS Lambda?"}'

# Run Monty Python demo
curl -X POST YOUR_FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"demo": "monty_python"}'

# Validate traces in Langfuse
python test_deployed_lambda.py
```

## Cleanup

To delete all AWS resources:

```bash
aws cloudformation delete-stack --stack-name strands-langfuse-lambda
```

## Architecture

- **Lambda Layers**: Dependencies split into base-deps and strands-layer (55MB total)
- **Function Code**: Only ~50KB (uses parent core/ and demos/ modules)
- **Deployment**: CloudFormation with public Function URL
- **Observability**: OpenTelemetry traces sent to Langfuse