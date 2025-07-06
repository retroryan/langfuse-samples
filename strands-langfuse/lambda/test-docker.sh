#!/bin/bash
set -e

echo "🧪 Testing Lambda locally with Docker..."

# Load environment variables from parent cloud.env
CLOUD_ENV_PATH="$(dirname "$0")/../cloud.env"

if [ ! -f "$CLOUD_ENV_PATH" ]; then
    echo "❌ Error: cloud.env not found at $CLOUD_ENV_PATH"
    echo "Please ensure cloud.env exists in the strands-langfuse directory"
    exit 1
fi

# Load the environment variables
set -a
source "$CLOUD_ENV_PATH"
set +a
echo "✅ Environment variables loaded from cloud.env"

# Create test directory
echo "📁 Setting up test environment..."
rm -rf docker-test
mkdir -p docker-test

# Copy lambda handler
cp lambda_handler.py docker-test/

# Copy core and demos from parent
cp -r ../core docker-test/
cp -r ../demos docker-test/

# Create requirements.txt with all dependencies
cat > docker-test/requirements.txt << 'EOF'
strands-agents[otel]>=0.2.0
langfuse>=3.0.0
boto3>=1.35.0
python-dotenv>=1.0.0
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation
opentelemetry-exporter-otlp
EOF

# Create Dockerfile
cat > docker-test/Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.12

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target /opt/python

# Copy function code and modules
COPY . ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["lambda_handler.handler"]
EOF

# Build and run
cd docker-test
echo "🐳 Building Docker image..."
docker build --platform linux/amd64 -t strands-lambda-test .

echo "🚀 Starting Lambda container on port 9001..."
docker run --rm -d \
  --name strands-lambda-test \
  -p 9001:8080 \
  -e LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
  -e LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
  -e LANGFUSE_HOST="$LANGFUSE_HOST" \
  -e BEDROCK_REGION="$BEDROCK_REGION" \
  -e BEDROCK_MODEL_ID="$BEDROCK_MODEL_ID" \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  -e AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
  -e AWS_REGION="$AWS_REGION" \
  -e OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="all" \
  strands-lambda-test

# Wait for startup
echo "⏳ Waiting for Lambda runtime..."
sleep 5

# Test the Lambda
echo -e "\n📝 Testing Lambda function..."
echo "=== Test 1: Custom query ==="
curl -s -X POST "http://localhost:9001/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "demo": "custom",
    "query": "What is AWS Lambda?"
  }' | jq .

echo -e "\n=== Test 2: Monty Python demo ==="
curl -s -X POST "http://localhost:9001/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "demo": "monty_python"
  }' | jq .

# Cleanup
echo -e "\n🛑 Stopping container..."
docker stop strands-lambda-test

echo "✅ Test complete!"
echo ""
echo "📌 To test with AWS credentials, ensure your AWS CLI is configured"
echo "📌 The Lambda expects these environment variables:"
echo "   - LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST"
echo "   - BEDROCK_REGION, BEDROCK_MODEL_ID"
echo "   - AWS credentials (for Bedrock access)"