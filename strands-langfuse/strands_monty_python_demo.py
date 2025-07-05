"""
Strands Agents + Langfuse - Monty Python Edition
A fun demo showing AWS Strands agents answering Monty Python inspired questions

This example demonstrates:
- Using AWS Strands agents with Langfuse tracing
- Multiple conversation turns with context
- Fun Monty Python themed interactions
- Rich trace attributes for better observability

Prerequisites:
1. AWS credentials must be configured
2. Langfuse must be running (locally via Docker or cloud)
3. Configure environment variables in .env file
"""

import os
import base64
import time
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
os.environ["OTEL_SERVICE_NAME"] = "strands-monty-python-demo"
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

def main():
    print("🦜 Strands Agents + Langfuse Demo: Monty Python Edition\n")
    
    print(f"📡 Sending traces to Langfuse at: {os.getenv('LANGFUSE_HOST')}")
    print(f"🔑 Using public key: {os.getenv('LANGFUSE_PUBLIC_KEY')[:20]}...")
    print()
    
    # Configure the Bedrock model
    model = BedrockModel(
        model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region=os.environ.get("BEDROCK_REGION", "us-east-1")
    )
    
    # Create the main agent with fun trace attributes
    print("🏰 Approaching the Bridge of Death...")
    print("👴 Bridgekeeper: STOP! He who would cross the Bridge of Death")
    print("                 Must answer me these questions three!")
    print("\n🤴 King Arthur: Very well, I shall consult my AI assistant...")
    print("-" * 60)
    
    # Question 1: The famous swallow question
    print("\n❓ Question 1: The Airspeed Velocity")
    
    agent1 = Agent(
        model=model,
        system_prompt="You are a medieval scholar well-versed in ornithology and Monty Python references. Be helpful but also acknowledge the humor in the questions.",
        trace_attributes={
            "session.id": "holy-grail-quest",
            "user.id": "king-arthur",
            "langfuse.tags": ["monty-python", "bridge-of-death", "swallow-question"],
            "quest.type": "bridge-crossing",
            "question.number": "1"
        }
    )
    
    response1 = agent1("What is the airspeed velocity of an unladen swallow?")
    print(f"🤖 AI Scholar: {response1}")
    print(f"\n📊 Metrics: {response1.metrics.accumulated_usage['totalTokens']} tokens, {response1.metrics.accumulated_metrics['latencyMs']}ms")
    print("-" * 60)
    
    # Question 2: The follow-up trick question
    print("\n❓ Question 2: The Clarification")
    
    # Continue with the same agent to maintain context
    agent1.trace_attributes["question.number"] = "2"
    agent1.trace_attributes["difficulty"] = "trick-question"
    
    response2 = agent1("But wait, African or European swallow?")
    print(f"🤖 AI Scholar: {response2}")
    print(f"\n📊 Metrics: {response2.metrics.accumulated_usage['totalTokens']} tokens, {response2.metrics.accumulated_metrics['latencyMs']}ms")
    print("-" * 60)
    
    # Question 3: Favorite color
    print("\n❓ Question 3: Personal Preferences")
    
    agent2 = Agent(
        model=model,
        system_prompt="You are King Arthur's AI assistant. Answer as if you were helping King Arthur cross the Bridge of Death. Be decisive about color choices.",
        trace_attributes={
            "session.id": "holy-grail-quest",
            "user.id": "king-arthur",
            "langfuse.tags": ["monty-python", "bridge-of-death", "favorite-color"],
            "question.number": "3",
            "favorite.color": "blue"  # The correct answer!
        }
    )
    
    response3 = agent2("What is your favorite color?")
    print(f"🤖 AI Assistant: {response3}")
    print("-" * 60)
    
    # Bonus: The Holy Grail quest
    print("\n🏆 Bonus Round: The Ultimate Quest")
    
    agent3 = Agent(
        model=model,
        system_prompt="You are a wise sage who knows about medieval quests and Monty Python humor. Be mystical yet funny.",
        trace_attributes={
            "session.id": "holy-grail-quest-bonus",
            "user.id": "king-arthur",
            "langfuse.tags": ["monty-python", "holy-grail", "quest-wisdom"],
            "quest.type": "grail-seeking"
        }
    )
    
    response4 = agent3("What is the secret to finding the Holy Grail?")
    print(f"🤖 Wise Sage: {response4}")
    print("-" * 60)
    
    # The Spanish Inquisition
    print("\n⚔️ NOBODY EXPECTS...")
    
    agent4 = Agent(
        model=model,
        system_prompt="You are a Python (the programming language) assistant who also loves Monty Python. Make programming jokes related to the Spanish Inquisition sketch. Be creative and funny!",
        trace_attributes={
            "session.id": "spanish-inquisition",
            "user.id": "python-developer",
            "langfuse.tags": ["monty-python", "spanish-inquisition", "programming-humor"],
            "unexpected": True,
            "chief.weapons": ["surprise", "fear", "ruthless efficiency"]
        }
    )
    
    response5 = agent4("What are the chief weapons of a Python developer?")
    print(f"🤖 Python Assistant: {response5}")
    print(f"\n📊 Total tokens used: {response5.metrics.accumulated_usage['totalTokens']}")
    print("-" * 60)
    
    print("\n🏃 *King Arthur successfully crosses the bridge*")
    print("\n🎬 THE END")
    
    print(f"\n✨ All traces sent to Langfuse! Check your dashboard at: {os.getenv('LANGFUSE_HOST')}")
    print("   Look for traces tagged with 'monty-python' and various session IDs")
    print("   - 'holy-grail-quest' for the bridge questions")
    print("   - 'holy-grail-quest-bonus' for the grail wisdom")
    print("   - 'spanish-inquisition' for the Python humor")
    
    # Force flush telemetry to ensure all traces are sent
    print("\n🔄 Flushing telemetry...")
    if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
        telemetry.tracer_provider.force_flush()
    
    # Give Langfuse time to process traces
    print("⏳ Waiting for traces to be processed...")
    time.sleep(3)
    
    print("\n✅ Done! Your traces should now be visible in Langfuse.")

if __name__ == "__main__":
    main()