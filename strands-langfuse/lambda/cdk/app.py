#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stack import StrandsLangfuseLambdaStack

app = cdk.App()

StrandsLangfuseLambdaStack(
    app,
    "StrandsLangfuseLambdaStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    )
)

app.synth()