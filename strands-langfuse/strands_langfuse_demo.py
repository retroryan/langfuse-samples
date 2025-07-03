"""
Strands Agents + Langfuse Integration Demo

This demo shows how to properly integrate Strands agents with Langfuse for observability.
It includes multiple examples showcasing different use cases with proper telemetry setup.

Prerequisites:
1. AWS credentials configured for Bedrock access
2. Langfuse running (locally or cloud)
3. Environment variables configured in .env file
"""

import os
import base64
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Langfuse OTEL export - MUST be done BEFORE importing Strands
langfuse_pk = os.environ.get('LANGFUSE_PUBLIC_KEY')
langfuse_sk = os.environ.get('LANGFUSE_SECRET_KEY')
langfuse_host = os.environ.get('LANGFUSE_HOST')

# Create auth token for OTEL authentication
auth_token = base64.b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()

# CRITICAL: Set OTEL environment variables BEFORE importing Strands
# Use signal-specific endpoint for traces (not the generic /api/public/otel)
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"
os.environ["OTEL_SERVICE_NAME"] = "strands-langfuse-demo"
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.version=1.0.0,deployment.environment=demo"

# NOW import Strands after setting environment variables
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.telemetry import StrandsTelemetry

# CRITICAL: Initialize telemetry explicitly - this is not automatic!
print("🔧 Initializing StrandsTelemetry...")
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
print("✅ OTLP exporter configured")

def create_agent(system_prompt, session_id, user_id, tags):
    """Create an agent with Langfuse trace attributes"""
    model = BedrockModel(
        model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region=os.environ.get("BEDROCK_REGION", "us-west-2")
    )
    
    # These trace attributes will appear in Langfuse
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        trace_attributes={
            "session.id": session_id,  # Groups related traces
            "user.id": user_id,        # Identifies the user
            "langfuse.tags": tags      # Custom tags for filtering
        }
    )
    
    return agent

def demo_simple_chat(run_id):
    """Example 1: Simple single-turn chat"""
    print("\n📝 Example 1: Simple Chat")
    print("-" * 50)
    
    agent = create_agent(
        system_prompt="You are a helpful assistant. Be concise in your responses.",
        session_id=f"demo-simple-chat-{run_id}",
        user_id="demo-user",
        tags=["strands-demo", "simple-chat", f"run-{run_id}"]
    )
    
    query = "What is the capital of France?"
    print(f"Query: {query}")
    
    response = agent(query)
    print(f"Response: {response}")
    
    return True

def demo_multi_turn_conversation(run_id):
    """Example 2: Multi-turn conversation with context"""
    print("\n💬 Example 2: Multi-turn Conversation")
    print("-" * 50)
    
    agent = create_agent(
        system_prompt="You are a helpful history teacher. Remember our conversation context.",
        session_id=f"demo-multi-turn-{run_id}",
        user_id="demo-user",
        tags=["strands-demo", "multi-turn", f"run-{run_id}"]
    )
    
    # First turn
    query1 = "Who was Napoleon Bonaparte?"
    print(f"Turn 1 - Query: {query1}")
    response1 = agent(query1)
    print(f"Turn 1 - Response: {str(response1)[:100]}...")
    
    # Second turn (references first)
    query2 = "What was his most famous military defeat?"
    print(f"\nTurn 2 - Query: {query2}")
    response2 = agent(query2)
    print(f"Turn 2 - Response: {response2}")
    
    return True

def demo_task_specific_agent(run_id):
    """Example 3: Task-specific agent (calculator)"""
    print("\n🧮 Example 3: Task-Specific Agent (Calculator)")
    print("-" * 50)
    
    agent = create_agent(
        system_prompt="You are a calculator. Output only the numerical result, nothing else.",
        session_id=f"demo-calculator-{run_id}",
        user_id="demo-user",
        tags=["strands-demo", "calculator", f"run-{run_id}"]
    )
    
    calculations = [
        "25 * 4",
        "sqrt(144)",
        "15% of 200"
    ]
    
    for calc in calculations:
        print(f"Calculate: {calc}")
        result = agent(calc)
        print(f"Result: {result}")
    
    return True

def demo_creative_writing(run_id):
    """Example 4: Creative writing agent"""
    print("\n✍️ Example 4: Creative Writing Agent")
    print("-" * 50)
    
    agent = create_agent(
        system_prompt="You are a creative writer. Write a short, engaging haiku about the given topic.",
        session_id=f"demo-creative-{run_id}",
        user_id="demo-user",
        tags=["strands-demo", "creative", f"run-{run_id}"]
    )
    
    topic = "artificial intelligence"
    print(f"Topic: {topic}")
    
    haiku = agent(f"Write a haiku about {topic}")
    print(f"Haiku:\n{haiku}")
    
    return True

def main():
    """Run all demos"""
    print("\n🚀 Strands Agents + Langfuse Integration Demo")
    print("=" * 70)
    print(f"📊 Langfuse host: {langfuse_host}")
    print(f"🤖 Bedrock model: {os.getenv('BEDROCK_MODEL_ID')}")
    print(f"🌍 AWS region: {os.getenv('BEDROCK_REGION')}")
    
    # Generate unique run ID for this execution
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"🎨 Run ID: {run_id}")
    print(f"⏰ Timestamp: {timestamp}")
    print("=" * 70)
    
    try:
        # Run all demos
        demos = [
            demo_simple_chat,
            demo_multi_turn_conversation,
            demo_task_specific_agent,
            demo_creative_writing
        ]
        
        for demo in demos:
            success = demo(run_id)
            if not success:
                print(f"❌ Demo {demo.__name__} failed")
                return False
            time.sleep(1)  # Small delay between demos
        
        # Force flush telemetry to ensure all traces are sent
        print("\n🔄 Flushing telemetry...")
        if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
            telemetry.tracer_provider.force_flush()
        
        # Give Langfuse time to process traces
        print("⏳ Waiting for traces to be processed...")
        time.sleep(3)
        
        print("\n✅ All demos completed successfully!")
        print(f"\n🔍 View your traces in Langfuse:")
        print(f"   URL: {langfuse_host}")
        print(f"   Filter by run ID: {run_id}")
        print(f"   Filter by tags: strands-demo, run-{run_id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error running demos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)