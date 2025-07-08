from aws_cdk import CfnOutput, aws_s3 as s3
from constructs import Construct
from typing import Generator, Optional

class S3BucketConfig:
    """
    Represents the configuration for an S3 bucket, including optional permissions and settings.

    Attributes:
        bucket_name (str): The name of the S3 bucket.
        versioned (bool): Whether the bucket should have versioning enabled.
        public_read_access (bool): If the bucket should be publicly readable.
    """

    def __init__(self, bucket_name: str, versioned: bool = False, public_read_access: bool = False):
        """
        Initializes an S3BucketConfig instance.

        Args:
            bucket_name (str): The name of the S3 bucket.
            versioned (bool, optional): Enable versioning. Defaults to False.
            public_read_access (bool, optional): Enable public read access. Defaults to False.
        """
        self.bucket_name = bucket_name
        self.versioned = versioned
        self.public_read_access = public_read_access

class S3Blueprint:
    """
    Blueprint for creating multiple S3 buckets based on predefined configurations.

    Attributes:
        s3bucket_configs (list[S3BucketConfig]): A list of S3 Bucket configurations for defining roles.
    """

    def __init__(self, s3bucket_configs: list[S3BucketConfig] = []):
        """
        Initializes an S3BucketBlueprint instance.

        Args:
            s3bucket_configs (list[S3BucketConfig], optional): List of S3 Bucket configurations. Defaults to an empty list.
        """
        self.s3bucket_configs: list[S3BucketConfig] = s3bucket_configs
    
    def add_config(self, s3bucket_config: S3BucketConfig):
        """
        Adds a new S3 Bucket configuration to the blueprint.

        Args:
            s3bucket_config (S3BucketConfig): The S3 Bucket configuration to add.
        """
        self.s3bucket_configs.append(s3bucket_config)
    
    @property
    def all_configs(self) -> Generator[S3BucketConfig, None, None]:
        """
        Generator that yields each IAM configuration in the blueprint.

        Yields:
            S3BucketConfig: An S3Bucket configuration object.
        """
        for config in self.s3bucket_configs:
            yield config

class S3BucketData:
    """
    Wraps an S3 bucket for easy access and retrieval.

    Attributes:
        bucket (s3.Bucket): The S3 bucket instance.
    """

    def __init__(self, bucket: s3.Bucket):
        """
        Initializes an S3BucketData instance.

        Args:
            bucket (s3.Bucket): The S3 bucket to wrap.
        """
        self.bucket: s3.Bucket = bucket


class S3Resources:
    """
    Stores and manages S3 buckets created from configurations.

    Attributes:
        _buckets_dict (dict): A dictionary storing buckets by their name.
    """

    def __init__(self):
        """
        Initializes an S3Resources instance.
        """
        self._buckets_dict = {}

    def add_bucket(self, name: str, bucket_data: S3BucketData):
        """
        Adds an S3 bucket to the resources.

        Args:
            name (str): The name to associate with the bucket.
            bucket_data (S3BucketData): The S3 bucket data to store.
        """
        self._buckets_dict[name] = bucket_data

    def get_bucket(self, name: str) -> Optional[S3BucketData]:
        """
        Retrieves an S3 bucket by its name.

        Args:
            name (str): The name of the bucket to retrieve.

        Returns:
            Optional[S3BucketData]: The S3 bucket data associated with the name.
        """
        return self._buckets_dict.get(name)


class S3Utility:
    """
    Utility for creating and managing S3 buckets based on configurations.

    Attributes:
        resources (S3Resources): A container for storing and managing S3 buckets.
    """

    def __init__(self, scope: Construct, bucket_configs: list[S3BucketConfig]):
        """
        Initializes an S3Utility instance and creates S3 buckets based on the provided configurations.

        Args:
            scope (Construct): The scope in which to define the S3 buckets.
            bucket_configs (list[S3BucketConfig]): The configurations defining the buckets to create.
        """
        self.resources = S3Resources()

        for idx, config in enumerate(bucket_configs):
            bucket_name = config.bucket_name
            if not bucket_name:
                raise ValueError(f"bucket_name is a required parameter for bucket at index {idx}.")

            # Create the S3 Bucket
            bucket = s3.Bucket(
                scope,
                f"{bucket_name}",
                bucket_name=bucket_name,
                versioned=config.versioned,
                public_read_access=config.public_read_access,
            )

            # Store the bucket in the resources dictionary
            self.resources.add_bucket(bucket_name, S3BucketData(bucket))

            # Output the Bucket ARN
            CfnOutput(scope, f"{bucket_name}S3BucketArn", value=bucket.bucket_arn)
