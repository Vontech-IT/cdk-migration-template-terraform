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
    Configuration for a target group in an Application Load Balancer.
    
    Attributes:
        target_group_name (str): Name of the target group.
        port (int): Port for the target group.
        protocol (str): Protocol for the target group (e.g., "HTTP", "HTTPS").
        vpc (ec2.Vpc): The VPC where the target group is deployed.
        subnets (List[ec2.Subnet]): List of subnets for the target group.
        security_group (ec2.SecurityGroup): Security group for the target group.
        health_check_path (str): Path for health checks.
        health_check_enabled (bool): Whether health checks are enabled. Defaults to False.
        health_check_interval (int): Interval between health checks in seconds.
        health_check_timeout (int): Timeout for health checks in seconds.
        healthy_threshold_count (int): Number of successful health checks before considering healthy.
        unhealthy_threshold_count (int): Number of failed health checks before considering unhealthy.
        target_type (str): Type of targets (e.g., "instance", "ip").
        asg (Optional[autoscaling.AutoScalingGroup]): Auto Scaling Group to register with the target group.
    """
    HTTP = elbv2.ApplicationProtocol.HTTP
    HTTPS = elbv2.ApplicationProtocol.HTTPS

    def __init__(
        self,
        target_group_name: str,
        port: int,
        protocol: elbv2.ApplicationProtocol = elbv2.ApplicationProtocol.HTTP,
        vpc: ec2.Vpc = None,
        subnets: List[ec2.Subnet] = None,
        security_group: ec2.SecurityGroup = None,
        health_check_path: str = "/",
        health_check_enabled: bool = True,
        health_check_interval: int = 30,
        health_check_timeout: int = 5,
        healthy_threshold_count: int = 2,
        unhealthy_threshold_count: int = 2,
        target_type: str = "instance",
        asg: Optional[autoscaling.AutoScalingGroup] = None,
        ec2_instance: Optional[ec2.Instance] = None
    ):
        self.target_group_name = target_group_name
        self.port = port
        self.protocol = protocol
        self.vpc = vpc
        self.subnets = subnets
        self.security_group = security_group
        self.health_check_path = health_check_path
        self.health_check_enabled = health_check_enabled
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.healthy_threshold_count = healthy_threshold_count
        self.unhealthy_threshold_count = unhealthy_threshold_count
        self.target_type = target_type
        self.asg = asg
        self.ec2_instance = ec2_instance



class ListenerConfig:
    """
    Configuration for a listener in an Application Load Balancer.
    
    Attributes:
        port (int): Port for the listener.
        protocol (elbv2.ApplicationProtocol): Protocol for the listener (e.g., "HTTP", "HTTPS").
        target_group (TargetGroupConfig): Configuration for the target group.
        certificate_arn (Optional[str]): ARN of the SSL certificate for HTTPS listeners.
    """

    HTTP = elbv2.ApplicationProtocol.HTTP
    HTTPS = elbv2.ApplicationProtocol.HTTPS

    def __init__(
        self,
        port: int,
        protocol: elbv2.ApplicationProtocol = elbv2.ApplicationProtocol.HTTP,
        target_group: TargetGroupConfig = None,
        certificate_arn: Optional[str] = None,
        path_pattern: Optional[str] = None,  # e.g. "/prod" or "/dev"
        priority: Optional[int] = None
    ):
        self.port = port
        self.protocol = protocol
        self.target_group = target_group
        self.certificate_arn = certificate_arn
        self.path_pattern = path_pattern
        self.priority = priority


class ALBConfig:
    """
    Configuration class for defining the properties of an Application Load Balancer (ALB).
    
    Attributes:
        alb_name (str): Name of the ALB.
        vpc (ec2.Vpc): The VPC where the ALB is deployed.
        internet_facing (bool): Whether the ALB is public or internal.
        security_group (Optional[ec2.SecurityGroup]): Security group for the ALB.
        subnets (Optional[List[ec2.ISubnet]]): List of subnets for the ALB.
        listener_configs (List[ListenerConfig]): Configuration for the listeners associated with the ALB.
    """

    def __init__(
        self,
        alb_name: str,
        vpc: Optional[ec2.Vpc] = None,
        internet_facing: bool = True,
        security_group: Optional[ec2.SecurityGroup] = None,
        subnets: Optional[List[ec2.ISubnet]] = None,
        listener_configs: Optional[List[ListenerConfig]] = None,
    ):
        self.alb_name = alb_name
        self.vpc = vpc
        self.internet_facing = internet_facing
        self.security_group = security_group
        self.subnets = subnets
        self.listener_configs = listener_configs or []


class ALBData:
    """
    Stores references to created ALB and its listeners for easy access.
    
    Attributes:
        alb (elbv2.ApplicationLoadBalancer): The created ALB instance.
        listeners (List[elbv2.ApplicationListener]): List of listeners associated with the ALB.
    """

    def __init__(self, alb: elbv2.ApplicationLoadBalancer, listeners: List[elbv2.ApplicationListener]):
        self.alb = alb
        self.listeners = listeners


class ALBResources:
    """
    Manages the resources for Application Load Balancers.
    
    Attributes:
        _resources (Dict[str, ALBData]): A dictionary mapping ALB names to ALBData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, alb_data: ALBData):
        """
        Adds an ALB and its data to the resources.
        
        Args:
            name (str): The name of the ALB.
            alb_data (ALBData): The ALB data containing the ALB and listeners.
        """
        self._resources[name] = alb_data

    def get_alb(self, name: str) -> elbv2.ApplicationLoadBalancer:
        return self._resources[name].alb

    def get_listener(self, name: str, index: int = 0) -> elbv2.ApplicationListener:
        return self._resources[name].listeners[index]


