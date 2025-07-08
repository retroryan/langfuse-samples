# MCP Server Configuration for Claude Code

When using Claude Code with this repository, you can enhance your development experience by configuring MCP (Model Context Protocol) servers. Create a `.mcp.json` file in your project root with the following configuration:

```json
{
  "mcpServers": {
    "langfuse": {
      "command": "node",
      "args": ["<path-to-langfuse-mcp-server>/build/index.js"],
      "env": {
        "LANGFUSE_PUBLIC_KEY": "<your-public-key>",
        "LANGFUSE_SECRET_KEY": "<your-secret-key>",
        "LANGFUSE_BASEURL": "https://cloud.langfuse.com"
      }
    },
    "langfuse-docs": {
      "endpoint": "https://langfuse.com/api/mcp",
      "transport": "streamableHttp"
    },
    "strands": {
      "command": "uvx",
      "args": ["strands-agents-mcp-server"]
    },
    "aws-documentation": {
      "command": "uvx",
      "args": ["langchain-mcp-server", "aws-documentation"]
    },
    "aws-iam": {
      "command": "uvx",
      "args": ["--quiet", "mcp-server-aws-iam"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-cdk": {
      "command": "uvx",
      "args": ["--quiet", "mcp-server-aws-cdk"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "awslabs.cost-analysis-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.cost-analysis-mcp-server", "--profile", "<YOUR_AWS_PROFILE>"]
    }
  }
}
```

## Configuration Notes

- Replace `<YOUR_AWS_PROFILE>` with your actual AWS profile name for the cost analysis server
- For the Langfuse MCP server:
  - Replace `<path-to-langfuse-mcp-server>` with the absolute path to your installed server
  - Replace `<your-public-key>` and `<your-secret-key>` with your Langfuse API keys
  - Update `LANGFUSE_BASEURL` if using a self-hosted instance

## Installing Langfuse MCP Server

```bash
git clone https://github.com/langfuse/mcp-server-langfuse.git
cd mcp-server-langfuse
npm install
npm run build
```

## Available MCP Servers

These MCP servers provide Claude Code with enhanced capabilities for:
- **langfuse**: Access to Langfuse prompt management for production prompts
- **langfuse-docs**: Search and access Langfuse documentation directly
- **strands**: Direct integration with AWS Strands agents
- **aws-documentation**: Access to AWS documentation within Claude
- **aws-iam**: IAM policy analysis and generation
- **aws-cdk**: CDK-specific assistance and code generation
- **cost-analysis**: AWS cost monitoring and optimization insights