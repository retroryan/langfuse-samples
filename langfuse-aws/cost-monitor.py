#!/usr/bin/env python3
"""
Monitor AWS costs for Langfuse deployment.
Shows daily costs by default, with option for weekly view.
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path


def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else "", e.returncode


def get_cost_data(start_date, end_date, granularity="DAILY"):
    """Retrieve cost data from AWS Cost Explorer."""
    # Check if cost-filter.json exists
    filter_arg = ""
    if Path("cost-filter.json").exists():
        filter_arg = "--filter file://cost-filter.json"
    
    command = f"""aws ce get-cost-and-usage \
        --time-period Start={start_date},End={end_date} \
        --granularity {granularity} \
        --metrics UnblendedCost \
        {filter_arg}"""
    
    stdout, stderr, code = run_command(command)
    
    if code != 0:
        print(f"Error retrieving cost data: {stderr}")
        sys.exit(1)
    
    return json.loads(stdout)


def format_cost(amount):
    """Format cost amount to 2 decimal places."""
    return f"${float(amount):.2f}"


def display_costs(cost_data, period_type):
    """Display cost data in a formatted table."""
    results = cost_data.get("ResultsByTime", [])
    
    if not results:
        print("No cost data available for the specified period.")
        return
    
    print(f"\n💰 AWS Costs - {period_type} View")
    print("=" * 50)
    
    total_cost = 0.0
    
    # Display header
    if period_type == "Daily":
        print(f"{'Date':<12} {'Cost':>10}")
        print("-" * 23)
    else:
        print(f"{'Period':<25} {'Cost':>10}")
        print("-" * 36)
    
    # Display costs
    for result in results:
        start = result["TimePeriod"]["Start"]
        end = result["TimePeriod"]["End"]
        amount = result["Total"]["UnblendedCost"]["Amount"]
        
        total_cost += float(amount)
        
        if period_type == "Daily":
            # For daily view, just show the date
            date = datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%d")
            print(f"{date:<12} {format_cost(amount):>10}")
        else:
            # For weekly view, show date range
            start_fmt = datetime.strptime(start, "%Y-%m-%d").strftime("%m/%d")
            end_fmt = datetime.strptime(end, "%Y-%m-%d").strftime("%m/%d/%Y")
            period = f"{start_fmt} - {end_fmt}"
            print(f"{period:<25} {format_cost(amount):>10}")
    
    print("-" * (23 if period_type == "Daily" else 36))
    print(f"{'Total':<12} {format_cost(total_cost):>10}")
    
    # Add daily average for weekly view
    if period_type == "Weekly" and len(results) > 0:
        days = sum([(datetime.strptime(r["TimePeriod"]["End"], "%Y-%m-%d") - 
                    datetime.strptime(r["TimePeriod"]["Start"], "%Y-%m-%d")).days 
                   for r in results])
        if days > 0:
            avg_daily = total_cost / days
            print(f"{'Daily Average':<12} {format_cost(avg_daily):>10}")
    
    print("\n📊 Cost Breakdown by Service:")
    print("-" * 50)
    
    # Get service breakdown if available
    service_costs = {}
    for result in results:
        if "Groups" in result:
            for group in result["Groups"]:
                service = group["Keys"][0] if group["Keys"] else "Unknown"
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                service_costs[service] = service_costs.get(service, 0) + amount
    
    if service_costs:
        # Sort by cost descending
        sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
        for service, cost in sorted_services:
            if cost > 0.01:  # Only show services with costs > $0.01
                print(f"{service:<35} {format_cost(cost):>10}")
    else:
        print("Service breakdown not available. Consider using cost-filter.json")
        print("to tag and filter your Langfuse resources.")
    
    print("\n💡 Tips:")
    print("- Create cost-filter.json to filter only Langfuse resources")
    print("- Use AWS resource tags to track Langfuse-specific costs")
    print("- Monitor RDS, ECS, and ALB costs as primary components")


def create_sample_cost_filter():
    """Create a sample cost-filter.json file."""
    sample_filter = {
        "Tags": {
            "Key": "Project",
            "Values": ["Langfuse"]
        }
    }
    
    with open("cost-filter.json", "w") as f:
        json.dump(sample_filter, f, indent=2)
    
    print("✓ Created sample cost-filter.json")
    print("  Update it with your resource tags to filter Langfuse costs")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Monitor AWS costs for Langfuse deployment")
    parser.add_argument("--weekly", action="store_true", help="Show costs for the past week")
    parser.add_argument("--create-filter", action="store_true", 
                       help="Create a sample cost-filter.json file")
    
    args = parser.parse_args()
    
    if args.create_filter:
        create_sample_cost_filter()
        return
    
    # Calculate date range
    end_date = datetime.now(timezone.utc).date()
    
    if args.weekly:
        # Past 7 days
        start_date = end_date - timedelta(days=7)
        period_type = "Weekly"
        granularity = "DAILY"
    else:
        # Current day
        start_date = end_date
        period_type = "Daily"
        granularity = "DAILY"
    
    # AWS Cost Explorer requires the end date to be exclusive (day after)
    end_date = end_date + timedelta(days=1)
    
    print(f"🔍 Retrieving AWS costs from {start_date} to {end_date}...")
    
    # Get cost data
    cost_data = get_cost_data(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        granularity
    )
    
    # Display costs
    display_costs(cost_data, period_type)


if __name__ == "__main__":
    main()