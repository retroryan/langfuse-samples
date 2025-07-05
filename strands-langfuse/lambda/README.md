# Strands-Langfuse Lambda Demo

Simple AWS Lambda deployment of the Strands-Langfuse integration demo with a public Function URL.

## Quick Start

Deploy the Lambda function using the provided deployment script:

```bash
# Using Python script (recommended - cross-platform)
python deploy.py

# Or using bash script (Linux/Mac)
./deploy.sh
```

The deployment script will:
1. Load environment variables from `../cloud.env`
2. Build the Lambda deployment package with all dependencies
3. Install CDK dependencies
4. Deploy the Lambda stack to us-east-1 (same region as Langfuse)
5. Test the function
6. Display access details

## Manual Deployment

If you prefer to deploy manually:

```bash
# Load environment variables
export $(grep -v '^#' ../cloud.env | xargs)

# Deploy with CDK
cd cdk
pip install -r requirements.txt
cdk deploy
```

## Testing the Lambda

Once deployed, test the function with curl:

```bash
# Get the function URL from deployment output
FUNCTION_URL="https://xxx.lambda-url.region.on.aws/"

# Test query
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

## Lambda Handler

The Lambda accepts JSON input:
```json
{
  "query": "Your question here"
}
```

And returns:
```json
{
  "success": true,
  "run_id": "abc12345",
  "timestamp": "2025-01-05T12:00:00Z",
  "query": "Your question here",
  "response": "The AI response",
  "langfuse_url": "http://your-langfuse-host",
  "trace_filter": "run-abc12345"
}
```

## Cleanup

To delete the Lambda and all resources:

```bash
cd cdk
cdk destroy
```

## Files

- `lambda_handler.py` - Lambda function code
- `requirements.txt` - Python dependencies
- `deploy.py` - Cross-platform deployment script
- `deploy.sh` - Bash deployment script
- `cdk/` - CDK infrastructure code
  - `app.py` - CDK app entry point
  - `stack.py` - Lambda stack definition
  - `requirements.txt` - CDK dependencies
  - `cdk.json` - CDK configuration