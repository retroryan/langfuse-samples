# Lambda Deployment Plan for Strands-Langfuse Demo

## Overview
This plan outlines the steps to convert the strands_langfuse_demo.py into a Lambda function with a Function URL for easy HTTP access.

## Architecture
- **Lambda Function**: Runs the Strands agent with Langfuse telemetry
- **Function URL**: Provides HTTP endpoint for invoking the Lambda
- **CDK Stack**: Infrastructure as code for deployment
- **Environment Variables**: Configured via CDK for Langfuse and AWS settings

## Implementation Steps

### 1. Lambda Function Structure
```
lambda/
├── lambda_handler.py      # Main Lambda handler
├── strands_demo.py        # Adapted demo code
├── requirements.txt       # Python dependencies
└── cdk/
    ├── app.py            # CDK application
    ├── stack.py          # Lambda stack definition
    ├── requirements.txt  # CDK dependencies
    └── cdk.json         # CDK configuration
```

### 2. Lambda Handler Design
- **Handler Function**: `lambda_handler.handler`
- **Input**: JSON payload with optional parameters:
  ```json
  {
    "action": "run_demo",  // or specific demo functions
    "parameters": {
      "demo_type": "basic" // basic, knowledge_base, tools, etc.
    }
  }
  ```
- **Output**: JSON response with execution results and trace URLs

### 3. Code Adaptations
- Remove infinite loops and sleep statements
- Convert print statements to structured logging
- Add error handling for Lambda context
- Ensure proper OTEL flush before Lambda terminates
- Add response formatting for API Gateway compatibility

