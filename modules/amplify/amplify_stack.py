import aws_cdk as cdk
from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk.aws_iam import Role, ServicePrincipal, PolicyStatement, ManagedPolicy
from aws_cdk.aws_amplify import CfnApp, CfnBranch

class AmplifyStack(Stack):

    def __init__(self, scope: Construct, id: str, amplify_configs: list, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Loop through each configuration to create Amplify apps
        for config in amplify_configs:
            app_name = config.get("app_name")
            github_repo = config.get("github_repo")
            oauth_token = config.get("oauth_token")
            access_token = config.get("access_token")
            branch_name = config.get("branch_name", "main")
            build_spec = config.get("build_spec", """
                version: 1
                frontend:
                    phases:
                        preBuild:
                            commands:
                                - npm install
                        build:
                            commands:
                                - npm run build
                    artifacts:
                        baseDirectory: build
                        files:
                            - '**/*'
                    cache:
                        paths:
                            - node_modules/**/*
            """)
            envs = config.get("envs", [])

            # Create IAM role for Amplify
            amplify_service_role = Role(
                self, f"{app_name}AmplifyServiceRole",
                assumed_by=ServicePrincipal('amplify.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess')
                ]
            )

            amplify_service_role.add_to_policy(
                PolicyStatement(
                    actions=[
                        "s3:*", "lambda:*", "cloudfront:*", "dynamodb:*", "cognito-idp:*", 
                        "cloudwatch:*", "logs:*", "iam:PassRole", "codebuild:*", "appsync:*"
                    ],
                    resources=["*"]
                )
            )

            # Create Amplify app
            amplify_app = CfnApp(
                self, f"{app_name}AmplifyApp",
                name=app_name,
                repository=github_repo,
                iam_service_role=amplify_service_role.role_arn,
                build_spec=build_spec,
                environment_variables=[
                    {"name": env["key"], "value": env["value"]} for env in envs
                ] if envs else None
            )
            if oauth_token:
                amplify_app.oauth_token = oauth_token
            elif access_token:
                amplify_app.access_token = access_token
            
            # else:
            #     raise Exception("Either oauth_token or access_token must be provided.")
            

            # Create Amplify branch
            amplify_branch = CfnBranch(
                self, f"{app_name}AmplifyBranch",
                app_id=amplify_app.attr_app_id,
                branch_name=branch_name,
                enable_auto_build=True
            )

            # Output the Amplify App ID and Branch URL
            cdk.CfnOutput(
                self, f"{app_name}AppId",
                description="The ID of the Amplify App",
                value=amplify_app.attr_app_id
            )

            cdk.CfnOutput(
                self, f"{app_name}BranchUrl",
                description="The URL of the Amplify Branch",
                value=f"https://{amplify_branch.attr_branch_name}.{amplify_app.attr_default_domain}"
            )

