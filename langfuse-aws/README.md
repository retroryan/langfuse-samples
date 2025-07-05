# Langfuse V3 on AWS - Quick Setup & Cost-Optimized

This is a simplified, cost-optimized version of the [AWS Samples Langfuse deployment](https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/tree/main/langfuse-v3). View that project for more details and manual setup guide.

This version was created to provide a quick setup approach with lower costs for developers.

## Cost Optimizations Made

Compared to the main branch, this version includes:
- **RDS PostgreSQL t4g.micro** instead of Aurora Serverless (saves ~$50/month)
- **Reduced container resources** for development workloads
- **Automated deployment scripts** for faster setup
- **Estimated cost**: ~$75-100/month (vs ~$150-200/month)

## Setup

Ensure Python 3.12.10 is set:
```bash
pyenv local 3.12.10
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Deploy

```bash
# 1. Prepare the environment (generates secure secrets and config)
python prepare-cdk.py

# 2. Deploy everything (takes ~15-20 minutes)
python deploy-cdk.py

# 3. Monitor costs
python cost-monitor.py          # Today's costs
python cost-monitor.py --weekly  # Past week's costs
```

## Clean Up

```bash
cdk destroy --force --all
```

## Architecture Overview

The deployment creates a microservices architecture on AWS using ECS Fargate:

![Langfuse V3 on AWS Architecture](langfuse-v3-on-aws-ecs-fargate-arch.svg)

Key components:
- **Application Load Balancer** - Routes traffic to Langfuse web service
- **ECS Fargate Services** - Runs Langfuse web, worker, and ClickHouse containers
- **RDS PostgreSQL** - Primary database (t4g.micro for cost optimization)
- **ClickHouse on EFS** - Analytics database with persistent storage
- **S3 Buckets** - Object storage for events and blobs
- **Redis** - Optional caching layer (disabled by default)