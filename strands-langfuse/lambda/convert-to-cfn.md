# Converting Strands-Langfuse Lambda to CloudFormation

## Current Implementation Status

This Lambda has been successfully refactored with a clean, layered architecture that reduces the deployment package from 37MB to ~50KB using Lambda layers. The structure is now ready for CloudFormation deployment.

### Completed Items ✅
- Clean directory structure with single lambda_handler.py
- Layer separation (base-deps and strands-layer)
- Docker-based build system for x86_64 compatibility
- Local testing with Docker
- Environment variable management from parent cloud.env
- Removed all legacy CDK and duplicate files

### Ready for Deployment 🚀
- [ ] Create CloudFormation template (`cloudformation/template.yaml`)
- [ ] Deploy to AWS with CloudFormation
- [ ] Test deployed Lambda function URL

## Lambda Architecture Issues and Solutions

### Original Architecture Problems

1. **Architecture Mismatch**
   - **Issue**: Building Lambda package on ARM64 Macs without Docker resulted in architecture-incompatible binaries
   - **Root Cause**: Native pip installs compile Python packages for the host architecture (ARM64), but Lambda runs on x86_64
   - **Solution**: Added `--docker` flag to build script that uses `--platform linux/amd64` to force x86_64 architecture

2. **Large Deployment Package (37MB)**
   - **Issue**: All dependencies bundled into single deployment package
   - **Root Cause**: No Lambda layers used, everything included in the zip
   - **Impact**: Slower deployments, cannot use Lambda console editor, approaching 50MB direct upload limit

3. **Dependency Management**
   - **Issue**: Mix of pure Python and compiled dependencies (e.g., cryptography, protobuf)
   - **Challenge**: Some packages like `strands` don't have pre-built wheels, requiring compilation

### Best Practices Analysis

Based on AWS CDK MCP Server Lambda Layer documentation and AWS best practices:

1. **When to Use Layers**:
   - ✅ Reduce deployment package size
   - ✅ Share dependencies across multiple functions
   - ✅ Separate function logic from dependencies
   - ✅ Enable Lambda console code editor usage
   - ❌ Not recommended for Go/Rust (compiled languages)

2. **Current Implementation vs Best Practices**:
   - ❌ No layers used - all dependencies bundled
   - ❌ 37MB package size prevents console editing
   - ✅ Correct Python 3.12 runtime
   - ✅ Docker build option for architecture compatibility

## Improved Architecture with Layers

### Proposed Layer Structure

1. **Base Dependencies Layer** (~25MB)
   - boto3, langfuse, python-dotenv
   - OpenTelemetry packages
   - Other standard dependencies

2. **Strands Agent Layer** (~10MB)
   - strands-agents[otel]
   - Associated dependencies

3. **Function Code** (~1MB)
   - lambda_handler.py
   - core/ module
   - demos/ module

### Benefits
- Function package reduced from 37MB to ~1MB
- Can use Lambda console editor
- Faster deployment iterations
- Shared layers across multiple functions

## Final Clean Architecture

### Current Directory Structure ✅
```
lambda/
├── lambda_handler.py          # Main handler (uses parent core/demos)
├── build-layers.sh            # Build script for layers
├── test-docker.sh             # Docker test script
├── layers/
│   ├── base-deps/
│   │   └── requirements.txt   # Base dependencies (boto3, langfuse, OTEL)
│   └── strands-layer/
│       └── requirements.txt   # Strands agent dependency
├── cloudformation/            # CloudFormation templates
│   └── template.yaml          # To be created
├── build/                     # Generated artifacts (gitignored)
│   ├── base-deps-layer.zip    # ~30MB
│   ├── strands-layer.zip      # ~25MB
│   └── function-code.zip      # ~50KB
└── Supporting files:
    ├── README.md              # Lambda documentation
    ├── requirements.txt       # Full dependency list
    └── test_lambda.py         # Test script for deployed Lambda
```

### Key Architecture Benefits
- **Function size reduced**: 37MB → ~50KB (99.9% reduction)
- **Layer separation**: Dependencies split into logical layers
- **Clean structure**: Single lambda_handler.py, no duplicates
- **Docker builds**: Ensures x86_64 compatibility
- **Parent module usage**: References core/ and demos/ from parent directory

### Standard CloudFormation Template

