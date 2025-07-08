from aws_cdk import (
    aws_amazonmq as mq,
    aws_ec2 as ec2,
    CfnOutput,
    Tags,
    aws_secretsmanager as sm,
)
from constructs import Construct
from typing import Optional, List, Dict

class AmazonMQConfig:
    """
    Configuration class for defining the properties of an Amazon MQ broker.

    Attributes:
        broker_name (str): The name of the Amazon MQ broker.
        engine_type (str): The engine type for Amazon MQ (e.g., "ACTIVEMQ" or "RABBITMQ").
        engine_version (str): The version of the engine.
        deployment_mode (str): The deployment mode for the broker (e.g., SINGLE_INSTANCE - ACTIVE_STANDBY_MULTI_AZ - CLUSTER_MULTI_AZ).
        instance_type (str): The instance type for the broker (e.g., mq.m5.large).
        publicly_accessible (bool): Whether the broker is publicly accessible.
        vpc (ec2.Vpc): The VPC for deploying the broker.
        security_group_ids (List[str]): List of security group IDs to associate with the broker.
        users (List[Dict[str, str]]): List of users, each represented as a dictionary with `username` and `password`.
        encryption_options (Optional[Dict[str, bool]]): Encryption options, such as "use_aws_owned_key".
        tags (Optional[Dict[str, str]]): Tags to associate with the broker.
    """

    def __init__(
        self,
        broker_name: str,
        engine_type: str = "ACTIVEMQ",
        engine_version: str = "5.18",
        instance_type: str = "mq.t3.micro",
        deployment_mode: str = "SINGLE_INSTANCE",
        publicly_accessible: bool = False,
        vpc: ec2.Vpc = None,
        security_group_ids: Optional[List[str]] = None,
        users: Optional[list[str]] = None,
        encryption_options: Optional[Dict[str, bool]] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.broker_name = broker_name
        self.engine_type = engine_type
        self.engine_version = engine_version
        self.deployment_mode = deployment_mode
        self.instance_type = instance_type
        self.publicly_accessible = publicly_accessible
        self.vpc: ec2.Vpc = vpc
        self.security_group_ids = security_group_ids or []
        self.users: List[list[str]] = users or ["admin"] # Password is invalid. Enter a password 12 to 250 characters long.
        self.encryption_options = encryption_options or mq.CfnBroker.EncryptionOptionsProperty(use_aws_owned_key=True)
        self.tags = tags or {}
        if "Name" not in self.tags:
            self.tags["Name"] = self.broker_name

        if engine_type != "ACTIVEMQ":
            self.engine_version = "3.13"
            

class AmazonMQBlueprint:
    """
    Blueprint for creating multiple Amazon MQ brokers based on predefined configurations.

    Attributes:
        mq_configs (List[AmazonMQConfig]): List of Amazon MQ configurations.
    """

    def __init__(self, mq_configs: Optional[List[AmazonMQConfig]] = None):
        self.mq_configs = mq_configs or []

    def add_config(self, mq_config: AmazonMQConfig):
        """
        Adds a new Amazon MQ configuration to the blueprint.

        Args:
            mq_config (AmazonMQConfig): The Amazon MQ configuration to add.
        """
        self.mq_configs.append(mq_config)

    @property
    def all_configs(self) -> List[AmazonMQConfig]:
        """
        Returns all Amazon MQ configurations in the blueprint.

        Returns:
            List[AmazonMQConfig]: List of Amazon MQ configurations.
        """
        return self.mq_configs


class AmazonMQData:
    """
    Stores references to created Amazon MQ brokers for easy access.

    Attributes:
        broker (mq.CfnBroker): The created Amazon MQ broker instance.
    """

    def __init__(self, broker: mq.CfnBroker):
        self.broker = broker


class AmazonMQResources:
    """
    Manages the created Amazon MQ brokers.

    Attributes:
        _resources (Dict[str, AmazonMQData]): Dictionary mapping broker names to AmazonMQData instances.
    """

    def __init__(self):
        self._resources: Dict[str, AmazonMQData] = {}

    def add_resource(self, name: str, mq_data: AmazonMQData):
        """
        Adds an Amazon MQ broker to the resources.

        Args:
            name (str): The name of the Amazon MQ broker.
            mq_data (AmazonMQData): The Amazon MQ broker data instance.
        """
        self._resources[name] = mq_data

    def get_broker(self, name: str) -> mq.CfnBroker:
        """
        Retrieves an Amazon MQ broker by name.

        Args:
            name (str): The name of the Amazon MQ broker.

        Returns:
            mq.CfnBroker: The associated Amazon MQ broker.
        """
        return self._resources[name].broker


class AmazonMQUtility:
    """
    Utility class for creating and managing Amazon MQ brokers based on blueprint configurations.

    Attributes:
        resources (AmazonMQResources): Manages the created Amazon MQ brokers by name.
    """

    def __init__(self, scope: Construct, mq_blueprint: AmazonMQBlueprint):
        """
        Initializes the AmazonMQUtility and creates Amazon MQ brokers based on provided configurations.

        Args:
            scope (Construct): The scope in which to define the Amazon MQ brokers.
            mq_blueprint (AmazonMQBlueprint): The blueprint defining the Amazon MQ brokers to create.
        """
        self.resources = AmazonMQResources()
        
        for config in mq_blueprint.all_configs:
            vpc = config.vpc
            security_group_ids = config.security_group_ids

            if not vpc:
                vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            
            if not security_group_ids:
                security_group_ids.append(vpc.vpc_default_security_group)
            
            if config.deployment_mode == "SINGLE_INSTANCE":
                subnet_ids = [vpc.select_subnets(one_per_az=True).subnet_ids[0] ]
            else:
                subnet_ids = vpc.select_subnets(one_per_az=True).subnet_ids


            # Create the Amazon MQ broker
            broker = mq.CfnBroker(
                scope,
                config.broker_name,
                broker_name=config.broker_name,
                deployment_mode=config.deployment_mode,
                engine_type=config.engine_type,
                engine_version=config.engine_version,
                host_instance_type=config.instance_type,
                publicly_accessible=config.publicly_accessible,
                subnet_ids=subnet_ids,
                logs = mq.CfnBroker.LogListProperty(general=True),
                security_groups=config.security_group_ids,
                users=[
                    mq.CfnBroker.UserProperty(
                        username=username,
                        password=sm.Secret(scope, f"{config.broker_name}{username}MQUserPassword", secret_name=f"{config.broker_name}{username}MQUserPassword", generate_secret_string=sm.SecretStringGenerator()).to_string()
                    ) for username in config.users
                ],
                encryption_options=config.encryption_options
            )

            # Apply tags if specified
            for key, value in config.tags.items():
                Tags.of(broker).add(key, value)

            # Store the broker in resources
            self.resources.add_resource(config.broker_name, AmazonMQData(broker))

            # Output the broker ARN
            CfnOutput(
                scope,
                f"{config.broker_name}ARN",
                value=broker.attr_arn,
                description=f"ARN of the Amazon MQ broker {config.broker_name}",
            )
