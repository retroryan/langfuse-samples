# Strands Agents + Langfuse Integration Example

This example demonstrates how to trace AWS Strands agents using Langfuse observability with OpenTelemetry.

## Prerequisites

1. **AWS Credentials** must be configured
   - Set up AWS CLI or configure environment variables
   - Ensure you have access to AWS Bedrock in your configured region

2. **Langfuse** must be running
   - Locally via Docker on port 3000
   - Or use Langfuse cloud (update LANGFUSE_HOST in .env)

3. **Python dependencies**
   - Install using: `pip install -r requirements.txt`

## About Strands Agents

The Strands Agents SDK is AWS's toolkit for building AI agents that integrate with Amazon Bedrock and other AWS services. This example shows how to:
- Create agents with different system prompts
- Send traces to Langfuse via OpenTelemetry
- Track session IDs, user IDs, and custom tags

## Files

- `strands_langfuse_demo.py` - Complete demo showing Strands + Langfuse integration with multiple examples
- `strands_monty_python_demo.py` - Fun Monty Python themed demo with rich trace attributes
- `strands_scoring_demo.py` - Automated scoring demo that evaluates agent responses
- `run_and_validate.py` - Script to run demos and validate traces/scores via API
- `run_scoring_and_validate.py` - Enhanced validation script with scoring support
- `view_traces.py` - View recent traces from the Langfuse API
- `KEY_STRANDS_LANGFUSE.md` - Complete integration guide with solution details
- `requirements.txt` - Python dependencies
- `.env` - Environment configuration

## Configuration

The `.env` file should contain:
```
# AWS Configuration
AWS_REGION=us-west-2
BEDROCK_REGION=us-west-2
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

## Usage

### Option 1: Run the complete demo

```bash
python strands_langfuse_demo.py
```

### Option 2: Run with validation (recommended)

```bash
python run_and_validate.py
```

This will:
- Check prerequisites (AWS credentials, Langfuse connectivity)
- Run the complete demo with 4 different agent examples
- Validate traces were created with proper attributes
- Display detailed trace information

### Option 3: Run the Monty Python demo

```bash
python strands_monty_python_demo.py
```

### Option 4: View recent traces

```bash
python view_traces.py
```

### Option 5: Run the scoring demo

```bash
# Run scoring demo with validation
python run_scoring_and_validate.py scoring

# Or run directly
python strands_scoring_demo.py
```

This will:
- Test agent responses against expected answers
- Score responses using multiple methods (exact match, keyword match)
- Send scores to Langfuse (numeric and categorical)
- Save results to JSON for analysis
- Display detailed score analytics

### Option 6: Delete all traces (cleanup)

```bash
# Interactive mode with confirmation
python delete_traces.py

# Skip confirmation (use with caution!)
python delete_traces.py --yes
```

## Examples Included

### Complete Demo (`strands_langfuse_demo.py`)
1. **Simple Chat** - Basic question-answering agent
2. **Multi-turn Conversation** - Agent that maintains conversation context  
3. **Task-Specific Agent** - Calculator agent with precise outputs
4. **Creative Writing** - Agent that writes haikus

### Monty Python Demo (`strands_monty_python_demo.py`)
1. **Airspeed Velocity Question** - The famous swallow question with context
2. **Trick Follow-up** - African or European swallow clarification
3. **Favorite Color** - Bridge crossing requirements
4. **Holy Grail Wisdom** - Quest insights from a wise sage
5. **Spanish Inquisition** - Programming humor with Python references

### Scoring Demo (`strands_scoring_demo.py`)
Automated evaluation of agent responses with programmatic scoring:
1. **Math Questions** - Tests both correct and intentionally wrong answers
2. **Geography Facts** - Capital city questions with keyword matching
3. **History Questions** - Moon landing facts with context evaluation
4. **Automated Scoring** - Multiple score types (numeric, categorical)
5. **Result Analysis** - JSON output with detailed metrics

## What's happening?

The example uses Strands agents with OpenTelemetry instrumentation to automatically send traces to Langfuse. This provides:

- Automatic capture of all agent interactions
- Model usage tracking (input/output tokens)
- Latency measurements
- Session and user tracking
- Custom tags for organization
- Error tracking and debugging

### Scoring Integration
The scoring demo demonstrates external evaluation pipelines:
- Uses Langfuse SDK to add scores to existing traces
- Supports numeric scores (0.0-1.0) and categorical scores (passed/failed)
- Evaluates responses with custom logic (exact match, keyword presence)
- Tracks test metadata (category, expected answer, scoring method)
- Saves results for further analysis

## Viewing Traces

After running the example, you can view traces in two ways:

1. **Langfuse UI**: Open http://localhost:3000 in your browser
2. **API**: Use `view_traces.py` to query traces programmatically

## Key Integration Points

See [KEY_STRANDS_LANGFUSE.md](KEY_STRANDS_LANGFUSE.md) for the complete solution including:

1. **Critical Requirements**:
   - Use signal-specific OTEL endpoint: `/api/public/otel/v1/traces`
   - Explicitly initialize telemetry with `StrandsTelemetry().setup_otlp_exporter()`
   - Set environment variables BEFORE importing Strands

2. **Common Pitfalls**:
   - Don't use the generic OTEL endpoint
   - Don't expect automatic telemetry initialization
   - Don't forget to flush telemetry

## Troubleshooting

1. **AWS credentials not found**: Configure AWS CLI with `aws configure` or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
2. **Bedrock access denied**: Ensure your AWS account has access to the specified model in the configured region
3. **Langfuse not accessible**: Ensure the Docker container is running on port 3000
4. **No traces appearing**: See [KEY_STRANDS_LANGFUSE.md](KEY_STRANDS_LANGFUSE.md) for debugging tips

## Learn More

- [Strands Agents Documentation](https://strandsagents.com)
- [Langfuse Documentation](https://langfuse.com/docs)
- [AWS Bedrock Models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)