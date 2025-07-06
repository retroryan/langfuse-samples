"""
Strands Agents + Langfuse - Monty Python Edition

A fun demo showing AWS Strands agents answering Monty Python inspired questions.
This example demonstrates:
- Using AWS Strands agents with Langfuse tracing
- Multiple conversation turns with context
- Fun Monty Python themed interactions
- Rich trace attributes for better observability
"""
import time
from typing import Tuple, List, Optional

# Initialize OTEL before importing Agent
from core.setup import initialize_langfuse_telemetry, setup_telemetry
from core.agent_factory import create_agent
from core.metrics_formatter import format_dashboard_metrics, TokenAggregator

# Initialize Langfuse OTEL
langfuse_pk, langfuse_sk, langfuse_host = initialize_langfuse_telemetry()


def run_demo(session_id: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Run the Monty Python themed demo with the provided or generated session ID.
    
    Args:
        session_id: Optional session ID (will generate if not provided)
        
    Returns:
        Tuple of (session_id, trace_ids)
    """
    # Setup telemetry
    telemetry = setup_telemetry("strands-monty-python-demo")
    
    # Initialize token aggregator for cost tracking
    aggregator = TokenAggregator()
    
    print("🦜 Strands Agents + Langfuse Demo: Monty Python Edition\n")
    
    print(f"📡 Sending traces to Langfuse at: {langfuse_host}")
    print(f"🔑 Using public key: {langfuse_pk[:20]}...")
    print()
    
    # Use provided session_id or generate a default one
    if not session_id:
        session_id = "holy-grail-quest"
    
    trace_ids = []
    
    # Create the main agent with fun trace attributes
    print("🏰 Approaching the Bridge of Death...")
    print("👴 Bridgekeeper: STOP! He who would cross the Bridge of Death")
    print("                 Must answer me these questions three!")
    print("\n🤴 King Arthur: Very well, I shall consult my AI assistant...")
    print("-" * 60)
    
    # Question 1: The famous swallow question
    print("\n" + "-" * 70)
    print("❓ QUESTION 1: What is the airspeed velocity of an unladen swallow?")
    print("-" * 70)
    
    agent1 = create_agent(
        system_prompt="You are a medieval scholar well-versed in ornithology and Monty Python references. Be helpful but also acknowledge the humor in the questions.",
        session_id=session_id,
        user_id="king-arthur",
        tags=["monty-python", "bridge-of-death", "swallow-question"],
        **{
            "quest.type": "bridge-crossing",
            "question.number": "1"
        }
    )
    
    response1 = agent1("What is the airspeed velocity of an unladen swallow?")
    print(f"\n🤖 AI Scholar: {response1}")
    
    print(format_dashboard_metrics(response1, trace_id=f"{session_id}-q1"))
    aggregator.add_response(response1, "Swallow Question")
    
    print("-" * 70)
    trace_ids.append(f"{session_id}-q1")
    
    # Question 2: The follow-up trick question
    print("\n" + "-" * 70)
    print("❓ QUESTION 2: But wait, African or European swallow?")
    print("-" * 70)
    
    # Update trace attributes for the second question
    agent1.trace_attributes["question.number"] = "2"
    agent1.trace_attributes["difficulty"] = "trick-question"
    
    response2 = agent1("But wait, African or European swallow?")
    print(f"\n🤖 AI Scholar: {response2}")
    
    print(format_dashboard_metrics(response2, trace_id=f"{session_id}-q2"))
    aggregator.add_response(response2, "African or European")
    
    print("-" * 70)
    trace_ids.append(f"{session_id}-q2")
    
    # Question 3: Favorite color
    print("\n" + "-" * 70)
    print("❓ QUESTION 3: What is your favorite color?")
    print("-" * 70)
    
    agent2 = create_agent(
        system_prompt="You are King Arthur's AI assistant. Answer as if you were helping King Arthur cross the Bridge of Death. Be decisive about color choices.",
        session_id=session_id,
        user_id="king-arthur",
        tags=["monty-python", "bridge-of-death", "favorite-color"],
        **{
            "question.number": "3",
            "favorite.color": "blue"  # The correct answer!
        }
    )
    
    response3 = agent2("What is your favorite color?")
    print(f"\n🤖 AI Assistant: {response3}")
    
    print(format_dashboard_metrics(response3, trace_id=f"{session_id}-q3"))
    aggregator.add_response(response3, "Favorite Color")
    
    print("-" * 70)
    trace_ids.append(f"{session_id}-q3")
    
    # Bonus: The Holy Grail quest
    print("\n" + "-" * 70)
    print("🏆 BONUS ROUND: What is the secret to finding the Holy Grail?")
    print("-" * 70)
    
    agent3 = create_agent(
        system_prompt="You are a wise sage who knows about medieval quests and Monty Python humor. Be mystical yet funny.",
        session_id=f"{session_id}-bonus",
        user_id="king-arthur",
        tags=["monty-python", "holy-grail", "quest-wisdom"],
        **{"quest.type": "grail-seeking"}
    )
    
    response4 = agent3("What is the secret to finding the Holy Grail?")
    print(f"\n🤖 Wise Sage: {response4}")
    
    print(format_dashboard_metrics(response4, trace_id=f"{session_id}-bonus"))
    aggregator.add_response(response4, "Holy Grail Secret")
    
    print("-" * 70)
    trace_ids.append(f"{session_id}-bonus")
    
    # The Spanish Inquisition
    print("\n" + "-" * 70)
    print("⚔️ NOBODY EXPECTS... THE SPANISH INQUISITION!")
    print("What are the chief weapons of a Python developer?")
    print("-" * 70)
    
    agent4 = create_agent(
        system_prompt="You are a Python (the programming language) assistant who also loves Monty Python. Make programming jokes related to the Spanish Inquisition sketch. Be creative and funny!",
        session_id="spanish-inquisition",
        user_id="python-developer",
        tags=["monty-python", "spanish-inquisition", "programming-humor"],
        **{
            "unexpected": True,
            "chief.weapons": ["surprise", "fear", "ruthless efficiency"]
        }
    )
    
    response5 = agent4("What are the chief weapons of a Python developer?")
    print(f"\n🤖 Python Assistant: {response5}")
    
    print(format_dashboard_metrics(response5, trace_id="spanish-inquisition"))
    aggregator.add_response(response5, "Spanish Inquisition")
    
    print("-" * 70)
    trace_ids.append("spanish-inquisition")
    
    print("\n" + "=" * 70)
    print("✅ KING ARTHUR SUCCESSFULLY CROSSES THE BRIDGE!")
    print("=" * 70)
    
    print("\n🎬 THE END")
    
    # Display cost summary with Monty Python theme
    cost_summary = aggregator.format_total_cost()
    # Replace the header with a themed one
    cost_summary = cost_summary.replace("💰 TOTAL COST SUMMARY", "🏺 YOUR QUEST COST SUMMARY")
    cost_summary = cost_summary.replace("Estimated Total Cost:", "Gold Pieces Required:")
    print(cost_summary)
    print(f"\n📊 Traces sent to Langfuse: {len(trace_ids)}")
    
    print("\n" + "=" * 70)
    
    print(f"\n✨ All traces sent to Langfuse! Check your dashboard at: {langfuse_host}")
    print("   Look for traces tagged with 'monty-python' and various session IDs")
    print(f"   - '{session_id}' for the bridge questions")
    print(f"   - '{session_id}-bonus' for the grail wisdom")
    print("   - 'spanish-inquisition' for the Python humor")
    
    # Force flush telemetry to ensure all traces are sent
    print("\n🔄 Flushing telemetry...")
    if hasattr(telemetry, 'tracer_provider') and hasattr(telemetry.tracer_provider, 'force_flush'):
        telemetry.tracer_provider.force_flush()
    
    # Give Langfuse time to process traces
    print("⏳ Waiting for traces to be processed...")
    time.sleep(3)
    
    print("\n✅ Done! Your traces should now be visible in Langfuse.")
    
    return session_id, trace_ids


if __name__ == "__main__":
    run_demo()