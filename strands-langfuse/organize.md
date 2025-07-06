# Strands-Langfuse Demo Reorganization Proposal

## Implementation Progress

### Phase Checklist
- [x] Phase 1: Core Infrastructure (Tasks 1-3) ✅
- [x] Phase 2: Demo Modules (Tasks 4-7) ✅
- [x] Phase 3: Main Entry Point (Task 8) ✅
- [x] Phase 4: Validation Scripts (Tasks 9-10) ✅
- [ ] Phase 5: Lambda Integration (Tasks 11-12)
- [ ] Phase 6: Infrastructure Updates (Tasks 13-15)
- [ ] Phase 7: Integration Testing (Task 16)
- [ ] Phase 8: Documentation & Cleanup (Tasks 17-18)

## Executive Summary

This proposal outlines a complete rewrite of the Strands-Langfuse demos to create a clean, modular system with:
1. Core agent functionality in reusable modules
2. A unified `main.py` entry point for demo selection
3. Lambda handler in the main directory supporting demo selection via JSON field
4. Simplified file references and imports

## Current Analysis

### Existing Demo Structure
- **strands_scoring_demo.py**: Automated scoring of LLM responses with test cases
- **strands_langfuse_demo.py**: Multiple example agents (chat, calculator, creative writing)
- **strands_monty_python_demo.py**: Fun Monty Python themed interactions

### Common Patterns Identified
All demos share:
1. Identical OTEL setup (lines 20-48 in each file)
2. Same telemetry initialization pattern
3. Similar agent creation with trace attributes
4. Consistent error handling and metrics reporting

## Proposed Architecture

### 1. New Directory Structure

```
strands-langfuse/
├── core/
│   ├── __init__.py
│   ├── setup.py          # OTEL setup and telemetry initialization
│   └── agent_factory.py  # Agent creation utilities
├── demos/
│   ├── __init__.py
│   ├── scoring.py        # Scoring demo logic
│   ├── examples.py       # Multiple examples demo logic (renamed from langfuse.py)
│   └── monty_python.py   # Monty Python demo logic
├── main.py               # Unified entry point
├── lambda_handler.py     # Lambda handler (moved to main directory)
├── run_and_validate.py   # Updated validation script
└── lambda/
    ├── build_lambda.py   # Build and deployment scripts remain here
    ├── deploy.py
    ├── requirements.txt
    └── cdk/              # CDK infrastructure code
```

### 2. Core Setup Module (`core/setup.py`) ✅

Implemented with:
- `initialize_langfuse_telemetry()` - OTEL configuration
- `setup_telemetry()` - Service-specific telemetry setup
- `get_langfuse_client()` - Client for scoring operations

### 3. Agent Factory Module (`core/agent_factory.py`) ✅

Implemented with:
- `create_bedrock_model()` - Configured Bedrock model creation
- `create_agent()` - Standardized agent creation with trace attributes
- `create_agent_with_context()` - Future support for conversation memory

### 4. Demo Modules ✅

All demo modules implemented with standardized `run_demo(session_id=None)` function:

- **`demos/scoring.py`** ✅ - Automated scoring with test cases
- **`demos/examples.py`** ✅ - Multiple example agents (chat, calculator, creative)  
- **`demos/monty_python.py`** ✅ - Fun Monty Python themed interactions

Each returns `(session_id, trace_ids)` for validation.

### 5. Unified Main Entry Point (`main.py`) ✅

Implemented with:
- Interactive menu for demo selection
- Command-line argument support
- Standardized error handling and output
- Exit codes for scripting

### 6. Lambda Handler (`lambda_handler.py`)

The Lambda handler now lives in the main directory for easier imports:

