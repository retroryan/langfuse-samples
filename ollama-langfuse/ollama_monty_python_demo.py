"""
Ollama + Langfuse Monty Python Demo

A fun demonstration of Ollama + Langfuse integration using 
the Bridge of Death scene from Monty Python and the Holy Grail.

Prerequisites:
1. Ollama must be installed and running locally
2. Pull the Llama 3.1 model: ollama pull llama3.1:8b
3. Langfuse must be running (locally via Docker or cloud)
"""

import os
import sys
from dotenv import load_dotenv
# The magic of Langfuse: Import their OpenAI wrapper instead of the standard OpenAI
# This wrapper intercepts all API calls and automatically creates traces
# Your code stays exactly the same - just change the import!
from langfuse.openai import OpenAI
from langfuse import get_client
import time

# Load environment variables
load_dotenv()

# Get model from environment or use default
model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')

def print_scene_header():
    """Print the opening scene"""
    print("\n" + "="*70)
    print("🏰 THE BRIDGE OF DEATH - An Ollama + Langfuse Adventure 🏰")
    print("="*70)
    print("\n🧙‍♂️ BRIDGEKEEPER: Stop! Who would cross the Bridge of Death")
    print("                  must answer me these questions three,")
    print("                  ere the other side he see.\n")
    print("👑 KING ARTHUR: Ask me the questions, bridgekeeper. I am not afraid.\n")
    time.sleep(1)

def print_question_header(num, question):
    """Print question header with formatting"""
    print("\n" + "-"*70)
    print(f"❓ QUESTION {num}: {question}")
    print("-"*70)

def print_response(response, label="🤖 AI Scholar"):
    """Print AI response with formatting"""
    print(f"\n{label}: {response}")
    print("\n" + "."*70)
    time.sleep(0.5)

def print_metrics(response):
    """Print token usage metrics if available"""
    if hasattr(response, 'usage') and response.usage:
        usage = response.usage
        print(f"\n📊 Metrics:")
        print(f"   - Input tokens: {usage.prompt_tokens}")
        print(f"   - Output tokens: {usage.completion_tokens}")
        print(f"   - Total tokens: {usage.total_tokens}")

