from aws_cdk import CfnOutput, aws_iam as iam
from constructs import Construct
from typing import Generator

class IamPermission:
    """
    Represents a permission with specific IAM actions and resources.

    Attributes:
        actions (list[str]): A list of IAM actions that the permission allows.
        resources (list[str]): A list of AWS resources the actions can be performed on.
    """

    def __init__(self, actions: list[str], resources: list[str] = ["*"]):
        """
        Initializes an IamPermission instance.

        Args:
            actions (list[str]): The IAM actions permitted.
            resources (list[str], optional): The resources on which actions are permitted. Defaults to ["*"].
        """
        self.actions: list[str] = actions
        self.resources: list[str] = resources


class IamConfig:
    """
    Represents the configuration for an IAM Role, including its permissions and managed policies.

    Attributes:
        role_name (str): The name of the IAM role.
        service (str): The AWS service for the IAM role's trust policy.
        managed_policies (list[str]): A list of managed policies to attach to the role.
        permissions (list[IamPermission]): A list of custom permissions to add to the role.
    """

    def __init__(self, role_name: str, service: str, managed_policies: list[str] = [], permissions: list[IamPermission] = []):
        """
        Initializes an IamConfig instance.

        Args:
            role_name (str): The name of the IAM role.
            service (str): The service for which the role will assume permissions.
            managed_policies (list[str], optional): Managed policies to attach to the role. Defaults to an empty list.
            permissions (list[IamPermission], optional): Custom permissions to add to the role. Defaults to an empty list.
        """
        self.role_name: str = role_name
        self.service: str = service
        self.managed_policies: list[str] = managed_policies
        self.permissions: list[IamPermission] = permissions


class IamBlueprint:
    """
    Blueprint for creating multiple IAM roles based on predefined configurations.

    Attributes:
        iam_configs (list[IamConfig]): A list of IAM configurations for defining roles.
    """

    def __init__(self, iam_configs: list[IamConfig] = []):
        """
        Initializes an IamBlueprint instance.

        Args:
            iam_configs (list[IamConfig], optional): List of IAM configurations. Defaults to an empty list.
        """
        self.iam_configs: list[IamConfig] = iam_configs
    
    def add_config(self, iam_config: IamConfig):
        """
        Adds a new IAM configuration to the blueprint.

        Args:
            iam_config (IamConfig): The IAM configuration to add.
        """
        self.iam_configs.append(iam_config)
    
    @property
    def all_configs(self) -> Generator[IamConfig, None, None]:
        """
        Generator that yields each IAM configuration in the blueprint.

        Yields:
            IamConfig: An IAM configuration object.
        """
        for config in self.iam_configs:
            yield config


class IamRoleData:
    """
    Wraps an IAM role for easy access and retrieval.

    Attributes:
        role (iam.Role): The IAM role instance.
    """

    def __init__(self, role: iam.Role):
        """
        Initializes an IamRoleData instance.

        Args:
            role (iam.Role): The IAM role to wrap.
        """
        self.role: iam.Role = role  # Store the IAM role instance for access and retrieval


class IamResources:
    """
    Stores and manages IAM roles created from configurations.

    Attributes:
        _roles_dict (dict): A dictionary storing roles by their name.
    """

    def __init__(self):
        """
        Initializes an IamResources instance.
        """
        self._roles_dict = {}

    def add_role(self, name: str, iam_data: IamRoleData):
        """
        Adds an IAM role to the resources.

        Args:
            name (str): The name to associate with the role.
            iam_data (IamRoleData): The IAM role data to store.
        """
        self._roles_dict[name] = iam_data

    def get_role(self, name: str) -> IamRoleData:
        """
        Retrieves an IAM role by its name.

        Args:
            name (str): The name of the role to retrieve.

        Returns:
            IamRoleData: The IAM role data associated with the name.
        """
        return self._roles_dict.get(name)


class IamUtility:
    """
    Utility for creating and managing IAM roles based on a blueprint configuration.

    Attributes:
        resources (IamResources): A container for storing and managing IAM roles.
    """

    def __init__(self, scope: Construct, role_blueprint: IamBlueprint) -> None:
        """
        Initializes an IamUtility instance and creates IAM roles based on the provided blueprint.

        Args:
            scope (Construct): The scope in which to define the IAM roles.
            role_blueprint (IamBlueprint): The blueprint defining the roles to create.

        Raises:
            ValueError: If a required role_name or service is missing in the blueprint configuration.
        """
        self.resources = IamResources()

        for idx, config in enumerate(role_blueprint.all_configs):
            role_name = config.role_name
            if not role_name:
                raise ValueError(f"role_name is a required parameter for role at index {idx}.")

            service = config.service
            service = f"{service}.amazonaws.com"
            if not service:
                raise ValueError(f"service is a required parameter for role at index {idx}.")

            managed_policies = config.managed_policies
            permissions = config.permissions

            # Create the IAM Role
            iam_role = iam.Role(
                scope, 
                f"{role_name}",
                role_name=role_name,
                assumed_by=iam.ServicePrincipal(service)
            )

            # Attach managed policies
            for policy in managed_policies:
                iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(policy))

            # Attach inline permissions
            if permissions:
                for permission in permissions:
                    policy_statement = iam.PolicyStatement(
                        actions=permission.actions,
                        resources=permission.resources
                    )
                    iam_role.add_to_policy(policy_statement)

            # Store the role in the resources dictionary
            self.resources.add_role(role_name, IamRoleData(iam_role))

            # Output the Role ARN
            # CfnOutput(scope, f"{role_name}IAMRoleArn", value=iam_role.role_arn)