class ALBBlueprint:
    """
    Blueprint for creating multiple Application Load Balancers based on predefined configurations.

    Attributes:
        alb_configs (List[ALBConfig]): A list of ALB configurations for defining Application Load Balancers.
    """

    def __init__(self, alb_configs: List[ALBConfig] = []):
        """
        Initializes an ALBBlueprint instance.

        Args:
            alb_configs (List[ALBConfig], optional): List of ALB configurations. Defaults to an empty list.
        """
        self.alb_configs = alb_configs

    def add_config(self, alb_config: ALBConfig):
        """
        Adds a new ALB configuration to the blueprint.

        Args:
            alb_config (ALBConfig): The ALB configuration to add.
        """
        self.alb_configs.append(alb_config)
    
    @property
    def all_configs(self) -> List[ALBConfig]:
        return self.alb_configs

class ALBUtility:
    """
    Utility class for creating and managing Application Load Balancers based on the ALBConfig.
    
    Attributes:
        albs (dict): A dictionary of ALBs created by name.
    """

    def __init__(self, scope: Construct, alb_configs: ALBBlueprint):
        self.resources = ALBResources()
        for config in alb_configs.all_configs:
            # Create the ALB
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            subnets = config.subnets or vpc.public_subnets
            alb = elbv2.ApplicationLoadBalancer(
                scope,
                config.alb_name,
                load_balancer_name=config.alb_name,
                vpc=vpc,
                internet_facing=config.internet_facing,
                security_group=config.security_group,
                vpc_subnets=ec2.SubnetSelection(subnets=subnets),
            )
            Tags.of(alb).add("Name", config.alb_name)

            listeners = []
            # Create target groups and listeners
            for listener_config in config.listener_configs:
                listener = alb.add_listener(
                    f"{listener_config.target_group.target_group_name}Listener",
                    port=listener_config.port,
                    protocol=listener_config.protocol,
                    certificates=[listener_config.certificate_arn] if listener_config.certificate_arn else None,
                )

                # Create a target group and associate it with the listener
                target_group = elbv2.ApplicationTargetGroup(
                    scope,
                    f"{listener_config.target_group.target_group_name}TargetGroup",
                    vpc=vpc,
                    port=listener_config.target_group.port,
                    target_group_name=listener_config.target_group.target_group_name,
                    protocol=listener_config.target_group.protocol,
                    health_check=elbv2.HealthCheck(
                        enabled=listener_config.target_group.health_check_enabled,
                        path=listener_config.target_group.health_check_path,
                        interval=Duration.seconds(listener_config.target_group.health_check_interval),
                        timeout=Duration.seconds(listener_config.target_group.health_check_timeout),
                        healthy_threshold_count=listener_config.target_group.healthy_threshold_count,
                        unhealthy_threshold_count=listener_config.target_group.unhealthy_threshold_count,
                    ),
                )

                # Register ASG if provided
                if listener_config.target_group.asg:
                    target_group.add_target(listener_config.target_group.asg)
                
                if listener_config.target_group.ec2_instance:
                    target_group.add_target(InstanceTarget(listener_config.target_group.ec2_instance))


                # Add the target group to the listener's default action
                if listener_config.path_pattern:
                    if not listener_config.priority:
                        exit("Listener priority is required if path pattern is defined")
                    listener.add_action(
                        f"{listener_config.target_group.target_group_name}Rule",
                        priority=listener_config.priority,  # Make sure this is unique per rule
                        conditions=[
                            elbv2.ListenerCondition.path_patterns([listener_config.path_pattern])
                        ],
                        action=elbv2.ListenerAction.forward([target_group]),
                    )
                else:
                    # Default action if no path pattern is defined
                    listener.add_target_groups(
                        id=f"{listener_config.target_group.target_group_name}ListenerTG",
                        target_groups=[target_group]
                    )

                listeners.append(listener)

            # Store the ALB and listeners in the resources dictionary
            self.resources.add_resource(config.alb_name, ALBData(alb, listeners))

