from aws_cdk import (
    aws_dynamodb as dynamodb,
    CfnOutput,
)
from constructs import Construct
from typing import List, Optional

class LSIConfig:
    """
    Configuration for a Local Secondary Index (LSI).

    Attributes:
        index_name (str): The name of the LSI.
        sort_key (str): The sort key for the LSI.
        projection_type (Optional[str]): The projection type for the LSI.
    """

    def __init__(self, index_name: str, sort_key: str, non_key_attributes: Optional[List[str]] = None, projection_type: Optional[str] = dynamodb.ProjectionType.ALL):
        self.index_name = index_name
        self.sort_key = sort_key
        self.non_key_attributes = non_key_attributes
        self.projection_type = projection_type


class GSIConfig:
    """
    Configuration for a Global Secondary Index (GSI).

    Attributes:
        index_name (str): The name of the GSI.
        partition_key (str): The partition key for the GSI.
        sort_key (Optional[str]): The sort key for the GSI.
        read_capacity (Optional[int]): The read capacity units for the GSI.
        write_capacity (Optional[int]): The write capacity units for the GSI.
        projection_type (Optional[str]): The projection type for the GSI.
    """

    def __init__(self, index_name: str, partition_key: str, sort_key: Optional[str] = None,
                 read_capacity: Optional[int] = None, write_capacity: Optional[int] = None,
                 projection_type: Optional[str] = dynamodb.ProjectionType.ALL, non_key_attributes: Optional[List[str]] = None):
        self.index_name = index_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.read_capacity = read_capacity
        self.write_capacity = write_capacity
        self.projection_type = projection_type
        self.non_key_attributes = non_key_attributes


class DynamoDBConfig:
    """
    Configuration for an Amazon DynamoDB table.

    Attributes:
        table_name (str): The name of the DynamoDB table.
        partition_key (str): The partition key for the table.
        sort_key (Optional[str]): The sort key for the table.
        read_capacity (Optional[int]): The read capacity units for the table.
        write_capacity (Optional[int]): The write capacity units for the table.
        billing_mode (Optional[str]): The billing mode for the table (e.g., DynamoDBConfig.PAY_PER_REQUEST).
        local_secondary_indexes (Optional[List[LSIConfig]]): List of local secondary index configurations.
        global_secondary_indexes (Optional[List[GSIConfig]]): List of global secondary index configurations.
    """
    PAY_PER_REQUEST = dynamodb.BillingMode.PAY_PER_REQUEST
    PROVISIONED = dynamodb.BillingMode.PROVISIONED

    def __init__(
        self,
        table_name: str,
        partition_key: str,
        sort_key: Optional[str] = None,
        read_capacity: Optional[int] = None,
        write_capacity: Optional[int] = None,
        billing_mode: Optional[str] = PAY_PER_REQUEST,
        local_secondary_indexes: Optional[List[LSIConfig]] = None,
        global_secondary_indexes: Optional[List[GSIConfig]] = None,
    ):
        self.table_name = table_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.read_capacity = read_capacity
        self.write_capacity = write_capacity
        self.billing_mode = billing_mode
        self.local_secondary_indexes = local_secondary_indexes or []
        self.global_secondary_indexes = global_secondary_indexes or []


class DynamoDBBlueprint:
    """
    Blueprint for creating multiple DynamoDB tables based on predefined configurations.

    Attributes:
        dynamodb_configs (List[DynamoDBConfig]): List of DynamoDB configurations.
    """

    def __init__(self, dynamodb_configs: List[DynamoDBConfig] = []):
        self.dynamodb_configs = dynamodb_configs

    def add_config(self, dynamodb_config: DynamoDBConfig):
        self.dynamodb_configs.append(dynamodb_config)

    @property
    def all_configs(self):
        for config in self.dynamodb_configs:
            yield config


class DynamoDBData:
    """
    Stores references to created DynamoDB tables for easy access.

    Attributes:
        table (dynamodb.Table): The created DynamoDB table instance.
    """

    def __init__(self, table: dynamodb.Table):
        self.table = table


class DynamoDBResources:
    """
    Manages the created DynamoDB tables.

    Attributes:
        _resources (dict): Dictionary mapping table names to DynamoDBData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, dynamodb_data: DynamoDBData):
        self._resources[name] = dynamodb_data

    def get_table(self, name: str) -> dynamodb.Table:
        return self._resources[name].table


class DynamoDBUtility:
    """
    Utility class for creating and managing DynamoDB tables based on configurations.

    Attributes:
        resources (DynamoDBResources): Manages the created DynamoDB tables by name.
    """

    def __init__(self, scope: Construct, dynamodb_blueprint: DynamoDBBlueprint):
        self.resources = DynamoDBResources()

        for config in dynamodb_blueprint.all_configs:
            # Create the DynamoDB table
            table = dynamodb.Table(
                scope,
                config.table_name,
                table_name=config.table_name,
                partition_key=dynamodb.Attribute(name=config.partition_key, type=dynamodb.AttributeType.STRING),
                sort_key=dynamodb.Attribute(name=config.sort_key, type=dynamodb.AttributeType.STRING) if config.sort_key else None,
                read_capacity=config.read_capacity,
                write_capacity=config.write_capacity,
                billing_mode=config.billing_mode,
            )

            # Add Local Secondary Indexes (LSI)
            for lsi in config.local_secondary_indexes:
                table.add_local_secondary_index(
                    index_name=lsi.index_name,
                    non_key_attributes=lsi.non_key_attributes,
                    sort_key=dynamodb.Attribute(name=lsi.sort_key, type=dynamodb.AttributeType.STRING),
                    projection_type=lsi.projection_type
                )

            # Add Global Secondary Indexes (GSI)
            for gsi in config.global_secondary_indexes:
                table.add_global_secondary_index(
                    index_name=gsi.index_name,
                    partition_key=dynamodb.Attribute(name=gsi.partition_key, type=dynamodb.AttributeType.STRING),
                    sort_key=None if not gsi.sort_key else dynamodb.Attribute(name=gsi.sort_key, type=dynamodb.AttributeType.STRING),
                    read_capacity=gsi.read_capacity,
                    write_capacity=gsi.write_capacity,
                    projection_type=gsi.projection_type,
                    non_key_attributes=gsi.non_key_attributes
                )

            # Store the table in the resources dictionary
            self.resources.add_resource(config.table_name, DynamoDBData(table))

            # Output the table ARN
            CfnOutput(scope, f"{config.table_name}TableArn", value=table.table_arn)