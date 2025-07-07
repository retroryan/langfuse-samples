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

## Quick Start

```bash
# Test locally
./test-docker.sh

# Deploy to AWS
./deploy-cfn.sh  # or: python deploy-lambda.py

# Test deployment
python test_lambda.py
```

## Architecture & Implementation

### Layer Architecture

The Lambda uses a multi-layer architecture to optimize deployment size and performance:

```
Lambda Function (50KB)
├── Lambda Handler
├── Core modules (shared utilities)
└── Demo modules (business logic)
    ↓
Strands Layer (25MB)
└── strands-agents library with OTEL support
    ↓
Base Dependencies Layer (30MB)
├── boto3 (AWS SDK)
├── langfuse (observability client)
├── opentelemetry (OTEL packages)
└── Other dependencies
```

**Key Benefits:**
- **Reduced deployment size**: Function code is only ~50KB instead of 37MB
- **Faster deployments**: Only update function code for logic changes
- **Better cold starts**: Layers are cached by Lambda service
- **Clean separation**: Business logic separated from dependencies

### Critical Implementation Details

#### 1. OpenTelemetry (OTEL) Configuration

The most critical aspect is proper OTEL configuration for Strands + Langfuse integration:

```python
# MUST set environment variables BEFORE importing strands
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"

# THEN import strands
from strands import Agent
from strands.telemetry import StrandsTelemetry

# MUST manually initialize telemetry
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
```

**Common Pitfalls:**
- ❌ Setting OTEL config after importing strands (won't work)
- ❌ Using generic OTEL endpoint `/api/public/otel` (returns 404)
- ❌ Forgetting to initialize telemetry (no traces sent)
- ✅ Use signal-specific endpoint: `/api/public/otel/v1/traces`

#### 2. Lambda Handler Structure

```python
def handler(event, context):
    """Lambda handler with demo selection support"""
    # Parse event body (handles both API Gateway and direct invocation)
    body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
    
    # Demo selection based on JSON field
    demo_name = body.get('demo', 'custom')
    
    # Session ID handling (accept from request or generate)
    session_id = body.get('session_id') or f"lambda-{demo_name}-{uuid4()}"
    
    # Route to appropriate demo
    if demo_name == 'scoring':
        # Run scoring demo
    elif demo_name == 'monty_python':
        # Run Monty Python demo
    else:
        # Default: custom query mode
```

#### 3. Environment Variables

The Lambda requires these environment variables:
- `LANGFUSE_PUBLIC_KEY`: For authentication
- `LANGFUSE_SECRET_KEY`: For authentication
- `LANGFUSE_HOST`: Langfuse instance URL
- `BEDROCK_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Model to use (e.g., Claude 3.5)
- `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS`: Set to "all" to avoid conflicts

#### 4. Build Process

The `build-layers.sh` script handles the complex build process:

1. **Uses Docker for x86_64 compatibility**:
   ```bash
   docker run --platform linux/amd64 public.ecr.aws/lambda/python:3.12
   ```

2. **Copies parent modules**:
   ```bash
   cp -r ../core build/function/
   cp -r ../demos build/function/
   ```

3. **Creates separate layers** for dependencies and Strands

### Performance Characteristics

- **Cold Start**: ~3-5 seconds (layer loading + OTEL initialization)
- **Warm Invocation**: 
  - Custom queries: 0.5-2 seconds
  - Complex demos: 30-60 seconds
- **Memory Usage**: 150-200MB of 1024MB allocated
- **Timeout**: Set to 300 seconds (5 minutes) for complex demos

### Demo Modes

The Lambda supports multiple demo modes via JSON field selection:

```json
// Custom query (default)
{"query": "What is AWS Lambda?"}

// Specific demos
{"demo": "monty_python"}
{"demo": "examples"}
{"demo": "scoring"}

// With custom session ID
{"demo": "custom", "query": "Hello", "session_id": "my-session-123"}
```

### Trace Observability

All traces are automatically sent to Langfuse with:
- **Session ID**: Groups related traces
- **User ID**: Identifies the user (set to "lambda-user")
- **Tags**: Includes demo type and run ID for filtering
- **Metrics**: Token usage, latency, model information

### Testing Approach

The `test_lambda.py` script provides comprehensive testing:

1. **Interactive Menu**:
   - Health check for basic connectivity
   - Individual demo testing
   - Custom query mode
   - Full test suite

2. **Trace Validation**:
   - Automatically checks if traces appear in Langfuse
   - Retry logic for eventual consistency
   - Detailed error reporting

3. **Performance Testing**:
   - Measures response times
   - Validates token usage reporting
   - Checks session ID handling

## Known Issues

### Scoring Demo File Write Error

The scoring demo attempts to save results to a JSON file, which fails in Lambda's read-only filesystem. See [SCORING_FIXES.md](SCORING_FIXES.md) for details and resolution steps.

## Deployment Options

### CloudFormation (Recommended)

The included CloudFormation template provides:
- IAM role with minimal required permissions
- Lambda function with proper configuration
- Function URL for easy HTTP access
- Organized outputs with example commands

### Manual Deployment

If deploying manually:
1. Create IAM role with Bedrock access
2. Build layers with Docker for Linux/x86_64
3. Upload layers and function code to Lambda
4. Set all required environment variables
5. Configure function URL or API Gateway

## Cost Optimization

- **Lambda Layers**: Reduce deployment package size
- **Memory Setting**: 1024MB provides good price/performance
- **Timeout**: 5 minutes handles all demo scenarios
- **Architecture**: x86_64 (ARM not yet supported by all dependencies)

## Troubleshooting

### No Traces in Langfuse
- Check OTEL endpoint includes `/v1/traces`
- Verify auth token is properly base64 encoded
- Ensure telemetry.tracer_provider.force_flush() is called
- Check CloudWatch logs for OTEL export errors

### Timeouts
- Complex demos can take 30-60 seconds
- Increase client timeout when testing
- Check Lambda timeout is set to 300 seconds

### Cold Start Issues
- First invocation loads layers (3-5 seconds)
- Keep Lambda warm with periodic invocations
- Consider provisioned concurrency for production

## Security Considerations

- Function URL has no authentication (demo purposes)
- Add API Gateway with auth for production use
- Store secrets in AWS Secrets Manager
- Use IAM role with minimal permissions
- Enable CloudWatch logging encryption