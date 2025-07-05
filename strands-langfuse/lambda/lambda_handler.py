"""
Simple Lambda handler for Strands + Langfuse demo
"""
import os
import json
import base64
import uuid
from datetime import datetime

# Configure Langfuse OTEL export - MUST be done BEFORE importing Strands
langfuse_pk = os.environ.get('LANGFUSE_PUBLIC_KEY')
langfuse_sk = os.environ.get('LANGFUSE_SECRET_KEY')
langfuse_host = os.environ.get('LANGFUSE_HOST')

# Create auth token for OTEL authentication
auth_token = base64.b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()

# Set OTEL environment variables BEFORE importing Strands
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"
os.environ["OTEL_SERVICE_NAME"] = "Lambda Strands Agents"

# NOW import Strands after setting environment variables
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.telemetry import StrandsTelemetry

# Initialize telemetry
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()

def handler(event, context):
    """Lambda handler function"""
    try:
        # Generate unique run ID
        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Extract query from event
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        query = body.get('query', 'What is the capital of France?')
        
        # Create agent
        model = BedrockModel(
            model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
            region=os.environ.get("BEDROCK_REGION", "us-east-1")
        )
        
        agent = Agent(
            model=model,
            system_prompt="You are a helpful assistant. Be concise in your responses.",
            trace_attributes={
                "session.id": f"lambda-demo-{run_id}",
                "user.id": "lambda-user",
                "langfuse.tags": ["lambda-demo", f"run-{run_id}"],
                "langfuse.name": "Lambda Strands Agents"
            }
        )
        
        # Get response
        response = agent(query)
        
        # Force flush telemetry before Lambda terminates
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
                'query': query,
                'response': str(response),
                'langfuse_url': langfuse_host,
                'trace_filter': f"run-{run_id}"
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }