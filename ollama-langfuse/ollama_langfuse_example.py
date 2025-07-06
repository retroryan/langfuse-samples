"""
Ollama + Langfuse Integration Example

This example demonstrates how to trace local Ollama models using Langfuse.
Based on the official Langfuse documentation for Ollama integration.

Prerequisites:
1. Ollama must be installed and running locally
2. Pull the Llama 3.1 model: ollama pull llama3.1:8b
3. Langfuse must be running (locally via Docker or cloud)
"""

import os
import sys
from dotenv import load_dotenv
# The Langfuse OpenAI wrapper automatically intercepts all OpenAI API calls
# and creates traces in Langfuse without changing your code structure
from langfuse.openai import OpenAI

# Load environment variables
load_dotenv()

# Get model from environment or use default
model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')

def main(session_id=None):
    # Initialize the Langfuse OpenAI client
    # This looks exactly like regular OpenAI code, but behind the scenes:
    # 1. Langfuse wraps the OpenAI client class
    # 2. Every API call (chat.completions.create) is automatically traced
    # 3. Request/response data, latency, and token usage are captured
    # 4. Traces are sent asynchronously to your Langfuse instance
    client = OpenAI(
        base_url='http://localhost:11434/v1',  # Point to Ollama instead of OpenAI
        api_key='ollama',  # Required by OpenAI client but unused by Ollama
    )
    
    print("🚀 Starting Ollama + Langfuse integration example...")
    print(f"📦 Using model: {model}")
    if session_id:
        print(f"📍 Session ID: {session_id}")
    print(f"📊 Langfuse host: {os.getenv('LANGFUSE_HOST')}")
    print("-" * 50)
    
    # Example 1: Simple chat completion
    print("\n📝 Example 1: Simple chat completion with Llama 3.1")
    
    # Build metadata
    metadata = {"example": "simple-chat"}
    if session_id:
        metadata["langfuse_session_id"] = session_id
    
    # This API call looks identical to regular OpenAI usage
    # Under the covers, Langfuse:
    # 1. Intercepts this method call
    # 2. Records the start time
    # 3. Passes the call to the actual OpenAI client (pointing to Ollama)
    # 4. Captures the response, end time, and token usage
    # 5. Creates a trace with all this data
    # 6. The 'name' parameter becomes the trace name in Langfuse
    # 7. The 'metadata' dict is attached to the trace for filtering/analysis
    response = client.chat.completions.create(
        name="ollama-traces",  # Trace name in Langfuse dashboard
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's a fun fact about ocean waves that most people don't know?"}
        ],
        metadata=metadata  # Custom data attached to trace
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print("-" * 50)
    
    # Example 2: Multi-turn conversation
    print("\n💬 Example 2: Multi-turn conversation")
    
    messages = [
        {"role": "system", "content": "You are an enthusiastic oceanographer who loves sharing fascinating facts about ocean waves."},
        {"role": "user", "content": "How powerful can ocean waves get? What's the most powerful wave ever recorded?"},
        {"role": "assistant", "content": "Ocean waves can be incredibly powerful! A single breaking wave can release more than 250,000 horsepower per meter of wave crest. The most powerful wave ever recorded was the 1958 Lituya Bay megatsunami in Alaska, which reached an astounding height of 1,720 feet (524 meters) - taller than the Empire State Building! This was triggered by an earthquake-induced landslide."},
        {"role": "user", "content": "That's incredible! How tall was the biggest wave ever recorded?"}
    ]
    
    metadata = {"example": "multi-turn"}
    if session_id:
        metadata["langfuse_session_id"] = session_id
    
    response = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=messages,
        metadata=metadata
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print("-" * 50)
    
    # Example 3: Calculator assistant
    print("\n🧮 Example 3: Calculator assistant")
    
    metadata = {"example": "calculator"}
    if session_id:
        metadata["langfuse_session_id"] = session_id
    
    calc_response = client.chat.completions.create(
        name="ollama-traces",
        model=model,
        messages=[
            {"role": "system", "content": "You are a very accurate calculator. You output only the result of the calculation."},
            {"role": "user", "content": "What is 12 * 15?"}
        ],
        metadata=metadata
    )
    
    print(f"12 * 15 = {calc_response.choices[0].message.content}")
    print("-" * 50)
    
    print("\n✅ All examples completed!")
    print(f"🔍 Check your Langfuse dashboard at {os.getenv('LANGFUSE_HOST')} to see the traces.")
    if session_id:
        print(f"📍 Filter by session ID: {session_id}")
    
    # Ensure all events are sent before exiting (v3 best practice)
    # The Langfuse wrapper sends traces asynchronously in the background
    # For short-lived scripts, we need to flush the queue before exiting
    # Otherwise, the script might terminate before traces are sent
    from langfuse import get_client
    langfuse = get_client()
    langfuse.flush()

if __name__ == "__main__":
    # Check if session ID was passed as command line argument
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    main(session_id)