import os
from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
from typing import Generator

class CloudFrontConfig:
    """
    Configuration for an AWS CloudFront distribution.

    Attributes:
        distribution_name (str): The name of the CloudFront distribution.
        origin_path (str): The path to the origin.
        bucket (s3.Bucket): The S3 bucket that serves as the origin.
    """

    def __init__(self, distribution_name: str, bucket: s3.Bucket):
        self.distribution_name: str = distribution_name
        self.bucket: s3.Bucket = bucket


class CloudFrontBlueprint:
    """
    A blueprint for managing multiple CloudFront configurations.

    Attributes:
        cloudfront_configs (list[CloudFrontConfig]): A list of CloudFrontConfig instances representing the configurations.

    Methods:
        add_config(cloudfront_config: CloudFrontConfig): Adds a new CloudFrontConfig to the blueprint.
        all_configs (Generator[CloudFrontConfig, None, None]): A generator that yields CloudFrontConfig instances.
    """

    def __init__(self, cloudfront_configs: list[CloudFrontConfig] = []):
        self.cloudfront_configs: list[CloudFrontConfig] = cloudfront_configs

    def add_config(self, cloudfront_config: CloudFrontConfig):
        """Adds a new CloudFrontConfig to the blueprint."""
        self.cloudfront_configs.append(cloudfront_config)

    @property
    def all_configs(self) -> Generator[CloudFrontConfig, None, None]:
        """Generator that yields each CloudFrontConfig in the blueprint."""
        for config in self.cloudfront_configs:
            yield config


class CloudFrontData:
    """
    Wrapper class for an AWS CloudFront distribution instance.

    Attributes:
        distribution (cloudfront.Distribution): The AWS CloudFront distribution instance.
    """

    def __init__(self, distribution: cloudfront.Distribution):
        self.distribution: cloudfront.Distribution = distribution


class CloudFrontResources:
    """
    A collection of CloudFront distributions.

    Attributes:
        _cloudfront_dict (dict): A dictionary that maps CloudFront distribution names to CloudFrontData instances.

    Methods:
        add_distribution(name: str, cloudfront_data: CloudFrontData): Adds a CloudFrontData instance to the collection.
        get_distribution(name: str) -> CloudFrontData: Retrieves a CloudFrontData instance by name.
    """

    def __init__(self):
        self._cloudfront_dict = {}

    def add_distribution(self, name: str, cloudfront_data: CloudFrontData):
        """Adds a CloudFrontData instance to the collection."""
        self._cloudfront_dict[name] = cloudfront_data

    def get_distribution(self, name: str) -> CloudFrontData:
        """Retrieves a CloudFrontData instance by name."""
        return self._cloudfront_dict[name]


class CloudFrontUtility:
    """
    Utility class for creating and managing AWS CloudFront distributions based on a CloudFrontBlueprint.

    Attributes:
        resources (CloudFrontResources): An instance of CloudFrontResources that stores created CloudFront distributions.

    Methods:
        __init__(scope: Construct, cloudfront_blueprint: CloudFrontBlueprint): Initializes the utility with a given scope and blueprint.
    """

    def __init__(self, scope: Construct, cloudfront_blueprint: CloudFrontBlueprint) -> None:
        self.resources = CloudFrontResources()
        self.scope = scope


        for config in cloudfront_blueprint.all_configs:
            # Create the CloudFront distribution
            origins = []
            origin_id = None
            if config.bucket:
                oac = cloudfront.CfnOriginAccessControl(
                    self.scope,
                    f"{config.distribution_name}OAC",
                    origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                        name=f"{config.distribution_name}-OAC",
                        origin_access_control_origin_type="s3",
                        signing_behavior="always",
                        signing_protocol="sigv4",
                        description="CloudFront OAC to access S3 securely"
                    )
                )
                origin_id = f"{config.distribution_name}S3Origin"
                origins = [
                        cloudfront.CfnDistribution.OriginProperty(
                            id=origin_id,
                            domain_name=f"{config.bucket.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com",
                            s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                                origin_access_identity=""  # required to be empty when using OAC
                            ),
                            origin_access_control_id=oac.attr_id
                        )
                    ]

            distribution = cloudfront.CfnDistribution(
                self.scope,
                f"{config.distribution_name}Distribution",
                distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                    enabled=True,
                    origins=origins,
                    default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                        target_origin_id=origin_id,
                        viewer_protocol_policy="redirect-to-https",
                        allowed_methods=["GET", "HEAD"],
                        cached_methods=["GET", "HEAD"],
                        compress=True,
                        forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                            query_string=False,
                            cookies=cloudfront.CfnDistribution.CookiesProperty(forward="none")
                        )
                    )
                )
            )

            # Update the bucket's access policy to allow CloudFront to access it
            if config.bucket:
                self._update_bucket_policy(config.bucket, distribution)

            # Store CloudFront distribution in CloudFrontResources
            self.resources.add_distribution(config.distribution_name, CloudFrontData(distribution))

            # Output the CloudFront distribution domain name for reference
            CfnOutput(self.scope, f"{config.distribution_name}DomainName", value=distribution.attr_domain_name)

    def _update_bucket_policy(self, bucket: s3.Bucket, distribution: cloudfront.CfnDistribution):
        """Updates the S3 bucket policy to allow access from the CloudFront distribution."""
        bucket.add_to_resource_policy(
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[f"{bucket.bucket_arn}/*"],
                    principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                    conditions={
                        "StringEquals": {
                            "AWS:SourceArn": f"arn:aws:cloudfront::{os.getenv('AWS_ACCOUNT_ID')}:distribution/{distribution.ref}"
                        }
                    }
                )
            )