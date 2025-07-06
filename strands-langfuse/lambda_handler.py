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
        
    except Exception as e:
        print(f"Error in Lambda handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
        }