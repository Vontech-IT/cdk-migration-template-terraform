from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    Tags,
    Duration
)
from aws_cdk.aws_elasticloadbalancingv2_targets import InstanceTarget
from constructs import Construct
from typing import Optional, List


class TargetGroupConfig:
    """
    Configuration for a target group in a Network Load Balancer.
    
    Attributes:
        target_group_name (str): Name of the target group.
        port (int): Port for the target group.
        protocol (str): Protocol for the target group (e.g., "TCP").
        vpc (ec2.Vpc): The VPC where the target group is deployed.
        health_check_path (str): Path for health checks.
        health_check_enabled (bool): Whether health checks are enabled. Defaults to False.
        health_check_interval (int): Interval between health checks in seconds.
        health_check_timeout (int): Timeout for health checks in seconds.
        healthy_threshold_count (int): Number of successful health checks before considering healthy.
        unhealthy_threshold_count (int): Number of failed health checks before considering unhealthy.
        target_type (str): Type of targets (e.g., "instance", "ip").
        asg (Optional[autoscaling.AutoScalingGroup]): Auto Scaling Group to register with the target group.
    """
    TCP = elbv2.Protocol.TCP

    def __init__(
        self,
        target_group_name: str,
        port: int,
        protocol: elbv2.Protocol = elbv2.Protocol.TCP,
        vpc: ec2.Vpc = None,
        target_type: str = "instance",
        asg: Optional[autoscaling.AutoScalingGroup] = None,
        ec2_instance: Optional[ec2.Instance] = None
    ):
        self.target_group_name = target_group_name
        self.port = port
        self.protocol = protocol
        self.vpc = vpc
        self.target_type = target_type
        self.asg = asg
        self.ec2_instance = ec2_instance


class ListenerConfig:
    """
    Configuration for a listener in a Network Load Balancer.
    
    Attributes:
        port (int): Port for the listener.
        protocol (elbv2.Protocol): Protocol for the listener (e.g., "TCP").
        target_group (TargetGroupConfig): Configuration for the target group.
    """

    TCP = elbv2.Protocol.TCP

    def __init__(
        self,
        port: int,
        protocol: elbv2.Protocol = elbv2.Protocol.TCP,
        target_group: TargetGroupConfig = None,
    ):
        self.port = port
        self.protocol = protocol
        self.target_group = target_group


class NLBConfig:
    """
    Configuration class for defining the properties of a Network Load Balancer (NLB).
    
    Attributes:
        nlb_name (str): Name of the NLB.
        vpc (ec2.Vpc): The VPC where the NLB is deployed.
        internet_facing (bool): Whether the NLB is public or internal.
        listener_configs (List[ListenerConfig]): Configuration for the listeners associated with the NLB.
    """

    def __init__(
        self,
        nlb_name: str,
        vpc: Optional[ec2.Vpc] = None,
        internet_facing: bool = True,
        listener_configs: Optional[List[ListenerConfig]] = None,
    ):
        self.nlb_name = nlb_name
        self.vpc = vpc
        self.internet_facing = internet_facing
        self.listener_configs = listener_configs or []


class NLBData:
    """
    Stores references to created NLB and its listeners for easy access.
    
    Attributes:
        nlb (elbv2.NetworkLoadBalancer): The created NLB instance.
        listeners (List[elbv2.NetworkListener]): List of listeners associated with the NLB.
    """

    def __init__(self, nlb: elbv2.NetworkLoadBalancer, listeners: List[elbv2.NetworkListener]):
        self.nlb = nlb
        self.listeners = listeners


class NLBResources:
    """
    Manages the resources for Network Load Balancers.
    
    Attributes:
        _resources (Dict[str, NLBData]): A dictionary mapping NLB names to NLBData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, nlb_data: NLBData):
        """
        Adds an NLB and its data to the resources.
        
        Args:
            name (str): The name of the NLB.
            nlb_data (NLBData): The NLB data containing the NLB and listeners.
        """
        self._resources[name] = nlb_data

    def get_nlb(self, name: str) -> elbv2.NetworkLoadBalancer:
        return self._resources[name].nlb

    def get_listener(self, name: str, index: int = 0) -> elbv2.NetworkListener:
        return self._resources[name].listeners[index]


class NLBBlueprint:
    """
    Blueprint for creating multiple Network Load Balancers based on predefined configurations.

    Attributes:
        nlb_configs (List[NLBConfig]): A list of NLB configurations for defining Network Load Balancers.
    """

    def __init__(self, nlb_configs: List[NLBConfig] = []):
        """
        Initializes an NLBBlueprint instance.

        Args:
            nlb_configs (List[NLBConfig], optional): List of NLB configurations. Defaults to an empty list.
        """
        self.nlb_configs = nlb_configs

    def add_config(self, nlb_config: NLBConfig):
        """
        Adds a new NLB configuration to the blueprint.

        Args:
            nlb_config (NLBConfig): The NLB configuration to add.
        """
        self.nlb_configs.append(nlb_config)
    
    @property
    def all_configs(self) -> List[NLBConfig]:
        return self.nlb_configs


class NLBUtility:
    """
    Utility class for creating and managing Network Load Balancers based on the NLBConfig.
    
    Attributes:
        resources (NLBResources): A dictionary of NLBs created by name.
    """

    def __init__(self, scope: Construct, nlb_configs: NLBBlueprint):
        self.resources = NLBResources()
        for config in nlb_configs.all_configs:
            # Create the NLB
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            nlb = elbv2.NetworkLoadBalancer(
                scope,
                config.nlb_name,
                load_balancer_name=config.nlb_name,
                vpc=vpc,
                internet_facing=config.internet_facing,
            )
            Tags.of(nlb).add("Name", config.nlb_name)

            listeners = []
            # Create listeners
            for listener_config in config.listener_configs:
                listener = nlb.add_listener(
                    f"{listener_config.target_group.target_group_name}Listener",
                    port=listener_config.port,
                    protocol=listener_config.protocol,
                )

                # Create target group and associate it with the listener
                target_group = elbv2.NetworkTargetGroup(
                        scope,
                        f"{listener_config.target_group.target_group_name}TargetGroup",
                        vpc=vpc,
                        port=listener_config.target_group.port,
                        protocol=listener_config.target_group.protocol,
                        target_group_name=listener_config.target_group.target_group_name,
                        target_type=elbv2.TargetType.INSTANCE,
                    ) 

                # Register ASG if provided
                if listener_config.target_group.asg:
                    target_group.add_target(listener_config.target_group.asg)
                
                if listener_config.target_group.ec2_instance:
                    target_group.add_target(InstanceTarget(listener_config.target_group.ec2_instance))

                # Add the target group to the listener's default action
                listener.add_target_groups(
                    f"{listener_config.target_group.target_group_name}ListenerTG",
                    target_group
                )

                listeners.append(listener)

            # Store the NLB and listeners in the resources dictionary
            self.resources.add_resource(config.nlb_name, NLBData(nlb, listeners))
