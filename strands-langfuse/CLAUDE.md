# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This directory contains AWS Strands + Langfuse integration examples demonstrating OpenTelemetry-based observability for LLM applications using AWS Bedrock. It's part of a larger repository showcasing Langfuse integrations with different LLM frameworks.

## Common Development Commands

### Setup and Configuration

```bash
# Set Python version
pyenv local 3.12.10

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Interactive setup (recommended for first-time setup)
python setup.py  # Configures AWS Bedrock and Langfuse credentials
```

### Running Examples

```bash
# Unified entry point with interactive menu
python main.py                    # Interactive demo selector
python main.py scoring           # Run scoring demo directly
python main.py monty_python      # Run Monty Python demo directly
python main.py examples          # Run multiple examples demo directly

# Legacy individual scripts (still available)
python strands_langfuse_demo.py  # Multiple agent examples
python strands_monty_python_demo.py  # Themed demo
python strands_scoring_demo.py   # Automated evaluation

# Run with validation (checks traces were created successfully)
python run_and_validate.py        # Validates Monty Python demo
python run_scoring_and_validate.py  # Validates scoring demo

# View recent traces via Langfuse API
python view_traces.py
```

### Lambda Deployment

```bash
cd lambda
python build_lambda.py           # Build Lambda deployment package
cdk deploy                       # Deploy to AWS (requires CDK)
python test_lambda.py            # Test Lambda function locally
```

### Debugging Tools (from parent directory)

```bash
cd ..
python debug_scores_api.py        # Debug score API endpoints
python debug_scores_detailed.py   # Detailed score debugging
python delete_metrics.py          # Clean up test metrics
```

## Project Structure

```
strands-langfuse/
├── main.py              # Unified entry point with interactive menu
├── setup.py             # Interactive setup script for AWS/Langfuse config
├── core/                # Core utilities
│   ├── setup.py         # OTEL configuration (MUST be imported first)
│   ├── agent_factory.py # Factory functions for creating agents
│   └── metrics_formatter.py # Dashboard metrics formatting
├── demos/               # Demo modules
│   ├── scoring.py       # Automated evaluation with batch scoring
│   ├── monty_python.py  # Fun themed demo
│   └── examples.py      # Multiple agent examples
├── lambda/              # AWS Lambda deployment
│   ├── lambda_handler.py # Lambda function code
│   ├── build_lambda.py  # Build deployment package
│   └── cdk/             # CDK infrastructure code
└── validation scripts   # Test and validate demos
    ├── run_and_validate.py
    ├── run_scoring_and_validate.py
    └── view_traces.py

```

## High-Level Architecture

### Critical Integration Pattern

The Strands + Langfuse integration uses OpenTelemetry (OTEL) protocol and requires specific configuration:

1. **Environment Variables Must Be Set Before Imports**
   ```python
   # CRITICAL: Set OTEL config BEFORE importing Strands
   os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
   os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
   
   # NOW import Strands
   from strands import Agent
   from strands.telemetry import StrandsTelemetry
   ```

2. **Explicit Telemetry Initialization Required**
   ```python
   # CRITICAL: Must manually initialize telemetry
   telemetry = StrandsTelemetry()
   telemetry.setup_otlp_exporter()
   ```

3. **Use Signal-Specific OTEL Endpoint**
   - ✅ Correct: `/api/public/otel/v1/traces`
   - ❌ Wrong: `/api/public/otel` (returns 404)

### Key Components

- **Validation System** (`run_and_validate.py`):
  - Checks AWS Bedrock connectivity
  - Verifies Langfuse service availability
  - Executes demos with unique session IDs
  - Queries Langfuse API with retry logic to confirm traces
  - Displays trace metrics and validation results

- **Scoring System** (`demos/scoring.py`):
  - Test cases with expected answers
  - Multiple scoring methods (exact match, keyword match)
  - Intentional wrong answers to validate scoring (tests ending in "_wrong" should fail)
  - Results saved to timestamped JSON files
  - Scores range from 0.0-1.0 with categorical results (passed/partial/failed)
  - Uses batch scoring approach due to OTEL trace ID constraints

- **Trace Attributes**:
  ```python
  trace_attributes={
      "session.id": "unique-session-id",     # Groups related traces
      "user.id": "user@example.com",         # Identifies the user
      "langfuse.tags": ["production", "v1"]  # Custom tags for filtering
  }
  ```

### Environment Configuration

Required environment variables in `.env`:
```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=http://localhost:3000  # or https://cloud.langfuse.com

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Testing Approach

This example repository uses validation scripts rather than unit tests:
- Service connectivity checks (AWS Bedrock, Langfuse)
- Trace creation verification with retry logic
- Score recording confirmation
- Deterministic trace IDs for reliable validation

The scoring system validates itself using intentional test patterns:
- Tests ending in "_correct" should pass (score ≥ 0.8)
- Tests ending in "_wrong" should fail (score < 0.8)

## Important Notes

- **KEY_STRANDS_LANGFUSE.md** contains critical OTEL configuration details and troubleshooting
- Requires Strands v0.2.0+ with OTEL support
- Requires Langfuse v3.0.0+ with OTEL endpoint support (upgraded from v2)
- AWS Bedrock access required in configured region
- Token usage and latency metrics are automatically captured
- Always call `telemetry.tracer_provider.force_flush()` to ensure traces are sent
- Batch scoring is used because Strands OTEL generates trace IDs automatically (can't be set deterministically)
- The `main.py` script provides a unified entry point for all demos