```yaml
# cloudformation/template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Strands-Langfuse Lambda with optimized layer architecture'

Parameters:
  LangfusePublicKey:
    Type: String
    Description: Langfuse public API key
    NoEcho: true
  
  LangfuseSecretKey:
    Type: String
    Description: Langfuse secret API key
    NoEcho: true
  
  LangfuseHost:
    Type: String
    Description: Langfuse host URL
    Default: http://localhost:3000
  
  BedrockRegion:
    Type: String
    Description: AWS region for Bedrock
    Default: us-east-1
  
  BedrockModelId:
    Type: String
    Description: Bedrock model ID
    Default: us.anthropic.claude-3-5-sonnet-20241022-v2:0

Resources:
  # IAM Role for Lambda
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: BedrockAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                Resource: '*'

  # Base Dependencies Layer
  BaseDependenciesLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      LayerName: strands-langfuse-base-deps
      Description: Base dependencies for Strands-Langfuse Lambda
      Content:
        S3Bucket: !Ref LayersBucket
        S3Key: layers/base-deps-layer.zip
      CompatibleRuntimes:
        - python3.12
      CompatibleArchitectures:
        - x86_64

  # Strands Agent Layer
  StrandsAgentLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      LayerName: strands-agent-layer
      Description: Strands agent dependencies
      Content:
        S3Bucket: !Ref LayersBucket
        S3Key: layers/strands-layer.zip
      CompatibleRuntimes:
        - python3.12
      CompatibleArchitectures:
        - x86_64

  # Lambda Function
  StrandsLangfuseFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: strands-langfuse-demo
      Runtime: python3.12
      Handler: lambda_handler.handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        S3Bucket: !Ref LayersBucket
        S3Key: function/function-code.zip
      Layers:
        - !Ref BaseDependenciesLayer
        - !Ref StrandsAgentLayer
      MemorySize: 1024
      Timeout: 300
      Architectures:
        - x86_64
      Environment:
        Variables:
          LANGFUSE_PUBLIC_KEY: !Ref LangfusePublicKey
          LANGFUSE_SECRET_KEY: !Ref LangfuseSecretKey
          LANGFUSE_HOST: !Ref LangfuseHost
          BEDROCK_REGION: !Ref BedrockRegion
          BEDROCK_MODEL_ID: !Ref BedrockModelId
          OTEL_PYTHON_DISABLED_INSTRUMENTATIONS: all

  # Function URL
  FunctionUrl:
    Type: AWS::Lambda::Url
    Properties:
      TargetFunctionArn: !Ref StrandsLangfuseFunction
      AuthType: NONE
      Cors:
        AllowOrigins:
          - '*'
        AllowMethods:
          - '*'
        AllowHeaders:
          - '*'

  # Permission for Function URL
  FunctionUrlPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref StrandsLangfuseFunction
      Principal: '*'
      Action: lambda:InvokeFunctionUrl
      FunctionUrlAuthType: NONE

  # S3 Bucket for Layers (created separately)
  LayersBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'strands-langfuse-layers-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled

Outputs:
  FunctionUrl:
    Description: Lambda Function URL
    Value: !GetAtt FunctionUrl.FunctionUrl
  
  FunctionArn:
    Description: Lambda Function ARN
    Value: !GetAtt StrandsLangfuseFunction.Arn
```

### Rain-Enhanced Template

```yaml
# cloudformation/rain-template.yaml
!Rain::Module Version: 0.1
Description: |
  Strands-Langfuse Lambda with Rain enhancements
  Uses Rain directives for better template management

Parameters:
  # Parameters loaded from environment or config file
  LangfusePublicKey: !Rain::Env LANGFUSE_PUBLIC_KEY
  LangfuseSecretKey: !Rain::Env LANGFUSE_SECRET_KEY
  LangfuseHost: 
    Default: !Rain::Env LANGFUSE_HOST
    Type: String
  BedrockRegion:
    Default: !Rain::Env BEDROCK_REGION
    Type: String
  BedrockModelId:
    Default: !Rain::Env BEDROCK_MODEL_ID
    Type: String

Resources:
  # IAM Role with inline policy document
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument: !Rain::Include iam/trust-policy.json
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: BedrockAccess
          PolicyDocument: !Rain::Include iam/bedrock-policy.json

  # Layers with automatic packaging
  BaseDependenciesLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      LayerName: strands-langfuse-base-deps
      Description: Base dependencies for Strands-Langfuse Lambda
      Content: !Rain::S3
        Path: ../layers/base-deps
        BucketProperty: Bucket
        KeyProperty: Key
      CompatibleRuntimes:
        - python3.12
      CompatibleArchitectures:
        - x86_64

  StrandsAgentLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      LayerName: strands-agent-layer
      Description: Strands agent dependencies
      Content: !Rain::S3
        Path: ../layers/strands-layer
        BucketProperty: Bucket
        KeyProperty: Key
      CompatibleRuntimes:
        - python3.12
      CompatibleArchitectures:
        - x86_64

  # Lambda Function with embedded code
  StrandsLangfuseFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: strands-langfuse-demo
      Runtime: python3.12
      Handler: lambda_handler.handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code: !Rain::S3
        Path: ../src
        BucketProperty: Bucket
        KeyProperty: Key
      Layers:
        - !Ref BaseDependenciesLayer
        - !Ref StrandsAgentLayer
      MemorySize: 1024
      Timeout: 300
      Architectures:
        - x86_64
      Environment:
        Variables: !Rain::Include env-vars.yaml

  # Function URL configuration
  !Rain::Module URL:
    Type: ./modules/function-url.yaml
    Properties:
      FunctionName: !Ref StrandsLangfuseFunction

Outputs:
  FunctionUrl:
    Description: Lambda Function URL
    Value: !Rain::Module URL.FunctionUrl
  
  FunctionArn:
    Description: Lambda Function ARN
    Value: !GetAtt StrandsLangfuseFunction.Arn
```

