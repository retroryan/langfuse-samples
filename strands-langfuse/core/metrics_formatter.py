"""
Metrics formatter for displaying Langfuse metrics in a dashboard format.
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


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
    
    # Cost calculation moved to TokenAggregator for end-of-demo summary
    
    # Format the dashboard
    dashboard = f"""
📊 Performance Metrics:
   ├─ Tokens: {total_tokens} total ({input_tokens} input, {output_tokens} output)
   ├─ Latency: {latency_sec:.2f} seconds
   ├─ Throughput: {tokens_per_sec:.0f} tokens/second
   ├─ Model: {model_name}"""
    
    if trace_id:
        dashboard += f"\n   ├─ Trace ID: {trace_id}"
    
    dashboard += f"\n   └─ Session: {trace_id}" if trace_id else ""
    
    return dashboard


class TokenAggregator:
    """Aggregates token usage across multiple queries for cost calculation."""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.model_id = None
        
        # Pricing as of January 2025 - https://aws.amazon.com/bedrock/pricing/
        # Claude 3.7 Sonnet pricing
        self.pricing = {
            'claude-3-7-sonnet': {
                'input_per_1k': 0.003,
                'output_per_1k': 0.015
            },
            # Claude 3.5 Sonnet fallback pricing
            'claude-3-5-sonnet': {
                'input_per_1k': 0.003,
                'output_per_1k': 0.015
            },
            # Default pricing if model not found
            'default': {
                'input_per_1k': 0.003,
                'output_per_1k': 0.015
            }
        }
    
    def add_response(self, response: Any, query_name: Optional[str] = None):
        """Add a response's metrics to the aggregator."""
        metrics = response.metrics
        input_tokens = metrics.accumulated_usage.get('inputTokens', 0)
        output_tokens = metrics.accumulated_usage.get('outputTokens', 0)
        total_tokens = metrics.accumulated_usage.get('totalTokens', 0)
        latency_ms = metrics.accumulated_metrics.get('latencyMs', 0)
        
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens += total_tokens
        
        # Store model ID from first response
        if not self.model_id:
            self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'claude-3.5-sonnet')
        
        # Store query details
        self.queries.append({
            'name': query_name or f"Query {len(self.queries) + 1}",
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'latency_ms': latency_ms
        })
    
    def calculate_total_cost(self) -> float:
        """Calculate the total estimated cost."""
        # Determine pricing based on model
        model_key = 'default'
        if self.model_id:
            if 'claude-3-7-sonnet' in self.model_id.lower():
                model_key = 'claude-3-7-sonnet'
            elif 'claude-3-5-sonnet' in self.model_id.lower():
                model_key = 'claude-3-5-sonnet'
        
        pricing = self.pricing[model_key]
        input_cost = (self.total_input_tokens / 1000) * pricing['input_per_1k']
        output_cost = (self.total_output_tokens / 1000) * pricing['output_per_1k']
        
        return input_cost + output_cost
    
    def format_total_cost(self) -> str:
        """Format the total cost summary."""
        total_cost = self.calculate_total_cost()
        model_name = self.model_id.split('.')[-1].split('-v')[0] if self.model_id and '.' in self.model_id else self.model_id
        
        summary = "\n" + "=" * 70
        summary += "\n💰 TOTAL COST SUMMARY"
        summary += "\n" + "=" * 70
        summary += f"\nTotal Input Tokens: {self.total_input_tokens:,}"
        summary += f"\nTotal Output Tokens: {self.total_output_tokens:,}"
        summary += f"\nTotal Tokens: {self.total_tokens:,}"
        summary += f"\nModel: {model_name}"
        summary += f"\nEstimated Total Cost: ${total_cost:.4f}"
        summary += "\n" + "=" * 70
        
        return summary