```python
"""
Lambda handler for Strands + Langfuse demos
Supports demo selection via JSON field
"""
import os
import json
import uuid
from datetime import datetime

# Initialize OTEL before any other imports
from core.setup import initialize_langfuse_telemetry, setup_telemetry
langfuse_pk, langfuse_sk, langfuse_host = initialize_langfuse_telemetry()
telemetry = setup_telemetry("lambda-strands-agents")

from core.agent_factory import create_agent, create_bedrock_model
from demos import scoring, examples, monty_python

def handler(event, context):
    """Lambda handler with demo selection support"""
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        
        # Demo selection
        demo_name = body.get('demo', 'custom')
        query = body.get('query', 'What is the capital of France?')
        
        # Generate unique run ID
        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        if demo_name == 'scoring':
            session_id, trace_ids = scoring.run_demo(f"lambda-scoring-{run_id}")
            result = {
                'demo': 'scoring',
                'test_results': len(trace_ids),
                'session_id': session_id
            }
        elif demo_name == 'monty_python':
            session_id, trace_ids = monty_python.run_demo(f"lambda-monty-{run_id}")
            result = {
                'demo': 'monty_python',
                'interactions': len(trace_ids),
                'session_id': session_id
            }
        elif demo_name == 'examples':
            session_id, trace_ids = examples.run_demo(f"lambda-examples-{run_id}")
            result = {
                'demo': 'examples',
                'examples_run': len(trace_ids),
                'session_id': session_id
            }
        else:
            # Custom query mode (existing behavior)
            agent = create_agent(
                system_prompt="You are a helpful assistant. Be concise in your responses.",
                session_id=f"lambda-custom-{run_id}",
                user_id="lambda-user",
                tags=["lambda-demo", "custom", f"run-{run_id}"]
            )
            response = agent(query)
            result = {
                'demo': 'custom',
                'query': query,
                'response': str(response),
                'metrics': {
                    'tokens': response.metrics.accumulated_usage['totalTokens'],
                    'latency_ms': response.metrics.accumulated_metrics['latencyMs']
                }
            }
        
        # Force flush telemetry
        if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
            telemetry.tracer_provider.force_flush()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'run_id': run_id,
                'timestamp': timestamp,
                'langfuse_url': langfuse_host,
                'trace_filter': f"run-{run_id}",
                **result
            })
        }
```

### 7. Updated Validation Scripts ✅

Both validation scripts have been updated:

**`run_and_validate.py`**:
- Updated to use `main.py` instead of direct script execution
- Supports all three demos: monty_python (default), examples, scoring
- Maintains existing validation logic for traces and attributes

**`run_scoring_and_validate.py`**:
- Updated to use `main.py` for demo execution
- Defaults to scoring demo for score validation
- Supports all demos with enhanced score checking for scoring demo
- Validates expected test behavior (correct vs intentionally wrong answers)

## Implementation Benefits

### 1. **Code Reusability**
- Single source of truth for OTEL setup
- Shared agent creation logic
- No duplication of configuration code

### 2. **Maintainability**
- Changes to setup affect all demos
- Easy to add new demos
- Clear separation of concerns

### 3. **User Experience**
- Interactive menu for demo selection
- Command-line arguments for automation
- Consistent interface across all demos

### 4. **Lambda Flexibility**
- Single handler supports all demos
- JSON field selection is RESTful
- Backwards compatible with custom queries

### 5. **Testing & Validation**
- Existing validation scripts continue to work
- Each demo returns standardized output
- Easy to test individual components

## Design Decisions

### Why JSON Field over Separate Handlers?

**JSON field approach (recommended):**
- Single Lambda function to maintain
- Easier deployment (one function)
- More flexible for API consumers
- Natural REST pattern
- Example: `{"demo": "scoring", "query": "optional custom query"}`

**Alternative (separate handlers) - NOT recommended:**
- Would require multiple Lambda functions
- More complex deployment
- Harder to maintain
- No significant benefits for a demo project

### Lambda Handler Location

**Why move lambda_handler.py to main directory?**
- Simpler imports (no need for `sys.path` manipulation)
- Direct access to `core/` and `demos/` modules
- Build script can still package it correctly
- Cleaner development experience

### Simplified File References

With the new structure:
- All demo code can import from `core.setup` and `core.agent_factory`
- Lambda handler can import demos directly: `from demos import scoring`
- No complex relative imports needed
- Clear module hierarchy

## Example Usage

### Running Demos Locally
```bash
# Interactive menu
python main.py

# Direct demo execution
python main.py scoring
python main.py examples
python main.py monty_python
```

### Lambda API Calls
```json
// Run scoring demo
{"demo": "scoring"}

// Run Monty Python demo
{"demo": "monty_python"}

// Custom query (default behavior)
{"query": "What is machine learning?"}

// Custom query with explicit demo selection
{"demo": "custom", "query": "Explain quantum computing"}
```

## Conclusion

This complete rewrite creates a clean, modular structure that:
- Eliminates code duplication
- Simplifies imports and file references
- Makes it easy to add new demos
- Provides a clear, understandable code organization
- Maintains all existing functionality while improving maintainability