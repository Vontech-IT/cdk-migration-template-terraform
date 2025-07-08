from aws_cdk import (
    aws_macie as macie,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
)
from constructs import Construct
from typing import Optional, List, Dict


class MacieConfig:
    """
    Configuration class for Amazon Macie settings.

    Attributes:
        enable_macie (bool): Enables Amazon Macie.
        classification_type (str): The type of classification ("FULL" or "BASIC").
        s3_buckets (Optional[List[s3.Bucket]]): List of S3 bucket instances to be included for scanning.
        member_accounts (Optional[List[str]]): List of AWS account IDs to include as Macie member accounts.
        find_sensitive_data (bool): Enables sensitive data discovery.
        tags (Optional[Dict[str, str]]): Tags for organizational purposes.
    """

    def __init__(
        self,
        enable_macie: bool = True,
        classification_type: str = "FULL",
        s3_buckets: Optional[List[s3.Bucket]] = None,
        member_accounts: Optional[List[str]] = None,
        find_sensitive_data: bool = True,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.enable_macie = enable_macie
        self.classification_type = classification_type
        self.s3_buckets = s3_buckets or []
        self.member_accounts = member_accounts or []
        self.find_sensitive_data = find_sensitive_data
        self.tags = tags or {}


class MacieData:
    """
    Stores references to created Amazon Macie resources.

    Attributes:
        macie_session (macie.CfnSession): The Amazon Macie session.
    """

    def __init__(self, macie_session: macie.CfnSession):
        self.macie_session = macie_session


class MacieResources:
    """
    Manages the created Amazon Macie resources.

    Attributes:
        _resources (Dict[str, MacieData]): Dictionary mapping session names to MacieData instances.
    """

    def __init__(self):
        self._resources: Dict[str, MacieData] = {}

    def add_resource(self, name: str, macie_data: MacieData):
        """
        Adds an Amazon Macie resource to the resources dictionary.

        Args:
            name (str): Name of the Macie session.
            macie_data (MacieData): The Macie data instance.
        """
        self._resources[name] = macie_data

    def get_macie_session(self, name: str) -> macie.CfnSession:
        """
        Retrieves an Amazon Macie session by name.

        Args:
            name (str): Name of the Macie session.

        Returns:
            macie.CfnSession: The Amazon Macie session instance.
        """
        return self._resources[name].macie_session


class MacieUtility:
    """
    Utility class for configuring and managing Amazon Macie sessions based on configurations.

    Attributes:
        resources (MacieResources): Manages the created Amazon Macie sessions.
    """

    def __init__(self, scope: Construct, macie_config: MacieConfig):
        """
        Initializes MacieUtility and creates an Amazon Macie session based on provided configuration.

        Args:
            scope (Construct): The CDK construct scope for creating resources.
            macie_config (MacieConfig): The configuration for Amazon Macie.
        """
        self.resources = MacieResources()

        # Enable Macie session
        if macie_config.enable_macie:
            macie_session = macie.CfnSession(
                scope,
                "MacieSession",
                status="ENABLED" if macie_config.enable_macie else "PAUSED",
                finding_publishing_frequency="FIFTEEN_MINUTES",
                classification_type=macie_config.classification_type,
            )
            self.resources.add_resource("MacieSession", MacieData(macie_session))

            # Add S3 buckets for scanning if specified
            for bucket in macie_config.s3_buckets:
                self.add_s3_bucket_to_macie(scope, bucket)

            # Add member accounts if specified
            for account_id in macie_config.member_accounts:
                self.add_macie_member_account(scope, account_id)

            # Output Macie session status
            CfnOutput(
                scope,
                "MacieSessionStatus",
                value=macie_session.status,
                description="Amazon Macie session status",
            )

    def add_s3_bucket_to_macie(self, scope: Construct, bucket: s3.Bucket):
        """
        Adds an S3 bucket to Macie for data classification and sensitive data discovery.

        Args:
            scope (Construct): The CDK construct scope.
            bucket (s3.Bucket): The S3 bucket instance to include in Macie scans.
        """
        macie.CfnFindingsFilter(
            scope,
            f"{bucket.bucket_name}-FindingsFilter",
            name=f"Macie-{bucket.bucket_name}",
            action="ARCHIVE",  # Or "NOOP" if you want findings to be unarchived
            description="Filter for findings in the bucket",
            finding_criteria={
                "criterion": {
                    "resourcesAffected.s3Bucket.arn": {
                        "eq": [bucket.bucket_arn]
                    }
                }
            },
        )

    def add_macie_member_account(self, scope: Construct, account_id: str):
        """
        Adds a member account to Amazon Macie.

        Args:
            scope (Construct): The CDK construct scope.
            account_id (str): The AWS account ID of the member account to add to Macie.
        """
        macie.CfnMember(
            scope,
            f"MacieMember-{account_id}",
            account_id=account_id,
            email=f"{account_id}@example.com",
            status="ENABLED",
            invitation_disable_email_notification=True,
        )
