# Utility Scripts

This directory contains utility scripts for managing and maintaining the langfuse-samples repository.

## Available Scripts

### delete_metrics.py
Utility for cleaning up traces and scores from your Langfuse instance during development and testing.

```bash
# Interactive mode (safest - prompts for confirmation)
python utils/delete_metrics.py

# Delete only traces
python utils/delete_metrics.py --traces

# Delete only scores  
python utils/delete_metrics.py --scores

# Skip confirmation (use with caution!)
python utils/delete_metrics.py --yes
```

**Prerequisites:**
- Langfuse instance running
- Environment variables configured (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST)
- Can be run from any component directory that has a .env file

**Use Cases:**
- Clean up test data between development sessions
- Remove experimental traces before demos
- Reset Langfuse state for fresh testing

**Safety Features:**
- Interactive confirmation by default
- Shows count of items before deletion
- Supports selective deletion (traces only or scores only)