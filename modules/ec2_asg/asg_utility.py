# modules/ec2_asg/asg_utility.py
from constructs import Construct
from imports.aws.launch_template import LaunchTemplate
from imports.aws.autoscaling_group import AutoscalingGroup

class AsgModule(Construct):
    """
    A reusable module for creating an EC2 Auto Scaling Group (ASG)
    with a Launch Template.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 vpc_zone_identifier: list[str],
                 ami: str,
                 instance_type: str,
                 min_size: int,
                 max_size: int,
                 desired_capacity: int,
                 security_group_ids: list[str],
                 target_group_arns: list[str] = None,
                 user_data: str = None,
                 iam_instance_profile_name: str = None,
                 tags: dict = None):
        """
        Args:
            name (str): A name prefix for the ASG resources.
            vpc_zone_identifier (list[str]): A list of private subnet IDs for the instances.
            ami (str): The AMI ID for the instances.
            instance_type (str): The instance type (e.g., 't3.micro').
            min_size (int): The minimum number of instances.
            max_size (int): The maximum number of instances.
            desired_capacity (int): The desired number of instances.
            security_group_ids (list[str]): The security groups to associate with the instances.
            target_group_arns (list[str], optional): ARNs of ALB/NLB target groups to attach.
            user_data (str, optional): User data script to run on instance launch (base64 encoded).
            iam_instance_profile_name (str, optional): The name of the IAM instance profile.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        launch_template_tags = {"Name": f"{name}-lt", **(tags or {})}

        self.launch_template = LaunchTemplate(self, "LaunchTemplate",
            name=f"{name}-lt",
            image_id=ami,
            instance_type=instance_type,
            vpc_security_group_ids=security_group_ids,
            user_data=user_data,
            iam_instance_profile={"name": iam_instance_profile_name} if iam_instance_profile_name else None,
            tag_specifications=[
                {
                    "resource_type": "instance",
                    "tags": launch_template_tags
                }
            ],
            tags=launch_template_tags
        )

        self.asg = AutoscalingGroup(self, "Asg",
            name=name,
            min_size=min_size,
            max_size=max_size,
            desired_capacity=desired_capacity,
            vpc_zone_identifier=vpc_zone_identifier,
            target_group_arns=target_group_arns,
            launch_template={
                "id": self.launch_template.id,
                "version": "$Latest"
            },
            tags=[{"key": k, "value": v, "propagate_at_launch": True} for k, v in {**{"Name": name}, **(tags or {})}.items()]
        )
