from aws_cdk import (
    aws_inspectorv2 as inspector,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_ecr as ecr,
    CfnOutput,
)
from constructs import Construct
from typing import Optional, List, Dict


class InspectorConfig:
    """
    Configuration class for Amazon Inspector.

    Attributes:
        enable_inspector (bool): Enables Amazon Inspector.
        ec2_instances (Optional[List[ec2.Instance]]): List of EC2 instances to scan.
        lambda_functions (Optional[List[_lambda.Function]]): List of Lambda functions to scan.
        ecr_repositories (Optional[List[ecr.Repository]]): List of ECR repositories to scan.
        tags (Optional[Dict[str, str]]): Tags to apply to Inspector resources.
    """

    def __init__(
        self,
        enable_inspector: bool = True,
        ec2_instances: Optional[List[ec2.Instance]] = None,
        lambda_functions: Optional[List[_lambda.Function]] = None,
        ecr_repositories: Optional[List[ecr.Repository]] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.enable_inspector = enable_inspector
        self.ec2_instances = ec2_instances or []
        self.lambda_functions = lambda_functions or []
        self.ecr_repositories = ecr_repositories or []
        self.tags = tags or {}


class InspectorData:
    """
    Stores references to created Amazon Inspector resources.

    Attributes:
        inspector_service (inspector.CfnService): The Amazon Inspector service.
    """

    def __init__(self, inspector_service: inspector.CfnService):
        self.inspector_service = inspector_service


class InspectorResources:
    """
    Manages the created Amazon Inspector resources.

    Attributes:
        _resources (Dict[str, InspectorData]): Dictionary mapping resource names to InspectorData instances.
    """

    def __init__(self):
        self._resources: Dict[str, InspectorData] = {}

    def add_resource(self, name: str, inspector_data: InspectorData):
        """
        Adds an Amazon Inspector resource to the resources dictionary.

        Args:
            name (str): Name of the Inspector resource.
            inspector_data (InspectorData): The Inspector data instance.
        """
        self._resources[name] = inspector_data

    def get_inspector_service(self, name: str) -> inspector.CfnService:
        """
        Retrieves an Amazon Inspector service by name.

        Args:
            name (str): Name of the Inspector service.

        Returns:
            inspector.CfnService: The Amazon Inspector service instance.
        """
        return self._resources[name].inspector_service


class InspectorUtility:
    """
    Utility class for configuring and managing Amazon Inspector resources based on configurations.

    Attributes:
        resources (InspectorResources): Manages the created Amazon Inspector resources.
    """

    def __init__(self, scope: Construct, inspector_config: InspectorConfig):
        """
        Initializes InspectorUtility and creates an Amazon Inspector service based on the provided configuration.

        Args:
            scope (Construct): The CDK construct scope for creating resources.
            inspector_config (InspectorConfig): The configuration for Amazon Inspector.
        """
        self.resources = InspectorResources()

        # Enable Inspector service
        if inspector_config.enable_inspector:
            inspector_service = inspector.CfnService(
                scope,
                "InspectorService",
                disable_inspector=False,
            )
            self.resources.add_resource("InspectorService", InspectorData(inspector_service))

            # Add assessment targets
            for ec2_instance in inspector_config.ec2_instances:
                self.add_ec2_target(scope, ec2_instance)

            for lambda_function in inspector_config.lambda_functions:
                self.add_lambda_target(scope, lambda_function)

            for repository in inspector_config.ecr_repositories:
                self.add_ecr_repository(scope, repository)

            # Output Inspector service status
            CfnOutput(
                scope,
                "InspectorServiceStatus",
                value="ENABLED" if inspector_config.enable_inspector else "DISABLED",
                description="Amazon Inspector service status",
            )

    def add_ec2_target(self, scope: Construct, ec2_instance: ec2.Instance):
        """
        Adds an EC2 instance to Amazon Inspector for vulnerability scanning.

        Args:
            scope (Construct): The CDK construct scope.
            ec2_instance (ec2.Instance): The EC2 instance to include in Inspector scans.
        """
        inspector.CfnAssessmentTemplate(
            scope,
            f"{ec2_instance.instance_id}-AssessmentTemplate",
            duration_in_seconds=3600,
            assessment_target_arn=ec2_instance.instance_arn,
            rules_package_arns=[
                "arn:aws:inspector:us-west-2:123456789012:rulespackage/0-gEjTy7Tgs",
                # Add additional rule package ARNs as needed
            ],
        )

    def add_lambda_target(self, scope: Construct, lambda_function: _lambda.Function):
        """
        Adds a Lambda function to Amazon Inspector for vulnerability scanning.

        Args:
            scope (Construct): The CDK construct scope.
            lambda_function (_lambda.Function): The Lambda function to include in Inspector scans.
        """
        inspector.CfnResourceGroup(
            scope,
            f"{lambda_function.function_name}-ResourceGroup",
            resource_group_tags=[{"key": "LambdaFunctionArn", "value": lambda_function.function_arn}],
        )

    def add_ecr_repository(self, scope: Construct, repository: ecr.Repository):
        """
        Adds an ECR repository to Amazon Inspector for scanning container images.

        Args:
            scope (Construct): The CDK construct scope.
            repository (ecr.Repository): The ECR repository to include in Inspector scans.
        """
        inspector.CfnResourceGroup(
            scope,
            f"{repository.repository_name}-ECRResourceGroup",
            resource_group_tags=[{"key": "RepositoryArn", "value": repository.repository_arn}],
        )
