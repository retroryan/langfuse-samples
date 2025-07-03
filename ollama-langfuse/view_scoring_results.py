#!/usr/bin/env python3
"""
View and analyze scoring results from Langfuse

This script queries Langfuse for scoring data and provides analytics.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langfuse import Langfuse
import json
from collections import defaultdict

# Load environment variables
load_dotenv()

def format_score_display(score_value, score_type="NUMERIC"):
    """Format score for display with appropriate emoji"""
    if score_type == "BOOLEAN":
        return "✅ True" if score_value == 1 else "❌ False"
    elif score_type == "NUMERIC":
        if score_value >= 0.8:
            return f"✅ {score_value:.2f}"
        elif score_value >= 0.5:
            return f"⚠️  {score_value:.2f}"
        else:
            return f"❌ {score_value:.2f}"
    else:
        return str(score_value)

def main():
    # Initialize Langfuse client
    langfuse = Langfuse()
    
    print("📊 Langfuse Scoring Results Viewer")
    print(f"🌐 Host: {os.getenv('LANGFUSE_HOST')}")
    print("=" * 70)
    
    # Time range for queries
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)  # Last 24 hours
    
    print(f"\n🕐 Viewing scores from the last 24 hours")
    print(f"   From: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   To: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Fetch recent traces with scores
        print("\n🔍 Fetching scored traces...")
        
        # Note: The actual API might differ slightly
        # This is a conceptual implementation
        traces = langfuse.fetch_traces(
            from_timestamp=start_time,
            to_timestamp=end_time,
            limit=100
        )
        
        if not traces.data:
            print("No traces found in the specified time range.")
            return
        
        # Analyze scores
        all_scores = []
        score_by_name = defaultdict(list)
        score_by_category = defaultdict(list)
        traces_with_scores = 0
        
        for trace in traces.data:
            if hasattr(trace, 'scores') and trace.scores:
                traces_with_scores += 1
                for score in trace.scores:
                    score_data = {
                        'name': score.name,
                        'value': score.value,
                        'data_type': getattr(score, 'data_type', 'NUMERIC'),
                        'comment': getattr(score, 'comment', ''),
                        'trace_id': trace.id,
                        'timestamp': getattr(score, 'timestamp', trace.timestamp)
                    }
                    all_scores.append(score_data)
                    score_by_name[score.name].append(score.value)
                    
                    # Extract category from score name (e.g., "math_accuracy" -> "math")
                    if '_' in score.name:
                        category = score.name.split('_')[0]
                        score_by_category[category].append(score.value)
        
        print(f"\n📈 Found {len(all_scores)} scores across {traces_with_scores} traces")
        
        if not all_scores:
            print("No scores found. Run the scoring example first!")
            return
        
        # Overall statistics
        print("\n📊 Overall Statistics")
        print("-" * 50)
        print(f"Total scored traces: {traces_with_scores}")
        print(f"Total scores: {len(all_scores)}")
        print(f"Unique score types: {len(score_by_name)}")
        
        # Statistics by score name
        print("\n📋 Scores by Type:")
        for name, values in sorted(score_by_name.items()):
            if values:
                avg_score = sum(values) / len(values)
                min_score = min(values)
                max_score = max(values)
                print(f"\n  {name}:")
                print(f"    Count: {len(values)}")
                print(f"    Average: {format_score_display(avg_score)}")
                print(f"    Min: {format_score_display(min_score)}")
                print(f"    Max: {format_score_display(max_score)}")
        
        # Statistics by category
        if score_by_category:
            print("\n📂 Scores by Category:")
            for category, values in sorted(score_by_category.items()):
                if values:
                    avg_score = sum(values) / len(values)
                    print(f"  {category}: {format_score_display(avg_score)} (n={len(values)})")
        
        # Recent low scores (potential issues)
        print("\n⚠️  Recent Low Scores (< 0.5):")
        low_scores = [s for s in all_scores if s['value'] < 0.5]
        if low_scores:
            for score in low_scores[:5]:  # Show max 5
                print(f"  - {score['name']}: {format_score_display(score['value'])}")
                if score['comment']:
                    print(f"    Comment: {score['comment']}")
        else:
            print("  None found - all scores are >= 0.5 ✅")
        
        # Score distribution
        print("\n📊 Score Distribution:")
        bins = {
            "Excellent (0.8-1.0)": 0,
            "Good (0.6-0.79)": 0,
            "Fair (0.4-0.59)": 0,
            "Poor (0.2-0.39)": 0,
            "Very Poor (0-0.19)": 0
        }
        
        for score in all_scores:
            value = score['value']
            if value >= 0.8:
                bins["Excellent (0.8-1.0)"] += 1
            elif value >= 0.6:
                bins["Good (0.6-0.79)"] += 1
            elif value >= 0.4:
                bins["Fair (0.4-0.59)"] += 1
            elif value >= 0.2:
                bins["Poor (0.2-0.39)"] += 1
            else:
                bins["Very Poor (0-0.19)"] += 1
        
        for range_name, count in bins.items():
            percentage = (count / len(all_scores) * 100) if all_scores else 0
            bar = "█" * int(percentage / 2)  # Simple bar chart
            print(f"  {range_name}: {count:3d} ({percentage:5.1f}%) {bar}")
        
        # Export option
        print("\n💾 Export Options:")
        print("1. Export detailed scores to JSON")
        print("2. Export summary to JSON")
        print("3. Skip export")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            filename = f"scores_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(all_scores, f, indent=2, default=str)
            print(f"✅ Exported to {filename}")
        elif choice == "2":
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_scores": len(all_scores),
                "traces_with_scores": traces_with_scores,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "score_types": {
                    name: {
                        "count": len(values),
                        "average": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0
                    }
                    for name, values in score_by_name.items()
                },
                "distribution": bins
            }
            filename = f"scores_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Exported to {filename}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that Langfuse is running and accessible")
        print("2. Verify your API keys are correct")
        print("3. Run the scoring example first to generate data")
        sys.exit(1)

if __name__ == "__main__":
    main()