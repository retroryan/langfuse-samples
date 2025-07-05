# Strands Agents + Langfuse Integration Example

This example demonstrates how to trace AWS Strands agents using Langfuse observability with OpenTelemetry.

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   - Copy `.env.example` to `.env` (if needed)
   - Update with your AWS and Langfuse credentials

3. **Run with validation** (recommended)
   ```bash
   python run_and_validate.py
   ```

## Prerequisites

- **AWS Credentials**: Configure via AWS CLI (`aws configure`) or environment variables
- **AWS Bedrock Access**: Ensure access to Claude models in your region
- **Langfuse**: Running locally (Docker) or cloud instance
- **Python 3.8+**: With pip for dependency installation

## Configuration

Update `.env` with your settings:
```bash
# AWS Configuration
AWS_REGION=us-west-2
BEDROCK_REGION=us-west-2
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000  # or https://cloud.langfuse.com
```

## Running Examples

### Basic Demo
```bash
# Run with automatic validation
python run_and_validate.py

# Run standalone
python strands_langfuse_demo.py
```

### Monty Python Demo
```bash
python strands_monty_python_demo.py
```

### Scoring Demo (Automated Evaluation)
```bash
# Run with validation
python run_scoring_and_validate.py

# Run standalone
python strands_scoring_demo.py
```

### View Traces
```bash
# View recent traces via API
python view_traces.py

# Or open Langfuse UI at http://localhost:3000
```

## Cleanup

### Delete All Traces
```bash
# Interactive mode (asks for confirmation)
python delete_traces.py

# Skip confirmation - use with caution!
python delete_traces.py --yes
```

### Remove Python Environment
```bash
# If using virtual environment
deactivate
rm -rf venv/

# Or remove pip packages
pip uninstall -r requirements.txt -y
```

### Clear Local Data
```bash
# Remove generated result files
rm -f scoring_results_*.json
```

## What's Included

- **strands_langfuse_demo.py** - Complete demo with 4 different agent examples
- **strands_monty_python_demo.py** - Fun themed demo showcasing trace attributes
- **strands_scoring_demo.py** - Automated response evaluation with scoring
- **run_and_validate.py** - Validation script that checks trace creation
- **view_traces.py** - Query and display traces via API

## How It Works

The integration uses OpenTelemetry (OTEL) to send traces from Strands agents to Langfuse:
- Automatic capture of all agent interactions
- Token usage and latency tracking
- Session and user identification
- Custom tags and metadata
- Programmatic scoring for evaluation

## Troubleshooting

- **No AWS credentials**: Run `aws configure` or set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
- **Bedrock access denied**: Check AWS account has Bedrock access in your region
- **Langfuse connection failed**: Ensure Langfuse is running and accessible
- **No traces appearing**: Check [KEY_STRANDS_LANGFUSE.md](KEY_STRANDS_LANGFUSE.md) for OTEL configuration

## Learn More

- [Strands Agents Documentation](https://strandsagents.com)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Integration Details](KEY_STRANDS_LANGFUSE.md)