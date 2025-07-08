#!/usr/bin/env python
import base64
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from imports.aws.provider import AwsProvider

# --- Module Imports ---
# Import the reusable infrastructure modules from the `modules` directory.
from modules.vpc.vpc_utility import VpcModule
from modules.security_group.sg_utility import SecurityGroupModule
from modules.iam_role.iam_utility import IamRoleModule
from modules.alb.alb_utility import AlbModule
from modules.ec2_asg.asg_utility import AsgModule
from modules.rds.rds_utility import RdsModule

class ProductionStack(TerraformStack):
    """
    This stack defines a realistic, multi-tier web application architecture.
    It demonstrates how to compose the reusable modules to create a secure,
    scalable, and maintainable infrastructure.
    """
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # --- Configuration ---
        # Define project-specific tags and configuration variables here.
        project_tags = {
            "ManagedBy": "CDKTF",
            "Project": "WebApp-Production"
        }
        # WARNING: Do not hardcode secrets in production. Use a secret manager.
        db_password = "YourSecurePassword123"
        # Example AMI for Amazon Linux 2 in us-east-1. Find the latest for your region.
        latest_ami = "ami-0c55b159cbfafe1f0"

        # --- Provider ---
        # Configure the AWS Provider with the desired region.
        AwsProvider(self, "AWS", region="us-east-1")

        # --- Networking ---
        # Create a VPC with public and private subnets across two availability zones.
        network = VpcModule(self, "VPC",
            name="Prod-VPC",
            cidr_block="10.10.0.0/16",
            public_subnet_cidrs=["10.10.1.0/24", "10.10.2.0/24"],
            private_subnet_cidrs=["10.10.101.0/24", "10.10.102.0/24"],
            tags=project_tags
        )

        # --- Security Groups ---
        # A security group for the public-facing Application Load Balancer.
        alb_sg = SecurityGroupModule(self, "AlbSg",
            name="alb-sg",
            vpc_id=network.vpc.id,
            ingress_rules=[
                {"from_port": 80, "to_port": 80, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]},
                {"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}
            ],
            egress_rules=[
                {"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}
            ],
            tags=project_tags
        )

        # A security group for the application instances in the private subnets.
        app_sg = SecurityGroupModule(self, "AppSg",
            name="app-sg",
            vpc_id=network.vpc.id,
            ingress_rules=[
                # Allow traffic from the ALB
                {"from_port": 80, "to_port": 80, "protocol": "tcp", "security_groups": [alb_sg.id]}
            ],
            egress_rules=[
                # Allow all outbound traffic
                {"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}
            ],
            tags=project_tags
        )

        # A security group for the RDS database in the private subnets.
        db_sg = SecurityGroupModule(self, "DbSg",
            name="db-sg",
            vpc_id=network.vpc.id,
            ingress_rules=[
                # Allow traffic from the application security group on the MySQL port
                {"from_port": 3306, "to_port": 3306, "protocol": "tcp", "security_groups": [app_sg.id]}
            ],
            egress_rules=[], # No egress needed
            tags=project_tags
        )

        # --- IAM ---
        # An IAM role for the EC2 instances to allow access to other AWS services (e.g., S3).
        app_instance_role = IamRoleModule(self, "AppInstanceRole",
            role_name="AppInstanceRole",
            assume_role_policy_service="ec2.amazonaws.com",
            # Attach the SSM managed policy to allow for remote management via Session Manager
            managed_policy_arns=["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"],
            tags=project_tags
        )

        # --- Load Balancer ---
        # Create an Application Load Balancer in the public subnets.
        alb = AlbModule(self, "ALB",
            name="Prod-WebApp-ALB",
            vpc_id=network.vpc.id,
            subnet_ids=[subnet.id for subnet in network.public_subnets],
            security_group_ids=[alb_sg.id],
            tags=project_tags
        )

        # --- Compute ---
        # A simple user data script to install a web server.
        user_data_script = """#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Hello from CDKTF!</h1>" > /var/www/html/index.html
"""
        user_data_b64 = base64.b64encode(user_data_script.encode()).decode()

        # Create an Auto Scaling Group for the application instances.
        app_asg = AsgModule(self, "ASG",
            name="WebApp-ASG",
            vpc_zone_identifier=[subnet.id for subnet in network.private_subnets],
            ami=latest_ami,
            instance_type="t3.micro",
            min_size=1,
            max_size=3,
            desired_capacity=2,
            security_group_ids=[app_sg.id],
            target_group_arns=[alb.target_group_arn],
            user_data=user_data_b64,
            iam_instance_profile_name=app_instance_role.name,
            tags=project_tags
        )

        # --- Database ---
        # Create an RDS MySQL database in the private subnets.
        database = RdsModule(self, "Database",
            name="prod-webapp-db",
            vpc_id=network.vpc.id,
            subnet_ids=[subnet.id for subnet in network.private_subnets],
            security_group_ids=[db_sg.id],
            allocated_storage=20,
            engine="mysql",
            engine_version="8.0",
            instance_class="db.t3.micro",
            db_name="webappdb",
            username="admin",
            password=db_password,
            tags=project_tags
        )

        # --- Outputs ---
        # Output key values for easy access after deployment.
        TerraformOutput(self, "alb_dns_name",
            value=alb.dns_name,
            description="The public DNS name of the Application Load Balancer"
        )
        TerraformOutput(self, "db_endpoint",
            value=database.address,
            description="The connection endpoint for the RDS database"
        )

# --- Main Application ---
app = App()
ProductionStack(app, "aws-production-stack")
app.synth()
