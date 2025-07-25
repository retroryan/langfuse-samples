# Strands Agents + Langfuse Integration Example

This example demonstrates how to trace AWS Strands agents using Langfuse v3 observability with OpenTelemetry.

## Prerequisites

- **Python 3.11+** (3.12.10 recommended)
- **AWS Credentials**: Configure via AWS CLI (`aws configure`) or environment variables
- **AWS Bedrock Access**: Ensure access to Claude models in your region
- **Langfuse**: Running locally (Docker) or cloud instance

## Python Setup

```bash
# Set Python version for this project
pyenv local 3.12.10

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. **Run the setup script** (recommended)
   ```bash
   python setup.py
   ```
   This interactive script will:
   - Check AWS credentials and Bedrock access
   - Help you select a Bedrock model (automatically handles inference profile prefix)
   - Configure Langfuse (optional)
   - Create/update your .env file

2. **Or configure manually**
   - Copy `.env.example` to `.env` (if needed)
   - Update with your AWS and Langfuse credentials

3. **Run the demos** 
   ```bash
   python main.py                    # Interactive menu
   python main.py scoring           # Scoring demo
   python main.py monty_python      # Monty Python demo
   python main.py examples          # Multiple examples demo
   ```

## Running Examples

### Validation Scripts
```bash
# Run demos with automatic trace validation
python run_and_validate.py       # Validates Monty Python demo
python run_scoring_and_validate.py   # Validates scoring demo
```

### View Traces
```bash
# View recent traces via API
python view_traces.py

# Or open Langfuse UI at http://localhost:3000
```

## AWS Lambda Deployment

### Prerequisites
- **Langfuse deployed on AWS**: You need Langfuse running on AWS first. See [../langfuse-aws](../langfuse-aws/) for deployment instructions.

### Testing the Lambda Function

1. **Build and deploy the Lambda**:
   ```bash
   cd lambda
   python deploy-lambda.py
   ```

2. **Test the Lambda function**:
   ```bash
   python test_lambda.py
   ```

3. **Monitor traces**:
   - Open your Langfuse dashboard
   - Traces will appear under the Lambda's session

For more Lambda details, see [lambda/README.md](lambda/README.md).

## Langfuse Integration Architecture

### OTEL-Based Integration

This demo uses **OpenTelemetry (OTEL)** for tracing, which differs from Langfuse's native SDK decorators. Here's why:

1. **AWS Strands Compatibility**: Strands agents have built-in OTEL support via `strands.telemetry`
2. **Automatic Trace Propagation**: OTEL handles context propagation across nested agent calls
3. **Standards-Based**: Both Strands and Langfuse v3 are built on OpenTelemetry standards

### How It Works

The integration uses OpenTelemetry (OTEL) to send traces from Strands agents to Langfuse:
- Automatic capture of all agent interactions
- Token usage and latency tracking
- Session and user identification
- Custom tags and metadata
- Programmatic scoring for evaluation


### Key Differences from Langfuse SDK

| Feature | Langfuse SDK | Strands OTEL Integration |
|---------|--------------|-------------------------|
| Trace ID Control | Can set custom IDs | Auto-generated by OTEL |
| Decorators | `@observe` decorator | Not used |
| Context | `langfuse_context` | OTEL context |
| Scoring | Immediate with known ID | Batch scoring after trace discovery |

### Why Batch Scoring?

The scoring demo performs scoring as a separate batch operation because:

1. **No Trace ID Control**: Strands' OTEL integration generates trace IDs automatically
2. **Processing Time**: Traces need time to be processed and indexed in Langfuse
3. **Higher Success Rate**: Batch scoring after a delay ensures traces are available
4. **Natural Integration**: Shows how Strands is meant to be used without modification

```python
# Natural Strands usage - no Langfuse wrapping needed
agent = create_agent(system_prompt="...", session_id="...", tags=["..."])
response = agent("Your question")

# Later, find and score the trace
trace_id = find_trace_for_test(session_id, test_name)
langfuse_client.create_score(trace_id=trace_id, value=score)
```

### Integration Pattern

```
┌─────────────┐     OTEL      ┌──────────────┐     OTLP      ┌─────────────┐
│   Strands   │ ──────────► │ OpenTelemetry │ ──────────► │  Langfuse   │
│   Agents    │  Telemetry   │   Exporter    │  Protocol   │   Server    │
└─────────────┘              └──────────────┘              └─────────────┘
```

For detailed integration notes, see [KEY_STRANDS_LANGFUSE.md](KEY_STRANDS_LANGFUSE.md).

### What's Included

- **main.py** - Unified entry point with interactive menu or direct demo execution
- **demos/** - Organized demo modules:
  - **scoring.py** - Automated response evaluation with scoring
  - **monty_python.py** - Fun themed demo showcasing trace attributes
  - **examples.py** - Multiple agent examples demonstrating different patterns
- **core/** - Core functionality for agent creation and setup
- **run_and_validate.py** - Validation script that checks trace creation
- **view_traces.py** - Query and display traces via API



## Troubleshooting

- **No AWS credentials**: Run `aws configure` or set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
- **Bedrock access denied**: Check AWS account has Bedrock access in your region
- **"on-demand throughput isn't supported" error**: Use AWS Bedrock Inference Profiles by adding the `us.` prefix to model IDs (e.g., `us.anthropic.claude-3-5-sonnet-20241022-v2:0`). See the AWS Bedrock documentation for details
- **Langfuse connection failed**: Ensure Langfuse is running and accessible
- **No traces appearing**: Check [KEY_STRANDS_LANGFUSE.md](KEY_STRANDS_LANGFUSE.md) for OTEL configuration
- **"Unable to access Bedrock"**: Enable model access in the AWS Bedrock console for your account


## Cleanup

### Delete All Traces in Parent Directory
```bash
# Interactive mode (asks for confirmation)
python delete_traces.py

# Skip confirmation - use with caution!
python delete_traces.py --yes
```

### Clear Local Data
```bash
# Remove generated result files
rm -f scoring_results_*.json
```


## Learn More

- [Strands Agents Documentation](https://strandsagents.com)
- [Langfuse v3 Documentation](https://langfuse.com/docs)
- [Langfuse v3 Python SDK](https://langfuse.com/docs/sdk/python/sdk-v3)
- [Integration Details](KEY_STRANDS_LANGFUSE.md)