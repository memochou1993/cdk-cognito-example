import os

import aws_cdk

from deployment.cdk_cognito_example_stack import CdkCognitoExampleStack

app = aws_cdk.App()

env = aws_cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION"),
)

CdkCognitoExampleStack(app, "CdkCognitoExampleStack", env=env)

app.synth()
