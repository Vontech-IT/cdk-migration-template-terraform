from aws_cdk import aws_ec2 as ec2, CfnOutput
from constructs import Construct
from typing import Optional, Generator, List

class VPCConfig:
    """
    Represents the configuration for a VPC, including CIDR block, subnet configuration, 
    NAT gateway count, and other optional settings.

    Attributes:
        vpc_name (str): The name of the VPC.
        cidr (str): The CIDR block for the VPC.
        max_azs (int): Maximum number of Availability Zones to use.
        nat_gateways (int): Number of NAT gateways.
        subnet_configuration (Optional[List[ec2.SubnetConfiguration]]): Custom subnet configuration.
    """

    def __init__(
        self,
        vpc_name: str,
        cidr: str = "10.0.0.0/16",
        max_azs: int = 2,
        nat_gateways: int = 1,
        subnet_configuration: Optional[List[ec2.SubnetConfiguration]] = None
    ):
        """
        Initializes a VPCConfig instance.

        Args:
            vpc_name (str): The name of the VPC.
            cidr (str, optional): CIDR block for the VPC. Defaults to "10.0.0.0/16".
            max_azs (int, optional): Maximum AZs to use. Defaults to 2.
            nat_gateways (int, optional): Number of NAT gateways. Defaults to 1.
            subnet_configuration (Optional[List[ec2.SubnetConfiguration]], optional): Custom subnets. Defaults to None.
        """
        self.vpc_name = vpc_name
        self.cidr = cidr
        self.max_azs = max_azs
        self.nat_gateways = nat_gateways
        self.subnet_configuration = subnet_configuration if subnet_configuration else [
            ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
            ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24),
        ]


class VPCBlueprint:
    """
    Blueprint for creating multiple VPCs based on predefined configurations.

    Attributes:
        vpc_configs (list[VPCConfig]): A list of VPC configurations for defining VPCs.
    """

    def __init__(self, vpc_configs: List[VPCConfig] = []):
        """
        Initializes a VPCBlueprint instance.

        Args:
            vpc_configs (list[VPCConfig], optional): List of VPC configurations. Defaults to an empty list.
        """
        self.vpc_configs: List[VPCConfig] = vpc_configs
    
    def add_config(self, vpc_config: VPCConfig):
        """
        Adds a new VPC configuration to the blueprint.

        Args:
            vpc_config (VPCConfig): The VPC configuration to add.
        """
        self.vpc_configs.append(vpc_config)
    
    @property
    def all_configs(self) -> Generator[VPCConfig, None, None]:
        """
        Generator that yields each VPC configuration in the blueprint.

        Yields:
            VPCConfig: A VPC configuration object.
        """
        for config in self.vpc_configs:
            yield config


class VPCData:
    """
    Wraps a VPC instance for easy access and retrieval.

    Attributes:
        vpc (ec2.Vpc): The VPC instance.
    """

    def __init__(self, vpc: ec2.Vpc):
        """
        Initializes a VPCData instance.

        Args:
            vpc (ec2.Vpc): The VPC to wrap.
        """
        self.vpc = vpc


class VPCResources:
    """
    Stores and manages VPCs created from configurations.

    Attributes:
        _vpcs_dict (dict): A dictionary storing VPCs by their name.
    """

    def __init__(self):
        """
        Initializes a VPCResources instance.
        """
        self._vpcs_dict = {}

    def add_vpc(self, name: str, vpc_data: VPCData):
        """
        Adds a VPC to the resources.

        Args:
            name (str): The name to associate with the VPC.
            vpc_data (VPCData): The VPC data to store.
        """
        self._vpcs_dict[name] = vpc_data

    def get_vpc(self, name: str) -> Optional[VPCData]:
        """
        Retrieves a VPC by its name.

        Args:
            name (str): The name of the VPC to retrieve.

        Returns:
            Optional[VPCData]: The VPC data associated with the name.
        """
        return self._vpcs_dict.get(name)


class VPCUtility:
    """
    Utility for creating and managing VPCs based on a blueprint configuration.

    Attributes:
        resources (VPCResources): A container for storing and managing VPCs.
    """

    def __init__(self, scope: Construct, vpc_blueprint: VPCBlueprint):
        """
        Initializes a VPCUtility instance and creates VPCs based on the provided blueprint.

        Args:
            scope (Construct): The scope in which to define the VPCs.
            vpc_blueprint (VPCBlueprint): The blueprint defining the VPCs to create.
        """
        self.resources = VPCResources()

        for idx, config in enumerate(vpc_blueprint.all_configs):
            vpc_name = config.vpc_name
            if not vpc_name:
                raise ValueError(f"vpc_name is a required parameter for VPC at index {idx}.")

            # Create the VPC
            vpc = ec2.Vpc(
                scope,
                vpc_name,
                vpc_name=vpc_name,
                ip_addresses=ec2.IpAddresses.cidr(config.cidr),
                max_azs=config.max_azs,
                nat_gateways=config.nat_gateways,
                subnet_configuration=config.subnet_configuration,
            )

            # Store the VPC in the resources dictionary
            self.resources.add_vpc(vpc_name, VPCData(vpc))

            # Output the VPC ID
            # CfnOutput(scope, f"{vpc_name}VPCId", value=vpc.vpc_id)
