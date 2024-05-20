import json

from aws_cdk import (Duration, RemovalPolicy, Stack, aws_cloudfront,
                     aws_cloudfront_origins, aws_cognito, aws_s3, aws_ssm)
from constructs import Construct


class CdkCognitoExampleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.s3_bucket = self.create_s3_bucket()
        self.cloudfront_distribution = self.create_cloudfront_distribution()

    def create_s3_bucket(self):
        s3_bucket = aws_s3.Bucket(
            self,
            "Bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            access_control=aws_s3.BucketAccessControl.PRIVATE,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        return s3_bucket

    def create_cloudfront_distribution(self):
        cloudfront_distribution = aws_cloudfront.Distribution(
            self,
            "CloudFrontDistribution",
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3Origin(self.s3_bucket),
                compress=True,
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
        )

        return cloudfront_distribution

    def create_ssm_string_param(self):
        ssm_name = '/output/s3-cloudfront-stack'

        ssm_string_param = aws_ssm.StringParameter(
            self,
            'SsmStringParam',
            parameter_name=ssm_name,
            string_value=json.dumps(
                {
                    's3_bucket_name': self.s3_bucket.bucket_name,
                    'cloudfront_distribution_id': self.cloudfront_distribution.distribution_id,
                }
            ),
            tier=aws_ssm.ParameterTier.STANDARD,
        )

        ssm_string_param.apply_removal_policy(RemovalPolicy.DESTROY)

        return ssm_string_param

    def create_cognito_user_pool(self):
        ui_domain = self.cloudfront_distribution.domain_name
        user_pool = aws_cognito.UserPool(
            self,
            'UserPool',
            auto_verify=aws_cognito.AutoVerifiedAttrs(email=True),
            user_invitation=aws_cognito.UserInvitationConfig(
                email_subject='Your temporary password for Example Service',
                email_body=f"""<p>Hello {{username}}, </p>
<p>Here is your Example Service account details:</p>
<ul>
  <li>Username: {{username}}</li>
  <li>Temporary Password: {{####}}</li>
</ul>
<p>Please go to the following URL to reset your password and activate your account:\nhttps://{ui_domain}</p>
""",
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )

        user_pool.add_client(
            'UserPoolClient',
            auth_flows=aws_cognito.AuthFlow(admin_user_password=True, custom=True, user_password=True, user_srp=True),
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    aws_cognito.OAuthScope.OPENID,
                    aws_cognito.OAuthScope.PROFILE,
                    aws_cognito.OAuthScope.EMAIL,
                ],
                callback_urls=[
                    'http://localhost:3000/auth/callback',
                    f'https://{ui_domain}/auth/callback',
                ],
                logout_urls=[
                    'http://localhost:3000/sign-in',
                    f'https://{ui_domain}/sign-in',
                ],
            ),
            access_token_validity=Duration.days(1),
            id_token_validity=Duration.days(1),
            refresh_token_validity=Duration.days(30),
        )

        user_pool.add_domain(
            'UserPoolDomain',
            cognito_domain=aws_cognito.CognitoDomainOptions(
                domain_prefix='cognito-example',
            ),
        )

        return user_pool
