import os
from aws_cdk import aws_autoscaling as autoscaling, aws_ec2 as ec2, CfnOutput, aws_iam as iam, Tags, CfnParameter
from modules.iam_role.iam_utility import IamUtility, IamBlueprint, IamConfig
from constructs import Construct
from typing import Optional, List, Generator, Sequence

class ASGConfig:
    """
    Represents the configuration for an Auto Scaling Group (ASG), including capacity,
    target tracking, EC2 launch template settings, and additional optional parameters.

    Attributes:
        asg_name (str): The name of the Auto Scaling Group.
        min_capacity (int): Minimum capacity for the ASG.
        max_capacity (int): Maximum capacity for the ASG.
        target_utilization (int): Target CPU utilization for scaling.
        vpc (Optional[ec2.Vpc]): The VPC to launch instances into.
        instance_type (str): The instance type for EC2 instances in the ASG.
        ami_id (Optional[str]): The Amazon Machine Image (AMI) ID for EC2 instances.
        key_name (Optional[str]): The EC2 key pair name for SSH access.
        security_group (Optional[ec2.ISecurityGroup]): Security group to attach.
        user_data (Optional[ec2.UserData]): Optional user data script for EC2 instances.
        role (Optional[iam.Role]): IAM role to associate with the EC2 instances in the ASG.
        volume_size (Optional[int]): The root volume size (in GiB) for the EC2 instances. Defaults to 20 GiB.
        subnets (Optional[List[ec2.Subnet]]): Subnets to launch instances into.
    """

    def __init__(
        self,
        asg_name: str,
        vpc: Optional[ec2.Vpc] = None,
        ami_id: Optional[str] = None,
        instance_type: str = "t3.micro",
        min_capacity: Optional[int] = 1,
        max_capacity: Optional[int] = 1,
        target_utilization: int = 70,
        associate_public_ip: bool = False,
        volume_size: int = 20,
        key_name: Optional[str] = None,
        role: Optional[iam.Role] = None,
        security_group: Optional[ec2.ISecurityGroup] = None,
        user_data: Optional[ec2.UserData] = None,
        subnets: Optional[Sequence[ec2.ISubnet]] = None
    ):
        """
        Initializes an ASGConfig instance with the specified configuration for an Auto Scaling Group.

        Args:
            asg_name (str): The name of the ASG.
            min_capacity (int): Minimum capacity for the ASG.
            max_capacity (int): Maximum capacity for the ASG.
            target_utilization (int): Target CPU utilization for scaling.
            vpc (Optional[ec2.Vpc]): The VPC for the ASG.
            instance_type (Optional[str]): The EC2 instance type. Defaults to "t3.micro".
            ami_id (Optional[str]): The AMI ID for the instances.
            volume_size (Optional[int]): The root volume size (in GiB) for the EC2 instances. Defaults to 20.
            key_name (Optional[str], optional): The SSH key name. Defaults to None.
            role (Optional[iam.Role], optional): The IAM role for the EC2 instances. Defaults to None.
            security_group_ids (Optional[List[str]], optional): Security group IDs for the instances. Defaults to None.
            user_data (Optional[ec2.UserData], optional): EC2 user data script. Defaults to None.
        """
        self.asg_name = asg_name
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.target_utilization = target_utilization
        self.vpc = vpc
        self.instance_type = instance_type
        self.ami_id = ami_id
        self.key_name = key_name
        self.associate_public_ip = associate_public_ip
        self.security_group = security_group
        self.role = role
        self.user_data = user_data
        self.volume_size = volume_size
        self.subnets = subnets


class ASGBlueprint:
    """
    Blueprint for creating multiple Auto Scaling Groups based on predefined configurations.

    Attributes:
        asg_configs (list[ASGConfig]): A list of ASG configurations for defining Auto Scaling Groups.
    """

    def __init__(self, asg_configs: List[ASGConfig] = []):
        """
        Initializes an ASGBlueprint instance.

        Args:
            asg_configs (list[ASGConfig], optional): List of ASG configurations. Defaults to an empty list.
        """
        self.asg_configs = asg_configs
    
    def add_config(self, asg_config: ASGConfig):
        """
        Adds a new ASG configuration to the blueprint.

        Args:
            asg_config (ASGConfig): The ASG configuration to add.
        """
        self.asg_configs.append(asg_config)
    
    @property
    def all_configs(self) -> Generator[ASGConfig, None, None]:
        """
        Generator that yields each ASG configuration in the blueprint.

        Yields:
            ASGConfig: An ASG configuration object.
        """
        for config in self.asg_configs:
            yield config

