import os
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_iam as iam

from modules.builder import StackBuilder
from modules.vpc.vpc_utility import VPCConfig, VPCBlueprint
from modules.security_group.sg_utility import SecurityGroupConfig, SecurityGroupBlueprint, SecurityRule
from modules.iam_role.iam_utility import IamConfig, IamBlueprint, IamPermission
from modules.rds.rds_utility import RDSConfig, RDSBlueprint
from modules.ec2_asg.asg_utility import ASGConfig, ASGBlueprint
from modules.alb.alb_utility import ALBConfig, ALBBlueprint, ListenerConfig, TargetGroupConfig
from modules.s3.s3_utility import S3BucketConfig, S3Blueprint
from modules.cloudfront.cloudfront_utility import CloudFrontConfig, CloudFrontBlueprint
from modules.amplify.amplify_stack import AmplifyStack

# Environment
env = cdk.Environment(account=os.getenv("AWS_ACCOUNT_ID"), region=os.getenv("AWS_REGION"))
app = cdk.App()

# Main Backend Stack
builder = StackBuilder(app, "LifeBloodStack", env=env)

# 1. VPC
vpc_blueprint = VPCBlueprint([
    VPCConfig(
        vpc_name="LifeBloodVPC",
        cidr="10.0.0.0/16",
        max_azs=2,
        nat_gateways=1,
        subnet_configuration=[
            ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
            ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24),
        ]
    )
])
vpc_resources = builder.add_vpc(vpc_blueprint)
vpc = vpc_resources.get_vpc("LifeBloodVPC").vpc

# 2. Security Groups
alb_sg_config = SecurityGroupConfig(
    sg_name="alb-sg",
    vpc=vpc,
    description="Security group for the Application Load Balancer",
    inbound_rules=[
        SecurityRule(from_port=80, to_port=80, protocol="tcp", cidr="0.0.0.0/0", description="Allow HTTP from anywhere"),
        SecurityRule(from_port=443, to_port=443, protocol="tcp", cidr="0.0.0.0/0", description="Allow HTTPS from anywhere")
    ]
)

ec2_sg_config = SecurityGroupConfig(
    sg_name="ec2-sg",
    vpc=vpc,
    description="Security group for the EC2 instances in the ASG"
)

rds_sg_config = SecurityGroupConfig(
    sg_name="rds-sg",
    vpc=vpc,
    description="Security group for the RDS instance"
)

sg_blueprint = SecurityGroupBlueprint(sg_configs=[alb_sg_config, ec2_sg_config, rds_sg_config])
sg_resources = builder.add_security_group(sg_blueprint)

alb_sg = sg_resources.get_security_group("alb-sg").security_group
ec2_sg = sg_resources.get_security_group("ec2-sg").security_group
rds_sg = sg_resources.get_security_group("rds-sg").security_group

# Add rules between security groups
ec2_sg.add_ingress_rule(
    peer=alb_sg,
    connection=ec2.Port.tcp(80),
    description="Allow traffic from ALB"
)
rds_sg.add_ingress_rule(
    peer=ec2_sg,
    connection=ec2.Port.tcp(3306),
    description="Allow traffic from EC2 instances"
)

# 3. IAM Role for EC2
ec2_role_config = IamConfig(
    role_name="LifeBloodEC2Role",
    service="ec2",
    managed_policies=["AmazonSSMManagedInstanceCore"],
    permissions=[
        IamPermission(actions=["sns:*"], resources=["*"]),
        IamPermission(actions=["bedrock:*"], resources=["*"])
    ]
)
iam_blueprint = IamBlueprint([ec2_role_config])
iam_resources = builder.add_iam(iam_blueprint)
ec2_role = iam_resources.get_role("LifeBloodEC2Role").role

# 4. RDS (MySQL)
# Note: The diagram shows a read replica, which is not directly supported by the current RDS utility.
# For high availability, multi_az=True is enabled.
rds_blueprint = RDSBlueprint([
    RDSConfig(
        db_name="LifeBloodDB",
        db_username="admin",
        engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_35),
        vpc=vpc,
        instance_type="t3.micro",
        allocated_storage=20,
        multi_az=True,
        security_groups=[rds_sg],
        subnets=vpc.private_subnets
    )
])
rds_resources = builder.add_rds(rds_blueprint)


# 5. Auto Scaling Group
asg_blueprint = ASGBlueprint([
    ASGConfig(
        asg_name="LifeBloodASG",
        vpc=vpc,
        instance_type="t3.micro",
        min_capacity=2,
        max_capacity=4,
        role=ec2_role,
        security_group=ec2_sg,
        subnets=vpc.private_subnets
    )
])
asg_resources = builder.add_asg(asg_blueprint)
asg = asg_resources.get_asg("LifeBloodASG").asg

# 6. Application Load Balancer
target_group_config = TargetGroupConfig(
    target_group_name="LifeBloodTG",
    port=80,
    vpc=vpc,
    asg=asg
)

# Note: This listener is configured for HTTP. For HTTPS, a certificate ARN is required.
listener_config = ListenerConfig(
    port=80,
    target_group=target_group_config
)

alb_blueprint = ALBBlueprint([
    ALBConfig(
        alb_name="LifeBloodALB",
        vpc=vpc,
        internet_facing=True,
        security_group=alb_sg,
        subnets=vpc.public_subnets,
        listener_configs=[listener_config]
    )
])
alb_resources = builder.add_alb(alb_blueprint)
alb = alb_resources.get_alb("LifeBloodALB")

# 7. S3 Bucket for static assets
s3_blueprint = S3Blueprint([
    S3BucketConfig(bucket_name=f"lifeblood-static-assets-{os.getenv('AWS_ACCOUNT_ID')}")
])
s3_resources = builder.add_s3(s3_blueprint)
s3_bucket = s3_resources.get_bucket(f"lifeblood-static-assets-{os.getenv('AWS_ACCOUNT_ID')}").bucket

# 8. CloudFront
cloudfront_blueprint = CloudFrontBlueprint([
    CloudFrontConfig(
        distribution_name="LifeBloodDistribution",
        bucket=s3_bucket
    )
])
cloudfront_resources = builder.add_cloudfront(cloudfront_blueprint)

# 9. Amplify Stack
# Note: The AmplifyStack is a separate stack.
# Please replace placeholder values for github_repo and oauth_token.
# AWS WAF integration is not supported by the current AmplifyStack utility.
amplify_configs = [
    {
        "app_name": "LifeBloodAmplifyApp",
        "github_repo": "https://github.com/your-user/your-repo", # FIXME: Replace with your repository URL
        "oauth_token": "ghp_your_github_token", # FIXME: Replace with your GitHub token
        "branch_name": "main",
        "envs": [
            {"key": "REACT_APP_API_URL", "value": f"http://{alb.load_balancer_dns_name}"}
        ]
    }
]

amplify_stack = AmplifyStack(app, "LifeBloodAmplifyStack", amplify_configs=amplify_configs, env=env)