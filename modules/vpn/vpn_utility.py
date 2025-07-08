from aws_cdk import (
    aws_ec2 as ec2,
    aws_ssm as ssm,
    CfnOutput,
)
from constructs import Construct
from typing import Optional, List, Dict, Any, Union

class TunnelConfig:
    """
    Configuration for a VPN tunnel.

    Attributes:
        tunnel_inside_cidr (str): The CIDR block for the tunnel inside address.
        pre_shared_key (str): The pre-shared key for the tunnel or an SSM parameter path.
        ike_version (int): The IKE version to use (1 or 2).
        phase1_encryption_algorithms (List[str]): The encryption algorithms for Phase 1.
        phase1_integrity_algorithms (List[str]): The integrity algorithms for Phase 1.
        phase1_dh_group_numbers (List[int]): The DH group numbers for Phase 1.
        phase1_lifetime_seconds (int): The lifetime in seconds for Phase 1.
        phase2_encryption_algorithms (List[str]): The encryption algorithms for Phase 2.
        phase2_integrity_algorithms (List[str]): The integrity algorithms for Phase 2.
        phase2_dh_group_numbers (List[int]): The DH group numbers for Phase 2.
        phase2_lifetime_seconds (int): The lifetime in seconds for Phase 2.
        startup_action (str): The startup action for the tunnel.
        dpd_timeout_seconds (int): The DPD timeout in seconds.
        dpd_action (str): The DPD action.
    """

    # Default CIDR blocks for tunnels
    DEFAULT_TUNNEL_CIDRS = [
        "169.254.10.0/30",
        "169.254.11.0/30",
        "169.254.12.0/30",
        "169.254.13.0/30"
    ]

    def __init__(
        self,
        pre_shared_key: str,
        tunnel_inside_cidr: Optional[str] = None,
        ike_version: Optional[int] = 2,
        phase1_encryption_algorithms: Optional[List[str]] = ["AES256"],
        phase1_integrity_algorithms: Optional[List[str]] = ["SHA2-256"],
        phase1_dh_group_numbers: Optional[List[int]] = [14],
        phase1_lifetime_seconds: Optional[int] = 28800,
        phase2_encryption_algorithms: Optional[List[str]] = ["AES256"],
        phase2_integrity_algorithms: Optional[List[str]] = ["SHA2-256"],
        phase2_dh_group_numbers: Optional[List[int]] = [2],
        phase2_lifetime_seconds: Optional[int] = 3600,
        startup_action: Optional[str] = "add",
        dpd_timeout_seconds: Optional[int] = 30,
        dpd_action: Optional[str] = "restart"
    ):
        # Use the provided CIDR or a default one
        self.tunnel_inside_cidr = tunnel_inside_cidr or self.DEFAULT_TUNNEL_CIDRS[0]
        self.pre_shared_key = pre_shared_key
        self.ike_version = ike_version
        self.phase1_encryption_algorithms = phase1_encryption_algorithms or ["AES256"]
        self.phase1_integrity_algorithms = phase1_integrity_algorithms or ["SHA2-256"]
        self.phase1_dh_group_numbers = phase1_dh_group_numbers or [14]
        self.phase1_lifetime_seconds = phase1_lifetime_seconds or 28800
        self.phase2_encryption_algorithms = phase2_encryption_algorithms or ["AES256"]
        self.phase2_integrity_algorithms = phase2_integrity_algorithms or ["SHA2-256"]
        self.phase2_dh_group_numbers = phase2_dh_group_numbers or [2]
        self.phase2_lifetime_seconds = phase2_lifetime_seconds or 3600
        self.startup_action = startup_action or "add"
        self.dpd_timeout_seconds = dpd_timeout_seconds or 30
        self.dpd_action = dpd_action or "restart"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the tunnel configuration to a dictionary.

        Returns:
            Dict[str, Any]: The tunnel configuration as a dictionary.
        """
        return {
            "tunnel_inside_cidr": self.tunnel_inside_cidr,
            "pre_shared_key": self.pre_shared_key,  # This will be the SSM parameter path
            "ike_version": self.ike_version,
            "phase1_encryption_algorithms": self.phase1_encryption_algorithms,
            "phase1_integrity_algorithms": self.phase1_integrity_algorithms,
            "phase1_dh_group_numbers": self.phase1_dh_group_numbers,
            "phase1_lifetime_seconds": self.phase1_lifetime_seconds,
            "phase2_encryption_algorithms": self.phase2_encryption_algorithms,
            "phase2_integrity_algorithms": self.phase2_integrity_algorithms,
            "phase2_dh_group_numbers": self.phase2_dh_group_numbers,
            "phase2_lifetime_seconds": self.phase2_lifetime_seconds,
            "startup_action": self.startup_action,
            "dpd_timeout_seconds": self.dpd_timeout_seconds,
            "dpd_action": self.dpd_action
        }


class VPNConfig:
    """
    Configuration for a Site-to-Site VPN connection.

    Attributes:
        vpn_name (str): The name of the VPN connection.
        vpc (ec2.Vpc): The VPC to attach the VPN gateway to.
        peer_ip (str): The public IP address of the customer gateway.
        local_subnet (ec2.Subnet): The subnet to use for the VPN connection.
        amazon_side_asn (int): The ASN for the Amazon side of the VPN connection.
        customer_side_asn (int): The ASN for the customer side of the VPN connection.
        connection_type (str): The type of VPN connection.
        static_routes_only (bool): Whether to use static routes only.
        tunnel_configs (List[TunnelConfig]): The tunnel configurations for the VPN connection.
    """

    def __init__(
        self,
        vpn_name: str,
        vpc: ec2.Vpc,
        peer_ip: str,
        aws_subnet: ec2.Subnet,
        on_premise_cidr: str,
        amazon_side_asn: int = 64512,
        customer_side_asn: int = 65000,
        connection_type: str = "ipsec.1",
        static_routes_only: bool = True,
        tunnel_configs: Optional[List[TunnelConfig]] = None
    ):
        self.vpn_name = vpn_name
        self.vpc = vpc
        self.peer_ip = peer_ip
        self.aws_subnet = aws_subnet
        self.on_premise_cidr = on_premise_cidr
        self.amazon_side_asn = amazon_side_asn
        self.customer_side_asn = customer_side_asn
        self.connection_type = connection_type
        self.static_routes_only = static_routes_only
        self.tunnel_configs = tunnel_configs or []


class VPNBlueprint:
    """
    Blueprint for creating multiple VPN connections based on predefined configurations.

    Attributes:
        vpn_configs (List[VPNConfig]): List of VPN configurations.
    """

    def __init__(self, vpn_configs: List[VPNConfig] = []):
        self.vpn_configs = vpn_configs

    def add_config(self, vpn_config: VPNConfig):
        """
        Adds a VPN configuration to the blueprint.

        Args:
            vpn_config (VPNConfig): The VPN configuration to add.
        """
        self.vpn_configs.append(vpn_config)

    @property
    def all_configs(self):
        """
        Yields all VPN configurations in the blueprint.

        Yields:
            VPNConfig: Each VPN configuration.
        """
        for config in self.vpn_configs:
            yield config


class VPNUtility:
    """
    Utility class for creating and managing a Site-to-Site VPN connection.

    Attributes:
        resources (VPNResources): Manages the created VPN resources.
    """

    def __init__(self, scope: Construct, vpn_blueprint: VPNBlueprint):
        """
        Initializes the VPNUtility and creates the VPN resources based on the provided blueprint.

        Args:
            scope (Construct): The scope in which to define the VPN resources.
            vpn_blueprint (VPNBlueprint): The blueprint containing VPN configurations.
        """
        self.resources = VPNResources()
        self._used_cidrs = set()  # Track used CIDR blocks
        self.scope = scope  # Store the scope for later use

        for config in vpn_blueprint.all_configs:
            # Create the VPN Gateway
            vpn_gateway = ec2.CfnVPNGateway(
                scope,
                f"{config.vpn_name}VPNGateway",
                type=config.connection_type,
                amazon_side_asn=config.amazon_side_asn,
                tags=[{"Key": "Name", "Value": f"{config.vpn_name}-VPNGateway"}]
            )

            # Attach the VPN Gateway to the VPC
            vpn_attachment = ec2.CfnVPCGatewayAttachment(
                scope,
                f"{config.vpn_name}VPNGatewayAttachment",
                vpc_id=config.vpc.vpc_id,
                vpn_gateway_id=vpn_gateway.ref
            )
            vpn_attachment.add_dependency(vpn_gateway)

            # Create the Customer Gateway
            customer_gateway = ec2.CfnCustomerGateway(
                scope,
                f"{config.vpn_name}CustomerGateway",
                bgp_asn=config.customer_side_asn,
                ip_address=config.peer_ip,
                type=config.connection_type,
                tags=[{"Key": "Name", "Value": f"{config.vpn_name}-CustomerGateway"}]
            )

            # Create the VPN Connection
            vpn_connection = ec2.CfnVPNConnection(
                scope,
                f"{config.vpn_name}VPNConnection",
                vpn_gateway_id=vpn_gateway.ref,
                customer_gateway_id=customer_gateway.ref,
                type=config.connection_type,
                static_routes_only=config.static_routes_only,
                local_ipv4_network_cidr=config.on_premise_cidr,
                remote_ipv4_network_cidr=config.aws_subnet.ipv4_cidr_block
            )
            vpn_connection.add_dependency(vpn_gateway)
            vpn_connection.add_dependency(customer_gateway)

            # Add tunnel configurations if provided
            if config.tunnel_configs:
                tunnel_options = []
                for i, tunnel_config in enumerate(config.tunnel_configs):
                    # If the tunnel doesn't have a CIDR, assign one
                    if not tunnel_config.tunnel_inside_cidr:
                        # Find an unused CIDR
                        for cidr in TunnelConfig.DEFAULT_TUNNEL_CIDRS:
                            if cidr not in self._used_cidrs:
                                tunnel_config.tunnel_inside_cidr = cidr
                                self._used_cidrs.add(cidr)
                                break
                    
                    # Get the tunnel configuration as a dictionary
                    tunnel_dict = tunnel_config.to_dict()
                    
                    # Check if the pre-shared key is an SSM parameter path
                    if tunnel_dict["pre_shared_key"].startswith("/"):
                        # Create an SSM parameter reference
                        ssm_param = ssm.StringParameter.value_for_string_parameter(
                            self.scope,
                            tunnel_dict["pre_shared_key"]
                        )
                        # Replace the path with the actual value
                        tunnel_dict["pre_shared_key"] = ssm_param
                    
                    tunnel_options.append(ec2.CfnVPNConnection.VpnTunnelOptionsSpecificationProperty(
                        **tunnel_dict
                    ))
                vpn_connection.vpn_tunnel_options_specifications = tunnel_options

            # Add route to the route table for the VPN Gateway
            route_table = ec2.CfnRoute(
                scope,
                f"{config.vpn_name}Route",
                route_table_id=config.aws_subnet.route_table.route_table_id,
                destination_cidr_block=config.on_premise_cidr,
                gateway_id=vpn_gateway.ref
            ).add_dependency(vpn_attachment)

            # Store the resources
            self.resources.add_resource(config.vpn_name, VPNData(vpn_gateway, customer_gateway, vpn_connection, route_table))

            # Output the VPN connection details
            CfnOutput(scope, f"{config.vpn_name}VPNConnectionId", value=vpn_connection.ref)
            CfnOutput(scope, f"{config.vpn_name}VPNGatewayId", value=vpn_gateway.ref)
            CfnOutput(scope, f"{config.vpn_name}CustomerGatewayId", value=customer_gateway.ref)


class VPNData:
    """
    Stores references to created VPN resources.

    Attributes:
        vpn_gateway (ec2.CfnVPNGateway): The created VPN gateway instance.
        customer_gateway (ec2.CfnCustomerGateway): The created customer gateway instance.
        vpn_connection (ec2.CfnVPNConnection): The created VPN connection instance.
        route_table (ec2.CfnRoute): The created route for the VPN connection.
    """

    def __init__(self, vpn_gateway: ec2.CfnVPNGateway, customer_gateway: ec2.CfnCustomerGateway, vpn_connection: ec2.CfnVPNConnection, route_table: ec2.CfnRoute):
        self.vpn_gateway = vpn_gateway
        self.customer_gateway = customer_gateway
        self.vpn_connection = vpn_connection
        self.route_table = route_table


class VPNResources:
    """
    Manages the created VPN resources.

    Attributes:
        _resources (dict): A dictionary mapping VPN names to VPNData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, vpn_data: VPNData):
        """
        Adds a VPN resource to the resources.

        Args:
            name (str): The name of the VPN resource.
            vpn_data (VPNData): The VPN data instance.
        """
        self._resources[name] = vpn_data

    def get_resource(self, name: str) -> VPNData:
        """
        Retrieves a VPN resource by name.

        Args:
            name (str): The name of the VPN resource.

        Returns:
            VPNData: The associated VPN data.
        """
        return self._resources[name]
