#!/usr/bin/env python3
"""
Unified entry point for Strands-Langfuse demos

Usage:
    python main.py                    # Interactive menu
    python main.py scoring           # Run scoring demo
    python main.py examples          # Run multiple examples demo
    python main.py monty_python      # Run Monty Python demo
"""

import sys
from demos import scoring, examples, monty_python

DEMOS = {
    "scoring": ("Automated Scoring Demo", scoring.run_demo),
    "examples": ("Multiple Examples Demo", examples.run_demo),
    "monty_python": ("Monty Python Demo", monty_python.run_demo)
}

def show_menu():
    """Display interactive demo selection menu"""
    print("\n🚀 Strands + Langfuse Demo Selector")
    print("=" * 50)
    print("\nAvailable demos:")
    
    for i, (key, (description, _)) in enumerate(DEMOS.items(), 1):
        print(f"{i}. {description} ({key})")
    
    print("\nSelect a demo (1-3) or 'q' to quit: ", end="")
    
    choice = input().strip()
    if choice.lower() == 'q':
        return None
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(DEMOS):
            return list(DEMOS.keys())[index]
    except ValueError:
        pass
    
    print("Invalid choice. Please try again.")
    return show_menu()

def main():
    if len(sys.argv) > 1:
        demo_name = sys.argv[1].lower()
        if demo_name not in DEMOS:
            print(f"Unknown demo: {demo_name}")
            print(f"Available demos: {', '.join(DEMOS.keys())}")
            return 1
    else:
        demo_name = show_menu()
        if not demo_name:
            print("Exiting...")
            return 0
    
    description, run_func = DEMOS[demo_name]
    print(f"\n🎯 Running {description}...")
    
    try:
        session_id, trace_ids = run_func()
        print(f"\n✅ Demo completed successfully!")
        print(f"📊 Session ID: {session_id}")
        print(f"🔍 Created {len(trace_ids)} traces")
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())