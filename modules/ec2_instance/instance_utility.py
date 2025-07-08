import os
from aws_cdk import aws_ec2 as ec2, CfnOutput, aws_iam as iam
from aws_cdk import RemovalPolicy
from constructs import Construct
from typing import Optional, List, Generator
from modules.iam_role.iam_utility import IamBlueprint, IamConfig, IamUtility

class InstanceConfig:
    """
    Represents the configuration for an EC2 instance.

    Attributes:
        instance_name (str): The name of the EC2 instance.
        instance_type (str): The instance type for the EC2 instance.
        ami_id (Optional[str]): The Amazon Machine Image (AMI) ID for the EC2 instance.
        key_name (Optional[str]): The EC2 key pair name for SSH access.
        security_group (Optional[ec2.ISecurityGroup]): Security group to attach.
        user_data (Optional[ec2.UserData]): Optional user data script for the EC2 instance.
        role (Optional[iam.Role]): IAM role to associate with the EC2 instance.
        volume_size (Optional[int]): The root volume size (in GiB) for the EC2 instance. Defaults to 20 GiB.
        vpc (Optional[ec2.Vpc]): The VPC to launch the instance into.
        use_elastic_ip (bool): Whether to create and associate an Elastic IP. Defaults to False.
    """

    def __init__(
        self,
        instance_name: str,
        vpc: Optional[ec2.Vpc] = None,
        ami_id: Optional[str] = None,
        instance_type: str = "t3.micro",
        key_name: Optional[str] = None,
        role: Optional[iam.Role] = None,
        security_group: Optional[ec2.ISecurityGroup] = None,
        user_data: Optional[ec2.UserData] = None,
        volume_size: int = 20,
        private_ip: Optional[str] = None,
        subnets: Optional[List[ec2.ISubnet]] = None,
        use_elastic_ip: bool = False,
    ):
        self.instance_name = instance_name
        self.vpc = vpc
        self.ami_id = ami_id
        self.instance_type = instance_type
        self.key_name = key_name
        self.role = role
        self.security_group = security_group
        self.user_data = user_data
        self.volume_size = volume_size
        self.subnets = subnets
        self.private_ip = private_ip
        self.use_elastic_ip = use_elastic_ip


class InstanceData:
    def __init__(self, instance: ec2.Instance, elastic_ip: Optional[ec2.CfnEIP] = None):
        self.instance = instance
        self.elastic_ip = elastic_ip

class InstanceBlueprint:
    """
    Blueprint for creating an EC2 instance based on a predefined configuration.

    Attributes:
        instance_config (InstanceConfig): The configuration for the EC2 instance.
    """

    def __init__(self, instance_configs: List[InstanceConfig]):
        self.instance_configs = instance_configs
    
    def add_config(self, instance_config: InstanceConfig):
        """
        Adds a new EC2 configuration to the blueprint.

        Args:
            ec2_config (InstanceConfig): The EC2 Instance configuration to add.
        """
        self.instance_configs.append(instance_config)
    
    @property
    def all_configs(self) -> Generator[InstanceConfig, None, None]:
        """
        Generator that yields each EC2 configuration in the blueprint.

        Yields:
            EC2Config: Each EC2 Instance configuration.
        """
        for ec2_config in self.instance_configs:
            yield ec2_config


class InstanceResources:

    def __init__(self):
        self._resources = {}
    
    def add_instance(self, instance_name: str, instance_data: InstanceData):
        self._resources[instance_name] = instance_data
    
    def get_instance(self, instance_name: str) -> InstanceData:
        return self._resources[instance_name]
    
class InstanceUtility:
    """
    Utility for creating and managing an EC2 instance based on a blueprint configuration.

    Attributes:
        instance (ec2.Instance): The created EC2 instance.
        elastic_ip (Optional[ec2.CfnEIP]): The created Elastic IP, if applicable.
    """

    def __init__(self, scope: Construct, instance_blueprint: InstanceBlueprint):
        self.resources = InstanceResources()

        for config in instance_blueprint.all_configs:

            # Use the provided VPC or default to the default VPC
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, f"{config.instance_name}DefaultVpc", is_default=True)
            ami_id = config.ami_id or ec2.MachineImage.latest_amazon_linux2().get_image(vpc.stack).image_id
            role = config.role
            if not role:
                iam_blueprint = IamBlueprint([IamConfig(f"{config.instance_name}InstanceRole", service="ec2", managed_policies=["AmazonSSMManagedInstanceCore", "service-role/AmazonEC2RoleforAWSCodeDeploy"])])
                iam_utility = IamUtility(scope, iam_blueprint)
                role : iam.IRole = iam_utility.resources.get_role(f"{config.instance_name}InstanceRole").role

            subnets = ec2.SubnetSelection(subnets=vpc.public_subnets)
            if config.subnets:
                subnets = ec2.SubnetSelection(subnets=config.subnets)

            instance = ec2.Instance(
                scope,
                config.instance_name,
                instance_name=config.instance_name,
                instance_type=ec2.InstanceType(config.instance_type),
                machine_image=ec2.MachineImage.generic_linux({os.getenv("AWS_REGION"): ami_id}),
                vpc=vpc,
                vpc_subnets=subnets,
                key_pair=ec2.KeyPair(scope, f"{config.instance_name}KeyPair", key_pair_name=config.key_name),
                security_group=config.security_group,
                private_ip_address=config.private_ip,
                user_data=config.user_data,
                block_devices=[
                    ec2.BlockDevice(
                        device_name="/dev/xvda",
                        volume=ec2.BlockDeviceVolume.ebs(volume_size=config.volume_size)
                    )
                ],
                role=role,
            )

            # Create and associate an Elastic IP if specified
            if config.use_elastic_ip:
                elastic_ip = ec2.CfnEIP(scope, f"{config.instance_name}ElasticIP")
                ec2.CfnEIPAssociation(scope, f"{config.instance_name}EIPAssociation",
                                    instance_id=instance.instance_id,
                                    allocation_id=elastic_ip.attr_allocation_id)

            # Output the EC2 Instance ID
            CfnOutput(scope, f"{config.instance_name}InstanceId", value=instance.instance_id)
            instance_data = InstanceData(instance, elastic_ip if config.use_elastic_ip else None)
            self.resources.add_instance(config.instance_name, instance_data)
