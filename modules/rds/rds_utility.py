import os
from aws_cdk import aws_rds as rds, aws_ec2 as ec2, CfnOutput, Tags, Duration
from constructs import Construct
from typing import Optional, List

class RDSConfig:
    """
    Configuration for an Amazon RDS instance, including settings for database engine, instance size,
    security, storage, and networking.

    Attributes:
        db_name (str): The database name.
        db_username (str): The database username.
        instance_type (str): The instance type for the RDS database.
        engine (rds.DatabaseInstanceEngine): The database engine to use.
        vpc (ec2.Vpc): The VPC for the RDS instance.
        allocated_storage (int): Allocated storage size in GB for the RDS instance.
        multi_az (bool): Specifies if the instance is a Multi-AZ deployment.
        publicly_accessible (bool): Whether the database instance is publicly accessible.
        security_groups (Optional[List[ec2.SecurityGroup]]): List of security groups for the instance.
        subnet_group_name (Optional[str]): The name of the subnet group.
        backup_retention (Optional[int]): Number of days to retain backups.
    """
    
    def __init__(
        self,
        db_name: str,
        vpc: ec2.Vpc,
        db_username: str,
        instance_type: str = "t3.micro",
        engine: rds.DatabaseInstanceEngine = rds.DatabaseInstanceEngine.POSTGRES,
        allocated_storage: int = 20,
        multi_az: bool = False,
        publicly_accessible: bool = False,
        requires_license: bool = False,
        security_groups: Optional[List[ec2.SecurityGroup]] = None,
        subnet_group_name: Optional[str] = None,
        backup_retention: Optional[int] = 7,
        subnets: Optional[List[ec2.Subnet]] = None
    ):
        self.db_name = db_name
        self.vpc = vpc
        self.instance_type = instance_type
        self.engine = engine
        self.requires_license = requires_license
        self.allocated_storage = allocated_storage
        self.multi_az = multi_az
        self.db_username = db_username
        self.publicly_accessible = publicly_accessible
        self.security_groups = security_groups or []
        self.subnet_group_name = subnet_group_name
        self.backup_retention = Duration.days(backup_retention)
        self.subnets = subnets


class RDSBlueprint:
    """
    Blueprint for creating multiple RDS instances based on a predefined configuration.

    Attributes:
        rds_configs (List[RDSConfig]): List of RDS configurations.
    """
    
    def __init__(self, rds_configs: List[RDSConfig] = []):
        self.rds_configs = rds_configs

    def add_config(self, rds_config: RDSConfig):
        self.rds_configs.append(rds_config)
    
    @property
    def all_configs(self):
        for config in self.rds_configs:
            yield config


class RDSData:
    """
    Stores references to created RDS instance and associated subnet group for easy access.

    Attributes:
        db_instance (rds.DatabaseInstance): The created RDS database instance.
        subnet_group (rds.SubnetGroup): The created subnet group for the RDS instance.
    """
    
    def __init__(self, db_instance: rds.DatabaseInstance, subnet_group: rds.SubnetGroup):
        self.db_instance = db_instance
        self.subnet_group = subnet_group


class RDSResources:
    """
    Stores and manages the created RDS instances.

    Attributes:
        _resources (dict): Dictionary mapping instance names to RDSData instances.
    """
    
    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, rds_data: RDSData):
        self._resources[name] = rds_data

    def get_db_instance(self, name: str) -> rds.DatabaseInstance:
        return self._resources[name].db_instance


class RDSUtility:
    """
    Utility class for creating and managing RDS instances based on a blueprint configuration.

    Attributes:
        resources (RDSResources): Stores the created RDS instances and their configurations.
    """
    
    def __init__(self, scope: Construct, rds_blueprint: RDSBlueprint):
        self.resources = RDSResources()
        
        for idx, config in enumerate(rds_blueprint.all_configs):
            instance_name = config.db_name.replace("-", "").replace("_", "")
            if not instance_name:
                raise ValueError(f"db_name is required for RDS instance at index {idx}.")
            
            subnets = ec2.SubnetSelection(subnets=config.subnets or config.vpc.private_subnets)

            if config.publicly_accessible and not config.subnets:
                subnets = ec2.SubnetSelection(subnets=config.vpc.public_subnets)
            # Create the Subnet Group if specified
            subnet_group = rds.SubnetGroup(
                scope,
                f"{instance_name}SubnetGroup",
                vpc=config.vpc,
                vpc_subnets=subnets,
                subnet_group_name=config.subnet_group_name or f"{instance_name}SubnetGroup",
                description=f"Subnet group for {instance_name} RDS instance",
            )
            
            db_secret_name_prefix = config.db_name.removesuffix("db").removesuffix("DB")
            db_credentials = rds.Credentials.from_generated_secret(username=config.db_username, secret_name=f"{db_secret_name_prefix}DBcredentials")
            # Create the Database Instance
            license_model = rds.LicenseModel.LICENSE_INCLUDED if config.requires_license else None
            db_name = None if config.requires_license else config.db_name
            db_instance = rds.DatabaseInstance(
                scope,
                instance_name,
                credentials=db_credentials,
                instance_identifier=f"{instance_name}Instance",
                database_name=db_name,
                instance_type=ec2.InstanceType(config.instance_type),
                engine=config.engine,
                vpc=config.vpc,
                license_model=license_model,
                allocated_storage=config.allocated_storage,
                multi_az=config.multi_az,
                publicly_accessible=config.publicly_accessible,
                security_groups=config.security_groups,
                subnet_group=subnet_group,
                backup_retention=config.backup_retention,
            )
            Tags.of(db_instance).add("Name", f"{instance_name}")

            # Add created resources to the resources manager
            self.resources.add_resource(config.db_name, RDSData(db_instance, subnet_group))

            # Output the RDS Instance Endpoint
            CfnOutput(scope, f"{instance_name}Endpoint", value=db_instance.db_instance_endpoint_address)
