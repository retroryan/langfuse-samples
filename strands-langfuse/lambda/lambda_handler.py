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
        
        # Use provided session_id or generate unique run ID
        session_id = body.get('session_id')
        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        if demo_name == 'scoring':
            final_session_id = session_id or f"lambda-scoring-{run_id}"
            session_id, trace_ids, metrics = scoring.run_demo(final_session_id)
            result = {
                'demo': 'scoring',
                'test_results': len(trace_ids),
                'session_id': session_id,
                'usage_summary': metrics,
                'trace_info': {
                    'traces_created': len(trace_ids),
                    'langfuse_url': langfuse_host,
                    'view_instructions': {
                        'filter_by_run_id': f"run-{run_id}",
                        'filter_by_tags': ["strands-scoring", f"run-{run_id}"],
                        'filter_by_session_id': session_id
                    }
                }
            }
        elif demo_name == 'monty_python':
            final_session_id = session_id or f"lambda-monty-{run_id}"
            session_id, trace_ids, metrics = monty_python.run_demo(final_session_id)
            result = {
                'demo': 'monty_python',
                'interactions': len(trace_ids),
                'session_id': session_id,
                'usage_summary': metrics,
                'trace_info': {
                    'traces_created': len(trace_ids),
                    'langfuse_url': langfuse_host,
                    'view_instructions': {
                        'filter_by_run_id': f"run-{run_id}",
                        'filter_by_tags': ["monty-python", f"run-{run_id}"],
                        'filter_by_session_id': session_id
                    }
                }
            }
        elif demo_name == 'examples':
            final_session_id = session_id or f"lambda-examples-{run_id}"
            session_id, trace_ids, metrics = examples.run_demo(final_session_id)
            result = {
                'demo': 'examples',
                'examples_run': len(trace_ids),
                'session_id': session_id,
                'usage_summary': metrics,
                'trace_info': {
                    'traces_created': len(trace_ids),
                    'langfuse_url': langfuse_host,
                    'view_instructions': {
                        'filter_by_run_id': f"run-{run_id}",
                        'filter_by_tags': ["strands-demo", f"run-{run_id}"],
                        'filter_by_session_id': session_id
                    }
                }
            }
        else:
            # Custom query mode (existing behavior)
            final_session_id = session_id or f"lambda-custom-{run_id}"
            agent = create_agent(
                system_prompt="You are a helpful assistant. Be concise in your responses.",
                session_id=final_session_id,
                user_id="lambda-user",
                tags=["lambda-demo", "custom", f"run-{run_id}"]
            )
            response = agent(query)
            # Calculate cost for custom query
            input_tokens = response.metrics.accumulated_usage.get('inputTokens', 0)
            output_tokens = response.metrics.accumulated_usage.get('outputTokens', 0)
            total_tokens = response.metrics.accumulated_usage.get('totalTokens', 0)
            # Simple cost calculation (Claude 3.5 Sonnet pricing)
            estimated_cost = (input_tokens * 0.003 / 1000) + (output_tokens * 0.015 / 1000)
            
            result = {
                'demo': 'custom',
                'query': query,
                'response': str(response),
                'session_id': final_session_id,
                'usage_summary': {
                    'total_tokens': total_tokens,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'estimated_cost': round(estimated_cost, 4)
                },
                'trace_info': {
                    'traces_created': 1,
                    'langfuse_url': langfuse_host,
                    'view_instructions': {
                        'filter_by_run_id': f"run-{run_id}",
                        'filter_by_tags': ["lambda-demo", "custom", f"run-{run_id}"],
                        'filter_by_session_id': final_session_id
                    }
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