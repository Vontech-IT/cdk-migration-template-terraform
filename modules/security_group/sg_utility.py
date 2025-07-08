from aws_cdk import aws_ec2 as ec2, Tags
from constructs import Construct
from typing import Optional, List, Generator


class SecurityRule:
    """
    Represents a rule for a security group, supporting CIDR and Security Group peers.

    Attributes:
        from_port (int): Port range for the rule (e.g., 80).
        to_port (int): Port range for the rule (e.g., 80).
        protocol (str): Protocol for the rule (e.g., "tcp").
        description (Optional[str]): Description of the rule.
        cidr (Optional[str]): CIDR block if peer_type is CIDR.
        security_group (Optional[ec2.ISecurityGroup]): Security group you wish to grant access.
    """

    def __init__(
        self,
        from_port: int,
        to_port: int,
        protocol: str = "tcp",
        description: Optional[str] = None,
        cidr: Optional[str] = "0.0.0.0/0",
        security_group: Optional[ec2.ISecurityGroup] = None,
        
    ):
        protocols = {
            "tcp": ec2.Protocol.TCP,
            "udp": ec2.Protocol.UDP,
            "icmp": ec2.Protocol.ICMP,
        }
        self.from_port = from_port
        self.to_port = to_port
        self.protocol = protocols[protocol]
        self.description = description
        self.cidr = cidr
        self.security_group = security_group
    
    def get_peer(self) -> ec2.IPeer:
        if self.security_group:
            return self.security_group
        elif self.cidr:
            return ec2.Peer.ipv4(self.cidr)

class SecurityGroupConfig:
    """
    Configuration for creating a Security Group (SG), including settings for inbound and outbound rules, VPC, and optional tags.

    Attributes:
        sg_name (str): The name of the security group.
        vpc (ec2.Vpc): The VPC to associate with the security group.
        description (str): Description of the security group.
        allow_all_outbound (bool): Whether to allow all outbound traffic. Defaults to True.
        inbound_rules (List[SecurityRule]): List of inbound security rules.
        outbound_rules (List[SecurityRule]): List of outbound security rules.
        tags (Optional[dict]): Optional tags to associate with the security group.
    """

    def __init__(
        self,
        sg_name: str,
        description: Optional[str]=None,
        vpc: Optional[ec2.Vpc]=None,
        allow_all_outbound: bool = True,
        inbound_rules: Optional[List[SecurityRule]] = None,
        outbound_rules: Optional[List[SecurityRule]] = None,
        tags: Optional[dict] = None,
    ):
        self.sg_name = sg_name
        self.vpc = vpc
        self.description = description
        self.allow_all_outbound = allow_all_outbound
        self.inbound_rules = inbound_rules or []
        self.outbound_rules = outbound_rules or []
        self.tags = tags or {}
        if "Name" not in self.tags:
            self.tags["Name"] = self.sg_name

class SecurityGroupBlueprint:
    """
    Blueprint for creating multiple Auto Scaling Groups based on predefined configurations.

    Attributes:
        sg_configs (list[SecurityGroupConfig]): A list of Security Group configurations for defining Security Groups.
    """

    def __init__(self, sg_configs: List[SecurityGroupConfig] = []):
        """
        Initializes an SecurityGroupBlueprint instance.

        Args:
            sg_configs (list[SecurityGroupConfig], optional): List of Security Group configurations. Defaults to an empty list.
        """
        self.sg_configs = sg_configs
    
    def add_config(self, sg_config: SecurityGroupConfig):
        """
        Adds a new Security Group configuration to the blueprint.

        Args:
            sg_config (SecurityGroupConfig): The Security Group configuration to add.
        """
        self.sg_configs.append(sg_config)
    
    @property
    def all_configs(self) -> Generator[SecurityGroupConfig, None, None]:
        """
        Generator that yields each Security Group configuration in the blueprint.

        Yields:
            sgConfig: An Security Group configuration object.
        """
        for config in self.sg_configs:
            yield config

class SecurityGroupData:
    """
    Stores the created Security Group for easy access.

    Attributes:
        security_group (ec2.SecurityGroup): The created security group instance.
    """

    def __init__(self, security_group: ec2.SecurityGroup):
        self.security_group = security_group


class SecurityGroupResources:
    """
    Manages the created security groups.

    Attributes:
        _resources (dict): A dictionary mapping security group names to SecurityGroupData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, sg_data: SecurityGroupData):
        """
        Adds a security group to the resources.

        Args:
            name (str): The name of the security group.
            sg_data (SecurityGroupData): The security group data instance.
        """
        self._resources[name] = sg_data

    def get_security_group(self, name: str) -> SecurityGroupData:
        """
        Retrieves a security group by name.

        Args:
            name (str): The name of the security group.

        Returns:
            ec2.SecurityGroup: The associated security group.
        """
        return self._resources[name]


class SecurityGroupUtility:
    """
    Utility for creating and managing security groups based on blueprint configurations.

    Attributes:
        resources (SecurityGroupResources): Manages the security groups created by name.
    """

    def __init__(self, scope: Construct, sg_blueprint: SecurityGroupBlueprint):
        """
        Initializes the SecurityGroupUtility and creates security groups based on provided configurations.

        Args:
            scope (Construct): The scope in which to define the security groups.
            sg_blueprint (SecurityGroupBlueprint): The blueprint defining the security groups to create.
        """
        self.resources = SecurityGroupResources()
        for config in sg_blueprint.all_configs:
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            description = config.description or f"Security Group created by CDK"
            sg = ec2.SecurityGroup(
                scope,
                config.sg_name,
                security_group_name=config.sg_name,
                vpc=vpc,
                description=config.description,
                allow_all_outbound=config.allow_all_outbound,
            )

            # Add inbound rules
            for rule in config.inbound_rules:
                
                peer = rule.get_peer()
                sg.add_ingress_rule(
                    peer=peer,
                    connection=ec2.Port(protocol=rule.protocol, to_port=rule.to_port, from_port=rule.from_port, string_representation=f"{rule.from_port}-{rule.to_port}"),
                    description=rule.description or ""
                )

            # Add outbound rules
            for rule in config.outbound_rules:
                peer = rule.get_peer()
                sg.add_egress_rule(
                    peer=peer,
                    connection=ec2.Port(protocol=rule.protocol, to_port=rule.to_port, from_port=rule.from_port, string_representation=f"{rule.from_port}-{rule.to_port}"),
                    description=rule.description or ""
                )

            # Apply tags if specified
            for key, value in config.tags.items():
                Tags.of(sg).add(key, value)

            # Store the security group in resources
            self.resources.add_resource(config.sg_name, SecurityGroupData(sg))