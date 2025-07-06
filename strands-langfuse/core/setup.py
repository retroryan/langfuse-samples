"""
Core setup utilities for Strands-Langfuse OTEL integration

This module MUST be imported before any Strands imports to properly configure
OpenTelemetry export to Langfuse.
"""
import os
import base64
from dotenv import load_dotenv
from strands.telemetry import StrandsTelemetry


def initialize_langfuse_telemetry():
    """
    Initialize Langfuse OTEL telemetry configuration.
    
    This function MUST be called before importing Strands Agent to ensure
    proper OTEL environment variable configuration.
    
    Returns:
        tuple: (public_key, secret_key, host) for Langfuse configuration
    """
    # Load environment variables
    load_dotenv()
    
    # Get Langfuse credentials
    langfuse_pk = os.environ.get('LANGFUSE_PUBLIC_KEY')
    langfuse_sk = os.environ.get('LANGFUSE_SECRET_KEY')
    langfuse_host = os.environ.get('LANGFUSE_HOST')
    
    if not all([langfuse_pk, langfuse_sk, langfuse_host]):
        raise ValueError("Missing required Langfuse environment variables. "
                       "Please ensure LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, "
                       "and LANGFUSE_HOST are set.")
    
    # Create auth token for OTEL authentication
    auth_token = base64.b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()
    
    # CRITICAL: Set OTEL environment variables BEFORE importing Strands
    # Use signal-specific endpoint for traces (not the generic /api/public/otel)
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = f"{langfuse_host}/api/public/otel/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = f"Authorization=Basic {auth_token}"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = "http/protobuf"
    
    return langfuse_pk, langfuse_sk, langfuse_host


def setup_telemetry(service_name="strands-demo", environment="demo", version="1.0.0"):
    """
    Setup and initialize Strands telemetry with custom service configuration.
    
    Args:
        service_name: Name of the service for OTEL identification
        environment: Deployment environment (e.g., 'demo', 'production')
        version: Service version
        
    Returns:
        StrandsTelemetry: Configured telemetry instance
    """
    # Set service name and resource attributes
    os.environ["OTEL_SERVICE_NAME"] = service_name
    os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"service.version={version},deployment.environment={environment}"
    
    # Initialize telemetry
    print(f"🔧 Initializing StrandsTelemetry for {service_name}...")
    telemetry = StrandsTelemetry()
    telemetry.setup_otlp_exporter()
    print("✅ OTLP exporter configured")
    
    return telemetry


def get_langfuse_client(langfuse_pk=None, langfuse_sk=None, langfuse_host=None):
    """
    Get a configured Langfuse client for scoring and other operations.
    
    Args:
        langfuse_pk: Public key (optional, will use env var if not provided)
        langfuse_sk: Secret key (optional, will use env var if not provided)
        langfuse_host: Host URL (optional, will use env var if not provided)
        
    Returns:
        Langfuse: Configured Langfuse client
    """
    from langfuse import Langfuse
    
    # Use provided values or fall back to environment variables
    pk = langfuse_pk or os.environ.get('LANGFUSE_PUBLIC_KEY')
    sk = langfuse_sk or os.environ.get('LANGFUSE_SECRET_KEY')
    host = langfuse_host or os.environ.get('LANGFUSE_HOST')
    
    return Langfuse(
        public_key=pk,
        secret_key=sk,
        host=host
    )