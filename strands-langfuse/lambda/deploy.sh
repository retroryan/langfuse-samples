#!/bin/bash

# Deployment script for Strands-Langfuse Lambda
set -e

echo "🚀 Strands-Langfuse Lambda Deployment Script"
echo "==========================================="

# Check if cloud.env exists
if [ ! -f "../cloud.env" ]; then
    echo "❌ Error: cloud.env file not found in parent directory"
    exit 1
fi

# Load environment variables from cloud.env
echo "📋 Loading environment variables from cloud.env..."
export $(grep -v '^#' ../cloud.env | xargs)

# Check required environment variables
required_vars=("LANGFUSE_PUBLIC_KEY" "LANGFUSE_SECRET_KEY" "LANGFUSE_HOST" "BEDROCK_REGION" "BEDROCK_MODEL_ID")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables loaded successfully"
echo "   - Langfuse Host: $LANGFUSE_HOST"
echo "   - Bedrock Region: $BEDROCK_REGION"
echo "   - Bedrock Model: $BEDROCK_MODEL_ID"

# Change to CDK directory
cd cdk

# Install CDK dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment and installing CDK dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Bootstrap CDK if needed (only required once per account/region)
echo "🔧 Checking CDK bootstrap status..."
if ! npx cdk bootstrap --version-reporting false 2>/dev/null; then
    echo "📌 CDK bootstrap may be needed. Running bootstrap..."
    npx cdk bootstrap
fi

# Deploy the stack
echo "🏗️  Deploying Lambda stack..."
npx cdk deploy --require-approval never --outputs-file outputs.json

# Check if deployment was successful
if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

# Extract the function URL from outputs
echo "📤 Extracting function URL..."
FUNCTION_URL=$(python3 -c "import json; print(json.load(open('outputs.json'))['StrandsLangfuseLambdaStack']['FunctionUrl'])" 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Error: Could not extract function URL from outputs"
    exit 1
fi

echo "✅ Deployment successful!"
echo "   Function URL: $FUNCTION_URL"

# Wait a bit for the function to be fully available
echo "⏳ Waiting for Lambda to be fully available..."
sleep 5

# Test the function
echo "🧪 Testing Lambda function..."
TEST_QUERY="What is 2+2?"
echo "   Test query: $TEST_QUERY"

RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$TEST_QUERY\"}" || echo "")

if [ -z "$RESPONSE" ]; then
    echo "❌ Error: No response from Lambda function"
    exit 1
fi

# Check if response indicates success
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Lambda function test passed!"
    
    # Extract and display response details
    ANSWER=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'N/A'))" 2>/dev/null || echo "N/A")
    RUN_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('run_id', 'N/A'))" 2>/dev/null || echo "N/A")
    
    echo "   Response: $ANSWER"
    echo "   Run ID: $RUN_ID"
else
    echo "❌ Lambda function test failed"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Display access information
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📍 Access Details:"
echo "   Function URL: $FUNCTION_URL"
echo ""
echo "📝 Example Usage:"
echo ""
echo "   # Basic query"
echo "   curl -X POST $FUNCTION_URL \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"query\": \"What is the capital of France?\"}'"
echo ""
echo "   # Custom query"
echo "   curl -X POST $FUNCTION_URL \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"query\": \"Explain quantum computing in simple terms\"}'"
echo ""
echo "🔍 View Traces:"
echo "   Langfuse URL: $LANGFUSE_HOST"
echo "   Filter by: run-$RUN_ID"
echo ""
echo "🗑️  To delete the stack:"
echo "   cd cdk && cdk destroy"
echo ""

# Save deployment info
echo "{
  \"function_url\": \"$FUNCTION_URL\",
  \"langfuse_host\": \"$LANGFUSE_HOST\",
  \"deployed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"bedrock_model\": \"$BEDROCK_MODEL_ID\",
  \"bedrock_region\": \"$BEDROCK_REGION\"
}" > deployment-info.json

echo "💾 Deployment info saved to: cdk/deployment-info.json"

deactivate