### 4. Environment Configuration
Required Lambda environment variables:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`
- `AWS_REGION`
- `BEDROCK_REGION`
- `BEDROCK_MODEL_ID`
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
- `OTEL_EXPORTER_OTLP_TRACES_HEADERS`

### 5. CDK Stack Components
- **Lambda Function**:
  - Runtime: Python 3.11
  - Memory: 1024 MB (for model interactions)
  - Timeout: 5 minutes (300 seconds)
  - Architecture: x86_64
- **IAM Role**:
  - Bedrock model access permissions
  - CloudWatch Logs permissions
- **Function URL**:
  - Auth type: AWS_IAM or NONE (for demo)
  - CORS configuration if needed

### 6. Deployment Process
1. Install CDK dependencies
2. Build Lambda deployment package
3. Deploy CDK stack
4. Test Function URL endpoint
5. Monitor CloudWatch logs and Langfuse traces

### 7. Testing Strategy
- Unit tests for Lambda handler
- Integration tests with mock Bedrock responses
- End-to-end test via Function URL
- Trace validation in Langfuse

### 8. Security Considerations
- Store secrets in AWS Secrets Manager (production)
- Use IAM authentication for Function URL
- Implement request validation
- Add rate limiting if needed

### 9. Monitoring & Observability
- CloudWatch Logs for Lambda execution
- Langfuse for LLM trace analysis
- CloudWatch metrics for performance
- X-Ray integration (optional)

## Next Steps
1. Review and approve this plan
2. Implement Lambda handler wrapper
3. Create CDK infrastructure code
4. Test locally with SAM CLI (optional)
5. Deploy to AWS and validate

## Questions for Review
1. Should the Lambda support multiple demo types or focus on one?
   1. ** ANSWER ** Just focus on one simple demo to start - strands-langfuse/strands_langfuse_demo.py
2. What authentication method for Function URL (IAM vs public)?
   1. ** ANSWER ** - public for now and then we will lock it down.
3. Any specific error handling or retry logic needed?
   1.  ** ANSWER ** No keep it simple for this demo
4. Should we include API Gateway for more advanced features?
   1. ** ANSWER ** No keep it simple for this demo
5. Memory/timeout settings adequate for your use case?
   1. ** ANSWER ** Keep it simple for this demo

## Implementation Status

### ✅ Completed
1. Created Lambda directory structure
2. Created lambda_handler.py - simplified version that accepts a query and returns response
3. Created requirements.txt with necessary dependencies
4. Created CDK infrastructure:
   - cdk/app.py - CDK app entry point
   - cdk/stack.py - Lambda stack with public Function URL
   - cdk/requirements.txt - CDK dependencies
   - cdk.json - CDK configuration
5. Created deployment scripts:
   - deploy.py - Python deployment script (cross-platform)
   - deploy.sh - Bash deployment script
   - build_lambda.py - Lambda package builder script
6. Created README.md with documentation
7. Fixed region issue - aligned everything to us-east-1 (where Langfuse is deployed)

### ❌ Failed Attempts & Lessons Learned

1. **Docker Bundling Timeout (10+ minutes)**
   - **What Failed**: Using CDK's BundlingOptions with Docker to install dependencies
   - **Why**: Docker container spin-up and pip install inside container is very slow
   - **Error**: Command timed out after 10 minutes during `cdk deploy`
   - **Lesson**: Pre-build deployment packages instead of relying on Docker bundling

2. **PythonFunction from aws-lambda-python-alpha**
   - **What Failed**: Tried to use `aws-cdk.aws-lambda-python-alpha` module
   - **Why**: Alpha module versioning mismatch and not installed in environment
   - **Error**: `ModuleNotFoundError: No module named 'aws_cdk.aws_lambda_python_alpha'`
   - **Lesson**: Stick with standard Lambda constructs for simpler deployments

3. **AWS_REGION Environment Variable**
   - **What Failed**: Setting AWS_REGION in Lambda environment variables
   - **Why**: AWS_REGION is a reserved Lambda runtime variable
   - **Error**: `ValidationError: AWS_REGION environment variable is reserved`
   - **Lesson**: Only use BEDROCK_REGION for our custom region config

4. **Recursive CDK Asset Bundling**
   - **What Failed**: CDK tried to bundle the entire parent directory including cdk/ itself
   - **Why**: Asset bundling without proper excludes created infinite recursion
   - **Error**: `ENAMETOOLONG: name too long` with deeply nested cdk.out paths
   - **Lesson**: Use pre-built zip packages or carefully exclude directories

5. **Missing Dependencies in Lambda**
   - **What Failed**: Initial deployment without bundling resulted in ImportError
   - **Why**: Lambda doesn't include strands, langfuse, or other dependencies
   - **Error**: `Runtime.ImportModuleError: Unable to import module 'lambda_handler': No module named 'strands'`
   - **Lesson**: Must bundle all dependencies with the Lambda deployment

### ✅ Successful Approach

1. **Docker-based Deployment Package Strategy**:
   - Created `build_lambda_docker.py` to build deployment package using Docker
   - Uses `--platform linux/amd64` to ensure x86_64 architecture compatibility
   - Leverages official AWS Lambda Python 3.12 Docker image
   - Creates Linux-compatible binaries for compiled dependencies like pydantic_core

2. **Critical Fixes Applied**:
   - **Package Name**: Fixed `strands` → `strands-agents[otel]` in requirements.txt
   - **Architecture**: Forced x86_64 build with `--platform linux/amd64` in Docker
   - **Region Alignment**: Everything deployed to us-east-1 to match Langfuse

3. **Final Deployment Flow**:
   - deploy.py tries Docker build first (build_lambda_docker.py)
   - Falls back to regular build if Docker fails
   - Uses pre-built zip package with CDK deployment
   - Completes in ~2-3 minutes without timeout issues

### ⚠️ CRITICAL ISSUE: Package Name Mismatch

**Problem Discovered**: The Lambda `requirements.txt` specifies `strands>=0.2.0`, but:
- Only `strands==0.1.0` exists on PyPI (not 0.2.0)
- The actual package name is `strands-agents` (which has versions up to 0.2.1)
- The parent directory uses `strands-agents[otel]>=0.2.0` correctly

**Root Cause**: The import statements use `from strands import ...` but the package is installed as `strands-agents`. This works because:
- The `strands-agents` package installs a module named `strands`
- Local development works because the parent requirements.txt installs `strands-agents`
- Lambda deployment fails because it tries to install non-existent `strands>=0.2.0`

**Solution**: Update Lambda's `requirements.txt` to use the correct package name.

### ✅ CRITICAL FIX APPLIED

**Fixed**: Updated `lambda/requirements.txt` to use correct package name:
- Changed: `strands>=0.2.0` → `strands-agents[otel]>=0.2.0`
- This matches the parent directory's requirements and ensures proper installation

### 🎉 Final Status

**DEPLOYMENT SUCCESSFUL!**

- **Lambda Function URL**: https://3alxzbc5qmgovgdg7um4vxwvcm0njxfn.lambda-url.us-east-1.on.aws/
- **Test Results**: Lambda responds correctly to queries
- **Trace Generation**: Successfully sends traces to Langfuse via OTEL
- **Package Size**: ~89MB (within Lambda limits)

### 📋 Testing the Lambda

```bash
# Basic test
curl -X POST https://3alxzbc5qmgovgdg7um4vxwvcm0njxfn.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2+2?"}'

