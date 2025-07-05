# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a cost-optimized AWS deployment solution for Langfuse v3, an open-source observability platform for LLM applications. It's built with AWS CDK (Cloud Development Kit) and provides automated deployment scripts for quick setup with lower operational costs (~$75-100/month vs ~$150-200/month for the original AWS samples version).

## Common Development Commands

### Environment Setup

```bash
# Set Python version (required)
pyenv local 3.12.10

# Install dependencies
pip install -r requirements.txt
```

### Deployment Commands

```bash
# Prepare environment (generates secrets and config)
python prepare-cdk.py

# Deploy all stacks (~15-20 minutes)
python deploy-cdk.py

# Monitor deployment costs
python cost-monitor.py          # Today's costs
python cost-monitor.py --weekly # Past week's costs

# Clean up all resources
cdk destroy --force --all
```

### CDK Development Commands

```bash
# Synthesize CloudFormation templates
cdk synth

# Deploy specific stack
cdk deploy StackName

# List all stacks
cdk list

# Show stack differences
cdk diff

# Deploy with specific context values
cdk deploy --context key=value
```

## High-Level Architecture

### Stack Dependencies

The deployment creates multiple CloudFormation stacks in this order:
1. **ECR repositories** - Container registries for Docker images
2. **VPC** - Network infrastructure with public/private subnets
3. **ALB** - Application Load Balancer for web traffic
4. **Redis** - Cache layer (optional, disabled by default)
5. **RDS PostgreSQL** - Primary database (t4g.micro for cost optimization)
6. **S3 buckets** - Storage for blobs and events
7. **Service discovery** - AWS Cloud Map for internal communication
8. **ECS cluster** - Container orchestration
9. **ClickHouse + EFS** - Analytics database with persistent storage
10. **Langfuse worker** - Background processing service
11. **Langfuse web** - Main web application

### Key Cost Optimizations

- Uses RDS PostgreSQL t4g.micro instead of Aurora Serverless
- Reduced container resources for development workloads
- Single-AZ RDS deployment
- Optional Redis (disabled by default)
- Support for Fargate Spot instances

### CDK Stack Organization

```
cdk_stacks/
├── alb_langfuse_web.py      # Public load balancer configuration
├── aurora_postgresql.py      # RDS database (despite name, uses PostgreSQL)
├── ecr.py                   # Container registry setup
├── ecs_cluster.py           # ECS cluster configuration
├── ecs_fargate_service_*.py # Fargate service definitions
├── ecs_task_*.py            # ECS task definitions
├── efs_clickhouse.py        # Persistent storage for ClickHouse
├── redis.py                 # Cache configuration
├── s3.py                    # Object storage buckets
├── service_discovery.py     # Internal service DNS
└── vpc.py                   # Network infrastructure
```

### Configuration Management

- **cdk.context.json**: Generated from template by prepare-cdk.py
- **.env**: AWS credentials and region (generated automatically)
- **Secrets**: SALT, ENCRYPTION_KEY, NEXTAUTH_SECRET auto-generated

### Service Communication

- External traffic → ALB → Langfuse Web (port 3000)
- Langfuse Web ↔ Redis (if enabled)
- Langfuse Web/Worker → RDS PostgreSQL
- Langfuse Web/Worker → ClickHouse (port 8123)
- All services use AWS Cloud Map for discovery

## Important Notes

- Python 3.12.10 is required (use pyenv to manage versions)
- The deployment takes 15-20 minutes to complete
- Database credentials are stored in AWS Secrets Manager
- Container images are pulled from ghcr.io/langfuse
- All services run in private subnets except ALB
- Security groups are automatically configured for least-privilege access