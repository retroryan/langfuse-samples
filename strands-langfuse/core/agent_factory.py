"""
Agent factory utilities for creating Strands agents with Langfuse integration

This module provides standardized functions for creating Bedrock models and
Strands agents with proper Langfuse trace attributes.
"""
import os
from typing import Dict, Any, List, Optional
from strands import Agent
from strands.models.bedrock import BedrockModel


def create_bedrock_model(model_id: Optional[str] = None, region: Optional[str] = None) -> BedrockModel:
    """
    Create a configured Bedrock model instance.
    
    Args:
        model_id: Bedrock model ID (defaults to env var BEDROCK_MODEL_ID)
        region: AWS region (defaults to env var BEDROCK_REGION)
        
    Returns:
        BedrockModel: Configured Bedrock model instance
    """
    # Use provided values or fall back to environment variables
    model = BedrockModel(
        model_id=model_id or os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region=region or os.environ.get("BEDROCK_REGION", "us-east-1")
    )
    return model


def create_agent(
    system_prompt: str,
    session_id: str,
    user_id: str = "demo-user",
    tags: Optional[List[str]] = None,
    model: Optional[BedrockModel] = None,
    **extra_attributes: Any
) -> Agent:
    """
    Create a Strands agent with Langfuse trace attributes.
    
    Args:
        system_prompt: System prompt for the agent
        session_id: Unique session ID for grouping related traces
        user_id: User identifier for the traces
        tags: List of tags for filtering in Langfuse
        model: Optional pre-configured Bedrock model (creates new if not provided)
        **extra_attributes: Additional trace attributes to include
        
    Returns:
        Agent: Configured Strands agent with Langfuse integration
    """
    # Create model if not provided
    if model is None:
        model = create_bedrock_model()
    
    # Ensure tags is a list
    if tags is None:
        tags = []
    
    # Build trace attributes for Langfuse
    trace_attributes = {
        "session.id": session_id,
        "user.id": user_id,
        "langfuse.tags": tags,
        **extra_attributes  # Include any additional attributes
    }
    
    # Create and return the agent
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        trace_attributes=trace_attributes
    )
    
    return agent


def create_agent_with_context(
    system_prompt: str,
    session_id: str,
    user_id: str = "demo-user",
    tags: Optional[List[str]] = None,
    model: Optional[BedrockModel] = None,
    memory_size: int = 10,
    **extra_attributes: Any
) -> Agent:
    """
    Create a Strands agent with conversation memory.
    
    This is a convenience function for creating agents that need to maintain
    conversation context across multiple turns.
    
    Args:
        system_prompt: System prompt for the agent
        session_id: Unique session ID for grouping related traces
        user_id: User identifier for the traces
        tags: List of tags for filtering in Langfuse
        model: Optional pre-configured Bedrock model
        memory_size: Number of conversation turns to remember
        **extra_attributes: Additional trace attributes
        
    Returns:
        Agent: Configured agent with conversation memory
    """
    # For now, just use the standard create_agent
    # In the future, this could be extended to include memory configuration
    # when Strands supports it
    return create_agent(
        system_prompt=system_prompt,
        session_id=session_id,
        user_id=user_id,
        tags=tags,
        model=model,
        **extra_attributes
    )