### Build and Test Instructions

**1. Build Lambda Layers:**
```bash
cd lambda
./build-layers.sh
```

This script:
- Uses Docker with `--platform linux/amd64` for x86_64 compatibility
- Builds two layers: base dependencies (30MB) and Strands agent (25MB)
- Packages function code with core/demos from parent directory
- Creates zip files in `build/` directory ready for deployment

**2. Test Locally with Docker:**
```bash
cd lambda
./test-docker.sh
```

This script:
- Loads environment from parent `cloud.env`
- Builds a Docker container with all dependencies
- Runs Lambda on port 9000
- Tests both custom queries and demo modes
- Cleans up automatically after testing

**Build Results:**
- `build/base-deps-layer.zip`: 30MB (boto3, langfuse, OTEL packages)
- `build/strands-layer.zip`: 25MB (strands-agents[otel])
- `build/function-code.zip`: ~50KB (handler + core + demos)

### Deployment Instructions

```bash
# 1. Build layers
cd lambda
./build-layers.sh

# 2. Create S3 bucket for layers
BUCKET_NAME="strands-langfuse-layers-$(aws sts get-caller-identity --query Account --output text)"
aws s3 mb s3://$BUCKET_NAME

# 3. Upload layer artifacts
aws s3 cp build/ s3://$BUCKET_NAME/layers/ --recursive

# 4. Deploy with CloudFormation (using deploy-cfn.sh script)
./deploy-cfn.sh

# Or deploy manually:
source ../cloud.env
aws cloudformation create-stack \
  --stack-name strands-langfuse-lambda \
  --template-body file://cloudformation/template.yaml \
  --parameters \
    ParameterKey=LangfusePublicKey,ParameterValue=$LANGFUSE_PUBLIC_KEY \
    ParameterKey=LangfuseSecretKey,ParameterValue=$LANGFUSE_SECRET_KEY \
    ParameterKey=LangfuseHost,ParameterValue=$LANGFUSE_HOST \
    ParameterKey=BedrockRegion,ParameterValue=$BEDROCK_REGION \
    ParameterKey=BedrockModelId,ParameterValue=$BEDROCK_MODEL_ID \
  --capabilities CAPABILITY_IAM
```

### Advantages of CloudFormation/Rain Approach

1. **Infrastructure as Code**
   - Version controlled infrastructure
   - Reproducible deployments
   - Easy rollbacks

2. **Layer Management**
   - Reduced deployment size (37MB → 1MB function code)
   - Faster iterations on function code
   - Shared dependencies across functions

3. **Rain Enhancements**
   - Automatic S3 uploads with `!Rain::S3`
   - Environment variable injection with `!Rain::Env`
   - Template modularity with `!Rain::Module`
   - File inclusion with `!Rain::Include`

4. **Better Architecture**
   - Follows AWS best practices for Lambda layers
   - Proper separation of concerns
   - Docker-based builds ensure x86_64 compatibility

### Testing the Deployment

```bash
# Test the Lambda function
cd lambda
python test_lambda.py

# Or use curl directly
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name strands-langfuse-lambda \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text)

curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "custom",
    "message": "Tell me about CloudFormation"
  }'
```

### Complete Replacement Benefits

1. **Clean Architecture**
   - Proper layer separation
   - Infrastructure fully defined as code
   - No manual steps required

2. **Operational Excellence**
   - Automated builds with Docker
   - Environment configuration from cloud.env
   - Consistent deployments

3. **Developer Experience**
   - Lambda console editor enabled (1MB function)
   - Fast iteration on function code
   - Clear separation of concerns

## Summary

### What We Achieved ✅

1. **Clean Architecture**
   - Single lambda_handler.py in lambda/ directory
   - Removed all duplicate files and legacy CDK code
   - Clean separation of layers and function code

2. **Optimized Deployment**
   - Function size reduced from 37MB to ~50KB
   - Dependencies split into two logical layers
   - Docker builds ensure x86_64 compatibility

3. **Ready for Production**
   - Local testing confirmed working
   - Environment variables managed from parent cloud.env
   - CloudFormation template ready to create

### Next Steps

1. Create the CloudFormation template in `cloudformation/template.yaml`
2. Deploy to AWS using the deployment instructions above
3. Test the deployed Lambda function URL
4. Monitor traces in your Langfuse instance