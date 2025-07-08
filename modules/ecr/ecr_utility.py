from aws_cdk import (
    aws_ecr as ecr,
    aws_kms as kms,
    RemovalPolicy,
    CfnOutput,
    Tags,
)

from constructs import Construct
from typing import Optional, List, Dict


class ECRConfig:
    """
    Configuration class for defining the properties of an Amazon ECR repository.

    Attributes:
        repository_name (str): The name of the ECR repository.
        removal_policy (Optional[str]): The removal policy for the repository (e.g., RETAIN, DESTROY).
        image_scan_on_push (bool): Whether to enable image scanning on push. Defaults to False.
        image_tag_mutability (ecr.TagMutability): The tag mutability setting (MUTABLE or IMMUTABLE).
        lifecycle_rules (Optional[List[ecr.LifecycleRule]]): List of lifecycle rules for the repository.
        encryption (Optional[ecr.RepositoryEncryption]): Encryption settings for the repository.
        encryption_key (Optional[kms.IKey]): KMS key for encryption if using KMS encryption.
        tags (Optional[Dict[str, str]]): Tags to associate with the repository.
    """

    def __init__(
        self,
        repository_name: str,
        removal_policy: Optional[str] = RemovalPolicy.RETAIN,
        image_scan_on_push: bool = False,
        image_tag_mutability: ecr.TagMutability = ecr.TagMutability.MUTABLE,
        lifecycle_rules: Optional[List[ecr.LifecycleRule]] = None,
        encryption: Optional[ecr.RepositoryEncryption] = ecr.RepositoryEncryption.AES_256,
        encryption_key: Optional[kms.IKey] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.repository_name = repository_name
        self.removal_policy = removal_policy
        self.image_scan_on_push = image_scan_on_push
        self.image_tag_mutability = image_tag_mutability
        self.lifecycle_rules = lifecycle_rules or []
        self.encryption = encryption
        self.encryption_key = encryption_key
        self.tags = tags or {}
        if "Name" not in self.tags:
            self.tags["Name"] = self.repository_name


class ECRBlueprint:
    """
    Blueprint for creating multiple ECR repositories based on predefined configurations.

    Attributes:
        ecr_configs (List[ECRConfig]): List of ECR configurations.
    """

    def __init__(self, ecr_configs: Optional[List[ECRConfig]] = None):
        self.ecr_configs = ecr_configs or []

    def add_config(self, ecr_config: ECRConfig):
        """
        Adds a new ECR configuration to the blueprint.

        Args:
            ecr_config (ECRConfig): The ECR configuration to add.
        """
        self.ecr_configs.append(ecr_config)

    @property
    def all_configs(self) -> List[ECRConfig]:
        """
        Returns all ECR configurations in the blueprint.

        Returns:
            List[ECRConfig]: List of ECR configurations.
        """
        return self.ecr_configs


class ECRData:
    """
    Stores references to created ECR repositories for easy access.

    Attributes:
        repository (ecr.Repository): The created ECR repository instance.
    """

    def __init__(self, repository: ecr.Repository):
        self.repository = repository


class ECRResources:
    """
    Manages the created ECR repositories.

    Attributes:
        _resources (Dict[str, ECRData]): Dictionary mapping repository names to ECRData instances.
    """

    def __init__(self):
        self._resources: Dict[str, ECRData] = {}

    def add_resource(self, name: str, ecr_data: ECRData):
        """
        Adds an ECR repository to the resources.

        Args:
            name (str): The name of the ECR repository.
            ecr_data (ECRData): The ECR repository data instance.
        """
        self._resources[name] = ecr_data

    def get_repository(self, name: str) -> ecr.Repository:
        """
        Retrieves an ECR repository by name.

        Args:
            name (str): The name of the ECR repository.

        Returns:
            ecr.Repository: The associated ECR repository.
        """
        return self._resources[name].repository


class ECRUtility:
    """
    Utility class for creating and managing ECR repositories based on blueprint configurations.

    Attributes:
        resources (ECRResources): Manages the created ECR repositories by name.
    """

    def __init__(self, scope: Construct, ecr_blueprint: ECRBlueprint):
        """
        Initializes the ECRUtility and creates ECR repositories based on provided configurations.

        Args:
            scope (Construct): The scope in which to define the ECR repositories.
            ecr_blueprint (ECRBlueprint): The blueprint defining the ECR repositories to create.
        """
        self.resources = ECRResources()
        for config in ecr_blueprint.all_configs:
            repository = ecr.Repository(
                scope,
                config.repository_name,
                repository_name=config.repository_name,
                removal_policy=config.removal_policy,
                image_scan_on_push=config.image_scan_on_push,
                image_tag_mutability=config.image_tag_mutability,
                lifecycle_rules=config.lifecycle_rules,
                encryption=config.encryption,
                encryption_key=config.encryption_key,
            )

            # Apply lifecycle rules if any
            for rule in config.lifecycle_rules:
                repository.add_lifecycle_rule(**rule)

            # Apply tags if specified
            for key, value in config.tags.items():
                Tags.of(repository).add(key, value)

            # Store the repository in resources
            self.resources.add_resource(config.repository_name, ECRData(repository))

            # Output the repository URI
            CfnOutput(
                scope,
                f"{config.repository_name}URI",
                value=repository.repository_uri,
                description=f"URI of the ECR repository {config.repository_name}",
            )

