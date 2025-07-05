from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    BundlingOptions,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct
import os

class StrandsLangfuseLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda execution role with Bedrock permissions
        lambda_role = iam.Role(
            self, "StrandsLangfuseRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add Bedrock permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"]  # You can restrict this to specific models if needed
        ))

        # Path to deployment package
        deployment_package = os.path.join(os.path.dirname(__file__), "..", "build", "deployment-package.zip")
        
        # Check if deployment package exists
        if not os.path.exists(deployment_package):
            raise RuntimeError(
                "Deployment package not found. Run 'python build_lambda.py' first to create the package."
            )
        
        # Create Lambda function with pre-built deployment package
        lambda_function = _lambda.Function(
            self, "StrandsLangfuseFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset(deployment_package),
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                # These will need to be configured during deployment
                "LANGFUSE_PUBLIC_KEY": os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                "LANGFUSE_SECRET_KEY": os.getenv("LANGFUSE_SECRET_KEY", ""),
                "LANGFUSE_HOST": os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
                "BEDROCK_REGION": os.getenv("BEDROCK_REGION", "us-east-1"),
                "BEDROCK_MODEL_ID": os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
                "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS": "all"
            }
        )

        # Add Function URL with public access (no auth)
        function_url = lambda_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[_lambda.HttpMethod.ALL],
                allowed_headers=["*"]
            )
        )

        # Output the Function URL
        self.function_url = function_url.url
        
        CfnOutput(
            self, "FunctionUrl",
            value=function_url.url,
            description="URL of the Lambda Function"
        )