class ASGData:
    """
    Stores references to created ASG and Launch Template for easy access.

    Attributes:
        asg (autoscaling.AutoScalingGroup): The created Auto Scaling Group instance.
        launch_template (ec2.LaunchTemplate): The created Launch Template instance.
    """

    def __init__(self, asg: autoscaling.AutoScalingGroup, launch_template: ec2.LaunchTemplate):
        self.asg = asg
        self.launch_template = launch_template


class ASGResources:
    """
    Stores and manages the created Auto Scaling Groups and Launch Templates.

    Attributes:
        _resources (Dict[str, ASGData]): A dictionary mapping ASG names to ASGData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, asg_data: ASGData):
        """
        Adds an ASG and its Launch Template to the resources.

        Args:
            name (str): The name of the ASG to associate with the resource.
            asg_data (ASGData): The ASG data containing the ASG and Launch Template.
        """
        self._resources[name] = asg_data

    def get_asg(self, name: str) -> ASGData:
        """
        Retrieves the ASG by its name.

        Args:
            name (str): The name of the ASG.

        Returns:
            ASGData: The associated Auto Scaling Group and Launch Template.
        """
        return self._resources[name]

 

class ASGUtility:
    """
    Utility for creating and managing Auto Scaling Groups based on a blueprint configuration.

    Attributes:
        asgs (dict): A dictionary of Auto Scaling Groups created by name.
    """

    def __init__(self, scope: Construct, asg_blueprint: ASGBlueprint):
        """
        Initializes an ASGUtility instance and creates ASGs based on the provided blueprint.

        Args:
            scope (Construct): The scope in which to define the ASGs.
            asg_blueprint (ASGBlueprint): The blueprint defining the ASGs to create.
        """
        self.resources = ASGResources()
        for idx, config in enumerate(asg_blueprint.all_configs):
            asg_name = config.asg_name
            role = config.role

            # Use the provided VPC or default to the default VPC
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            ami_id = config.ami_id or ec2.MachineImage.latest_amazon_linux2().get_image(vpc.stack).image_id

            if not vpc:
                raise ValueError(f"VPC is a required parameter for ASG at index {idx}.")

            if not asg_name:
                raise ValueError(f"asg_name is a required parameter for ASG at index {idx}.")

            if not role:
                iam_blueprint = IamBlueprint([IamConfig(f"{asg_name}InstanceRole", service="ec2", managed_policies=["AmazonSSMManagedInstanceCore", "service-role/AmazonEC2RoleforAWSCodeDeploy"])])
                iam_utility = IamUtility(scope, iam_blueprint)
                role : iam.IRole = iam_utility.resources.get_role(f"{asg_name}InstanceRole").role

            # Attach the IAM role to an instance profile
            instance_profile = iam.InstanceProfile(
                scope,
                f"{asg_name}InstanceProfile",
                role=role,
                instance_profile_name=f"{asg_name}InstanceProfile"
            )

            # Create the Launch Template
            launch_template = ec2.LaunchTemplate(
                scope,
                f"{asg_name}LaunchTemplate",
                launch_template_name=f"{asg_name}LaunchTemplate",
                associate_public_ip_address=config.associate_public_ip,
                instance_type=ec2.InstanceType(config.instance_type),
                machine_image=ec2.MachineImage.generic_linux({ os.getenv("AWS_REGION"): ami_id }),
                key_name=config.key_name,
                user_data=config.user_data,
                block_devices=[
                    ec2.BlockDevice(
                        device_name="/dev/xvda",
                        volume=ec2.BlockDeviceVolume.ebs(volume_size=config.volume_size)
                    )
                ],
                instance_profile=instance_profile,
                security_group=config.security_group,
            )
            launch_template.node.add_dependency(instance_profile)

            # Create the ASG with the launch template
            if config.subnets:
                subnet_selection = ec2.SubnetSelection(subnets=config.subnets)
            else:
                subnet_selection = ec2.SubnetSelection(subnets=vpc.public_subnets) if config.associate_public_ip else ec2.SubnetSelection(subnets=vpc.private_subnets)

            asg = autoscaling.AutoScalingGroup(
                scope,
                asg_name,
                auto_scaling_group_name=asg_name,
                vpc=vpc,
                min_capacity=config.min_capacity,
                max_capacity=max(config.min_capacity, config.max_capacity),
                launch_template=launch_template,
                vpc_subnets=subnet_selection,
            )
            

            Tags.of(asg).add("Name", f"{asg_name}Instance")

            # Enable Target Tracking Scaling Policy
            asg.scale_on_cpu_utilization(
                f"{asg_name}CpuScaling",
                target_utilization_percent=config.target_utilization
            )

            # Store the ASG and Launch Template in the resources dictionary
            self.resources.add_resource(asg_name, ASGData(asg, launch_template))

            # Output the ASG Name
            # CfnOutput(scope, f"{asg_name}ASGName", value=asg.auto_scaling_group_name)
