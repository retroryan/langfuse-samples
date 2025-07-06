# Langfuse AWS Cost Tracking Guide

This guide explains how to track and filter AWS costs specifically for your Langfuse deployment using resource tagging and AWS Cost Explorer filters.

## Overview

The cost tracking system uses AWS resource tags combined with Cost Explorer filters to isolate Langfuse-related costs from other AWS resources in your account.

## Resource Tagging Strategy

All Langfuse resources are automatically tagged when deployed via CDK with the following tags:

- **Project**: "Langfuse" - Primary identifier for all Langfuse resources
- **Environment**: "production" (or custom via CDK context) - Environment identifier
- **ManagedBy**: "CDK" - Indicates resources managed by AWS CDK
- **Service**: "Langfuse-Observability" - Service identifier

These tags are applied globally in `app.py`:

```python
cdk.Tags.of(app).add("Project", "Langfuse")
cdk.Tags.of(app).add("Environment", app.node.try_get_context("environment") or "production")
cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Service", "Langfuse-Observability")
```

## Using Cost Filters

### Quick Start

1. Deploy your Langfuse stack with the updated tagging:
   ```bash
   cdk deploy --all
   ```

2. Enable cost allocation tags in AWS Billing Console:
   - Go to AWS Billing > Cost allocation tags
   - Find and activate: Project, Environment, Service, ManagedBy
   - Wait 24 hours for tags to appear in Cost Explorer

3. Use the cost monitor with filtering:
   ```bash
   # View today's Langfuse costs
   python cost-monitor.py
   
   # View weekly Langfuse costs
   python cost-monitor.py --weekly
   ```

### Understanding cost-filter.json

The `cost-filter.json` file contains the AWS Cost Explorer filter that isolates Langfuse costs. The default filter combines:

1. **Tag Filter**: Resources tagged with Project=Langfuse
2. **Service Filter**: Only AWS services used by Langfuse

This prevents including unrelated resources that might coincidentally have the same tags.

### Customizing Filters

Multiple example filters are provided in `cost-filter-examples.json`:

#### Example 1: Basic Tag Filter
```json
{
  "Tags": {
    "Key": "Project",
    "Values": ["Langfuse"]
  }
}
```

#### Example 2: Environment-Specific Filter
```json
{
  "And": [
    {
      "Tags": {
        "Key": "Project",
        "Values": ["Langfuse"]
      }
    },
    {
      "Tags": {
        "Key": "Environment",
        "Values": ["production"]
      }
    }
  ]
}
```

#### Example 3: Filter by CloudFormation Stack
```json
{
  "Tags": {
    "Key": "aws:cloudformation:stack-name",
    "Values": ["Langfuse*"]
  }
}
```

To use a custom filter, replace the contents of `cost-filter.json` with your desired filter configuration.

## Cost Breakdown by Component

The default filter tracks costs for these Langfuse components:

- **Amazon ECS**: Fargate compute costs for Langfuse web, worker, and ClickHouse
- **Amazon RDS**: PostgreSQL database costs
- **Amazon S3**: Storage for blobs and events
- **Elastic Load Balancing**: Application Load Balancer costs
- **Amazon EFS**: Storage for ClickHouse data
- **CloudWatch**: Logs and metrics
- **Secrets Manager**: Secure credential storage
- **ElastiCache**: Redis cache (if enabled)

## Troubleshooting

### Tags Not Appearing in Cost Explorer

1. Ensure tags are activated in AWS Billing Console
2. Wait 24 hours after activation
3. Verify resources were deployed after tagging was added

### Missing Cost Data

1. Check if `cost-filter.json` exists in the project directory
2. Verify the filter syntax is valid JSON
3. Ensure your AWS credentials have Cost Explorer permissions

### Incomplete Cost Breakdown

Some costs cannot be tagged:
- Data transfer between regions/AZs
- Some AWS support charges
- Certain API request charges

These will not appear in filtered views but are typically minimal.

## Advanced Usage

### Custom Environment Tagging

Deploy with custom environment tag:
```bash
cdk deploy --all --context environment=staging
```

### Multi-Account Tracking

For organizations with multiple AWS accounts, add an Account tag:
```python
cdk.Tags.of(app).add("Account", "production-account")
```

Then filter by account in cost-filter.json:
```json
{
  "And": [
    {
      "Tags": {
        "Key": "Project",
        "Values": ["Langfuse"]
      }
    },
    {
      "Tags": {
        "Key": "Account",
        "Values": ["production-account"]
      }
    }
  ]
}
```

## Best Practices

1. **Consistent Tagging**: Always deploy through CDK to ensure consistent tagging
2. **Regular Reviews**: Monitor costs weekly to catch any anomalies
3. **Tag Activation**: Activate tags in AWS Billing immediately after first deployment
4. **Filter Testing**: Test filters in AWS Cost Explorer UI before using in scripts
5. **Documentation**: Document any custom tags or filters for your team

## Related Files

- `app.py`: Contains global tagging configuration
- `cost-monitor.py`: Script to view filtered costs
- `cost-filter.json`: Active cost filter configuration
- `cost-filter-examples.json`: Example filter configurations