# Response format
{
  "success": true,
  "run_id": "3c9dfb1d",
  "timestamp": "2025-07-05T03:49:32.721542",
  "query": "What is the capital of France?",
  "response": "Paris is the capital of France.",
  "langfuse_url": "http://Langfu-LoadB-ddQ8kK3AEPfR-697964116.us-east-1.elb.amazonaws.com",
  "trace_filter": "run-3c9dfb1d"
}
```

2. **If Successful**:
   - Verify Lambda function executes correctly
   - Test Langfuse trace generation
   - Validate OTEL telemetry export
   - Update this document with successful deployment confirmation

3. **If Package Size Issues (>50MB)**:
   - Consider using Lambda Layers for dependencies per AWS best practices:
     - Create separate layer for strands-agents and dependencies
     - Create separate layer for langfuse 
     - Keep only handler code in Lambda function
   - Alternative: Use container image deployment for larger packages

4. **Production Improvements** (Future):
   - Add Lambda Layers for common dependencies (following AWS Python layer guidelines)
   - Implement proper error handling and retries
   - Add API Gateway for advanced features
   - Use Secrets Manager for credentials
   - Add CloudWatch alarms and monitoring

### 🔑 Key Insights

1. **Region Alignment**: Everything must be in us-east-1 to match Langfuse deployment
2. **Dependency Management**: Pre-building packages is more reliable than Docker bundling
3. **CDK Simplicity**: Standard Lambda constructs work better than alpha modules
4. **Best Practices**: Follow AWS documentation for Python package structure
5. **Environment Variables**: Be aware of Lambda reserved variables
6. **Package Naming**: Always verify PyPI package names match import statements

### 📝 Summary of Package Investigation

**Investigation Results**:
- The `strands` package import comes from the `strands-agents` PyPI package
- Local development uses `strands-agents[otel]>=0.2.0` (correct)
- Lambda requirements incorrectly specified `strands>=0.2.0` (doesn't exist on PyPI)
- Only `strands==0.1.0` exists on PyPI as a separate, unrelated package

**AWS Lambda Best Practices Applied**:
- Reviewed AWS documentation for Python Lambda layers
- Confirmed proper package structure with `python/` directory at root
- Identified need for `--platform manylinux2014_x86_64` for compiled dependencies
- Lambda layers recommended for large dependency sets to avoid deployment package size limits

**CDK Best Practices Applied**:
- Reviewed CDK guidance for Lambda deployments
- Confirmed pre-built package approach is appropriate
- Identified Lambda layer pattern as production best practice
- Avoided alpha modules in favor of stable constructs