def main(session_id=None):
    # Initialize the Langfuse OpenAI client
    # This is where the magic happens:
    # 1. We're using Langfuse's OpenAI class (not the standard one)
    # 2. It behaves identically to the regular OpenAI client
    # 3. But it automatically traces every API call we make
    # 4. No need to manually create spans, traces, or events!
    client = OpenAI(
        base_url='http://localhost:11434/v1',  # Ollama's OpenAI-compatible endpoint
        api_key='ollama',  # Required but unused by Ollama
    )
    
    print_scene_header()
    print(f"\n📦 Using model: {model}")
    
    if session_id:
        print(f"\n📍 Session ID: {session_id}")
        print("=" * 70)
    
    # Question 1: The Airspeed Velocity
    print_question_header(1, "What is the airspeed velocity of an unladen swallow?")
    
    # Behind the scenes when we call create():
    # 1. Langfuse intercepts the call and starts a timer
    # 2. The request is forwarded to Ollama
    # 3. When Ollama responds, Langfuse captures:
    #    - Input/output messages
    #    - Token counts (if provided by the model)
    #    - Latency (request duration)
    #    - Any errors that occur
    # 4. A trace is created with all this data
    # 5. The metadata fields with 'langfuse_' prefix have special meaning:
    #    - langfuse_session_id: Groups related traces together
    #    - langfuse_user_id: Identifies the user
    #    - langfuse_tags: Tags for filtering/searching
    response1 = client.chat.completions.create(
        name="ollama-traces",  # This becomes the trace name
        model=model,
        messages=[
            {"role": "system", "content": "You are a medieval scholar well-versed in ornithology and Monty Python references. Be helpful but also acknowledge the humor in the questions."},
            {"role": "user", "content": "What is the airspeed velocity of an unladen swallow?"}
        ],
        metadata={
            "langfuse_session_id": session_id if session_id else "holy-grail-quest",
            "langfuse_user_id": "king-arthur",
            "langfuse_tags": ["monty-python", "bridge-of-death", "swallow-question"]
        }
    )
    
    print_response(response1.choices[0].message.content)
    print_metrics(response1)
    
    # Follow-up: The trick question
    print("\n👑 KING ARTHUR: Wait, I have a follow-up question...")
    time.sleep(1)
    
    response2 = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=[
            {"role": "system", "content": "You are a medieval scholar well-versed in ornithology and Monty Python references. Be helpful but also acknowledge the humor in the questions."},
            {"role": "user", "content": "What is the airspeed velocity of an unladen swallow?"},
            {"role": "assistant", "content": response1.choices[0].message.content},
            {"role": "user", "content": "But wait, African or European swallow?"}
        ],
        metadata={
            "langfuse_session_id": session_id if session_id else "holy-grail-quest",
            "langfuse_user_id": "king-arthur",
            "langfuse_tags": ["monty-python", "trick-question"]
        }
    )
    
    print_response(response2.choices[0].message.content)
    print_metrics(response2)
    
    # Question 2: Favorite Color
    print_question_header(2, "What is your favorite color?")
    
    response3 = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=[
            {"role": "system", "content": "You are King Arthur's AI assistant. Answer as if you were helping King Arthur cross the Bridge of Death."},
            {"role": "user", "content": "What is your favorite color?"}
        ],
        metadata={
            "langfuse_session_id": session_id if session_id else "holy-grail-quest",
            "langfuse_user_id": "king-arthur",
            "langfuse_tags": ["monty-python", "bridge-of-death", "color-question"],
            "favorite_color": "blue"
        }
    )
    
    print_response(response3.choices[0].message.content, "🤖 AI Assistant")
    print_metrics(response3)
    
    # Question 3: The Holy Grail
    print_question_header(3, "What is the secret to finding the Holy Grail?")
    
    response4 = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=[
            {"role": "system", "content": "You are a wise sage who knows about medieval quests and Monty Python humor."},
            {"role": "user", "content": "What is the secret to finding the Holy Grail?"}
        ],
        metadata={
            "langfuse_session_id": session_id if session_id else "holy-grail-quest",
            "langfuse_user_id": "king-arthur",
            "langfuse_tags": ["monty-python", "holy-grail", "quest-wisdom"],
            "quest_type": "holy-grail"
        }
    )
    
    print_response(response4.choices[0].message.content, "🧙‍♂️ Wise Sage")
    print_metrics(response4)
    
    # Bonus: Spanish Inquisition / Python Developer
    print("\n\n🎭 BONUS ROUND - NOBODY EXPECTS THE SPANISH INQUISITION!")
    print_question_header("BONUS", "What are the chief weapons of a Python developer?")
    
    response5 = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=[
            {"role": "system", "content": "You are a Python (the programming language) assistant who also loves Monty Python. Make programming jokes related to the Spanish Inquisition sketch."},
            {"role": "user", "content": "What are the chief weapons of a Python developer?"}
        ],
        metadata={
            "langfuse_session_id": session_id if session_id else "spanish-inquisition",
            "langfuse_user_id": "python-developer",
            "langfuse_tags": ["monty-python", "spanish-inquisition", "programming-humor"],
            "chief_weapons": ["surprise", "fear", "ruthless efficiency", "nice red uniforms"]
        }
    )
    
    print_response(response5.choices[0].message.content, "🐍 Python Assistant")
    print_metrics(response5)
    
    # Success!
    print("\n" + "="*70)
    print("✅ KING ARTHUR SUCCESSFULLY CROSSES THE BRIDGE!")
    print("="*70)
    print("\n🎬 THE END")
    print("\n" + "="*70)
    
    print(f"\n🔍 Check your Langfuse dashboard at {os.getenv('LANGFUSE_HOST')} to see the traces.")
    print("   You should see:")
    print("   - Multiple conversation traces with Monty Python themes")
    print("   - Session tracking (holy-grail-quest, spanish-inquisition)")
    print("   - User identification (king-arthur, python-developer)")
    print("   - Custom tags and metadata")
    print("   - Token usage and latency metrics")
    if session_id:
        print(f"\n📍 Filter by session ID: {session_id}")
    
    # Ensure all events are sent before exiting (v3 best practice)
    # Langfuse uses an async background thread to send traces
    # This is efficient but means traces might not be sent immediately
    # flush() forces all pending traces to be sent before the script exits
    langfuse = get_client()  # Gets the singleton Langfuse client instance
    langfuse.flush()  # Blocks until all traces are sent

if __name__ == "__main__":
    # Check if session ID was passed as command line argument
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    main(session_id)