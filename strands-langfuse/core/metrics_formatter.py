"""
Metrics formatter for displaying Langfuse metrics in a dashboard format.
"""
import os
from typing import Dict, Any, Optional


def format_dashboard_metrics(response: Any, trace_id: Optional[str] = None) -> str:
    """
    Format response metrics in a full dashboard format.
    
    Args:
        response: The agent response object with metrics
        trace_id: Optional trace ID to include in the output
        
    Returns:
        Formatted string with metrics dashboard
    """
    # Extract metrics
    metrics = response.metrics
    total_tokens = metrics.accumulated_usage.get('totalTokens', 0)
    input_tokens = metrics.accumulated_usage.get('inputTokens', 0)
    output_tokens = metrics.accumulated_usage.get('outputTokens', 0)
    latency_ms = metrics.accumulated_metrics.get('latencyMs', 0)
    
    # Calculate derived metrics
    latency_sec = latency_ms / 1000.0
    tokens_per_sec = total_tokens / latency_sec if latency_sec > 0 else 0
    
    # Get model info from environment or default
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'claude-3.5-sonnet')
    model_name = model_id.split('.')[-1].split('-v')[0] if '.' in model_id else model_id
    
    # Estimate cost (rough approximation - adjust based on actual pricing)
    # Example pricing: $0.003 per 1K input tokens, $0.015 per 1K output tokens
    input_cost = (input_tokens / 1000) * 0.003
    output_cost = (output_tokens / 1000) * 0.015
    estimated_cost = input_cost + output_cost
    
    # Format the dashboard
    dashboard = f"""
📊 Performance Metrics:
   ├─ Tokens: {total_tokens} total ({input_tokens} input, {output_tokens} output)
   ├─ Latency: {latency_sec:.2f} seconds
   ├─ Throughput: {tokens_per_sec:.0f} tokens/second
   ├─ Model: {model_name}"""
    
    if trace_id:
        dashboard += f"\n   ├─ Trace ID: {trace_id}"
    
    dashboard += f"\n   └─ Estimated Cost: ~${estimated_cost:.4f}"
    
    return dashboard