#!/bin/bash
set -e

echo "🚀 Deploying Strands-Langfuse Lambda with CloudFormation..."

# Load environment variables
echo "📋 Loading environment variables..."
source ../cloud.env

# Get AWS account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")
STACK_NAME="strands-langfuse-lambda"
BUCKET_NAME="strands-langfuse-layers-${ACCOUNT_ID}-${REGION}"

echo "📦 AWS Account: $ACCOUNT_ID"
echo "📍 Region: $REGION"
echo "🪣 S3 Bucket: $BUCKET_NAME"

# Check if bucket exists, create if not
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo "🪣 Creating S3 bucket..."
    if [ "$REGION" == "us-east-1" ]; then
        aws s3 mb "s3://${BUCKET_NAME}"
    else
        aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION"
    fi
else
    echo "✅ S3 bucket already exists"
fi

# Build layers if not already built
if [ ! -f "build/base-deps-layer.zip" ] || [ ! -f "build/strands-layer.zip" ] || [ ! -f "build/function-code.zip" ]; then
    echo "🔨 Building Lambda layers..."
    ./build-layers.sh
else
    echo "✅ Build artifacts already exist"
fi

# Upload artifacts to S3
echo "📤 Uploading artifacts to S3..."
aws s3 cp build/base-deps-layer.zip "s3://${BUCKET_NAME}/layers/base-deps-layer.zip"
aws s3 cp build/strands-layer.zip "s3://${BUCKET_NAME}/layers/strands-layer.zip"
aws s3 cp build/function-code.zip "s3://${BUCKET_NAME}/layers/function-code.zip"

# Deploy CloudFormation stack
echo "🏗️  Deploying CloudFormation stack..."
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file cloudformation/template.yaml \
  --parameter-overrides \
    ArtifactsBucket="$BUCKET_NAME" \
    LangfusePublicKey="$LANGFUSE_PUBLIC_KEY" \
    LangfuseSecretKey="$LANGFUSE_SECRET_KEY" \
    LangfuseHost="$LANGFUSE_HOST" \
    BedrockRegion="$BEDROCK_REGION" \
    BedrockModelId="$BEDROCK_MODEL_ID" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset

# Get deployment outputs
echo "📋 Getting deployment information..."
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text)

CUSTOM_EXAMPLE=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`CurlExampleCustom`].OutputValue' \
  --output text)

MONTY_EXAMPLE=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`CurlExampleMontyPython`].OutputValue' \
  --output text)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 Lambda Function URL:"
echo "$FUNCTION_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Test Examples:"
echo ""
echo "1️⃣  Custom Query:"
echo "$CUSTOM_EXAMPLE"
echo ""
echo "2️⃣  Monty Python Demo:"
echo "$MONTY_EXAMPLE"
echo ""
echo "3️⃣  Validate Traces:"
echo "python test_deployed_lambda.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"