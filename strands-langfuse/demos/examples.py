"""
Strands Agents + Langfuse Integration Demo - Multiple Examples

This demo shows how to properly integrate Strands agents with Langfuse for observability.
It includes multiple examples showcasing different use cases with proper telemetry setup.
"""
import uuid
import time
from datetime import datetime
from typing import Tuple, List, Optional

# Initialize OTEL before importing Agent
from core.setup import initialize_langfuse_telemetry, setup_telemetry
from core.agent_factory import create_agent
from core.metrics_formatter import format_dashboard_metrics

# Initialize Langfuse OTEL
langfuse_pk, langfuse_sk, langfuse_host = initialize_langfuse_telemetry()


def demo_simple_chat(run_id: str) -> str:
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
    
    print(format_dashboard_metrics(response, trace_id=f"simple-chat-{run_id}"))
    
    print("-" * 70)
    
    return f"simple-chat-{run_id}"


def demo_multi_turn_conversation(run_id: str) -> str:
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
    
    print(format_dashboard_metrics(response1, trace_id=f"multi-turn-{run_id}-turn1"))
    
    print("-" * 70)
    
    # Second turn (references first)
    query2 = "What was his most famous military defeat?"
    print(f"\nTurn 2 - Query: {query2}")
    response2 = agent(query2)
    print(f"Turn 2 - Response: {response2}")
    
    print(format_dashboard_metrics(response2, trace_id=f"multi-turn-{run_id}-turn2"))
    
    print("-" * 70)
    
    return f"multi-turn-{run_id}"


def demo_task_specific_agent(run_id: str) -> str:
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
        
        calc_idx = calculations.index(calc)
        print(format_dashboard_metrics(result, trace_id=f"calculator-{run_id}-calc{calc_idx+1}"))
        
        if calc != calculations[-1]:  # Don't print separator after last calculation
            print("")
    
    print("-" * 70)
    
    return f"calculator-{run_id}"


def demo_creative_writing(run_id: str) -> str:
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
    
    print(format_dashboard_metrics(haiku, trace_id=f"creative-{run_id}"))
    
    print("-" * 70)
    
    return f"creative-{run_id}"


def run_demo(session_id: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Run all examples with the provided or generated session ID.
    
    Args:
        session_id: Optional session ID (will generate if not provided)
        
    Returns:
        Tuple of (session_id, trace_ids)
    """
    # Setup telemetry
    telemetry = setup_telemetry("strands-langfuse-demo")
    
    print("\n🚀 Strands Agents + Langfuse Integration Demo")
    print("=" * 70)
    print(f"📊 Langfuse host: {langfuse_host}")
    
    # Generate unique run ID for this execution
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"🎨 Run ID: {run_id}")
    print(f"⏰ Timestamp: {timestamp}")
    print("=" * 70)
    
    # If session_id provided, use it as the main session
    if not session_id:
        session_id = f"examples-demo-{timestamp}"
    
    trace_ids = []
    
    try:
        # Run all demos
        demos = [
            demo_simple_chat,
            demo_multi_turn_conversation,
            demo_task_specific_agent,
            demo_creative_writing
        ]
        
        for demo in demos:
            demo_session = demo(run_id)
            trace_ids.append(demo_session)
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
        
        return session_id, trace_ids
        
    except Exception as e:
        print(f"\n❌ Error running demos: {e}")
        import traceback
        traceback.print_exc()
        return session_id, trace_ids


if __name__ == "__main__":
    run_demo()