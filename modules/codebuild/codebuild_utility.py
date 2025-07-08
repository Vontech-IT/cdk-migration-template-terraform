from aws_cdk import (
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_logs as logs,
    Duration
)
from constructs import Construct
from modules.iam_role.iam_utility import IamUtility, IamBlueprint, IamConfig
from typing import Optional, List, Dict


class BuildSpecConfig:
    """
    Configuration for CodeBuild build specification.
    
    Attributes:
        version (str): The version of the build specification.
        phases (Dict): The phases of the build process.
        artifacts (Dict): The artifacts configuration.
        environment_variables (Dict): Environment variables for the build.
    """

    def __init__(
        self,
        version: str = "0.2",
        phases: Optional[Dict] = None,
        artifacts: Optional[Dict] = None,
        environment_variables: Optional[Dict] = None
    ):
        self.version = version
        self.phases = phases or {}
        self.artifacts = artifacts or {}
        self.environment_variables = environment_variables or {}


class CodeBuildConfig:
    """
    Configuration class for AWS CodeBuild project.
    
    Attributes:
        project_name (str): Name of the CodeBuild project.
        environment_type (codebuild.BuildEnvironmentType): Type of build environment.
        compute_type (codebuild.ComputeType): Compute resources for the build.
        build_image (codebuild.LinuxBuildImage): Build image to use.
        build_spec_config (BuildSpecConfig): Build specification configuration.
        vpc (Optional[ec2.Vpc]): VPC for the build project.
        subnet_selection (Optional[ec2.SubnetSelection]): Subnet selection for the build project.
        security_groups (Optional[List[ec2.ISecurityGroup]]): Security groups for the build project.
        role (Optional[iam.IRole]): IAM role for the build project.
        environment_variables (Optional[Dict]): Additional environment variables.
        cache (Optional[codebuild.Cache]): Cache configuration for the build project.
    """

    def __init__(
        self,
        project_name: str,
        environment_type: codebuild.EnvironmentType = codebuild.EnvironmentType.LINUX_CONTAINER,
        compute_type: codebuild.ComputeType = codebuild.ComputeType.SMALL,
        build_image: codebuild.LinuxBuildImage = codebuild.LinuxBuildImage.STANDARD_7_0,
        build_spec_config: BuildSpecConfig = None,
        vpc: Optional[ec2.Vpc] = None,
        subnet_selection: Optional[ec2.SubnetSelection] = None,
        security_groups: Optional[List[ec2.ISecurityGroup]] = None,
        role: Optional[iam.IRole] = None,
        environment_variables: Optional[Dict] = None,
        cache: Optional[codebuild.Cache] = None
    ):
        self.project_name = project_name
        self.environment_type = environment_type
        self.compute_type = compute_type
        self.build_image = build_image
        self.build_spec_config = build_spec_config or BuildSpecConfig()
        self.vpc = vpc
        self.subnet_selection = subnet_selection
        self.role = role
        self.environment_variables = environment_variables or {}
        self.cache = cache


class CodeBuildData:
    """
    Stores references to created CodeBuild project.
    
    Attributes:
        project (codebuild.Project): The created CodeBuild project.
    """

    def __init__(self, project: codebuild.Project):
        self.project = project


class CodeBuildResources:
    """
    Manages the resources for CodeBuild projects.
    
    Attributes:
        _resources (Dict[str, CodeBuildData]): A dictionary mapping project names to CodeBuildData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, project_data: CodeBuildData):
        """
        Adds a CodeBuild project to the resources.
        
        Args:
            name (str): The name of the CodeBuild project.
            project_data (CodeBuildData): The CodeBuild data containing the project.
        """
        self._resources[name] = project_data

    def get_project(self, name: str) -> CodeBuildData:
        """
        Retrieves a CodeBuild project by name.
        
        Args:
            name (str): The name of the CodeBuild project.
            
        Returns:
            CodeBuildData: The associated CodeBuild project.
        """
        return self._resources[name]


class CodeBuildBlueprint:
    """
    Blueprint for creating multiple CodeBuild projects based on predefined configurations.
    
    Attributes:
        build_configs (List[CodeBuildConfig]): A list of CodeBuild configurations.
    """

    def __init__(self, build_configs: List[CodeBuildConfig] = []):
        """
        Initializes a CodeBuildBlueprint instance.
        
        Args:
            build_configs (List[CodeBuildConfig], optional): List of CodeBuild configurations. Defaults to an empty list.
        """
        self.build_configs = build_configs

    def add_config(self, build_config: CodeBuildConfig):
        """
        Adds a new CodeBuild configuration to the blueprint.
        
        Args:
            build_config (CodeBuildConfig): The CodeBuild configuration to add.
        """
        self.build_configs.append(build_config)

    @property
    def all_configs(self) -> List[CodeBuildConfig]:
        return self.build_configs


class CodeBuildUtility:
    """
    Utility class for creating and managing CodeBuild projects based on CodeBuildConfig.
    
    Attributes:
        projects (dict): A dictionary of CodeBuild projects created by name.
    """

    def __init__(self, scope: Construct, build_configs: CodeBuildBlueprint):
        self.resources = CodeBuildResources()
        for config in build_configs.all_configs:
            # Create the CodeBuild project
            vpc = config.vpc or ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            if not config.role:
                iam_blueprint = IamBlueprint([IamConfig(f"{config.project_name}CodeBuildRole", service="codebuild", managed_policies=["AdministratorAccess"])])
                iam_utility = IamUtility(scope, iam_blueprint)
                role : iam.IRole = iam_utility.resources.get_role(f"{config.project_name}CodeBuildRole").role

            if config.subnet_selection:
                subnet_selection = config.subnet_selection
            else:
                subnet_selection = ec2.SubnetSelection(subnets=vpc.public_subnets)
            
            project = codebuild.Project(
                scope,
                config.project_name,
                project_name=config.project_name,
                environment=codebuild.BuildEnvironment(
                    build_image=config.build_image,
                    compute_type=config.compute_type,
                    privileged=config.environment_type == codebuild.EnvironmentType.LINUX_CONTAINER,
                ),
                build_spec=codebuild.BuildSpec.from_object({
                    "version": config.build_spec_config.version,
                    "phases": config.build_spec_config.phases,
                    "artifacts": config.build_spec_config.artifacts,
                    "environment_variables": config.build_spec_config.environment_variables
                }),
                vpc=vpc,
                subnet_selection=subnet_selection,
                role=role,
                environment_variables=config.environment_variables,
                cache=config.cache,
                logging=codebuild.LoggingOptions(
                    cloud_watch=codebuild.CloudWatchLoggingOptions(
                        log_group=logs.LogGroup(
                            scope,
                            f"{config.project_name}Logs",
                            log_group_name=f"/aws/codebuild/{config.project_name}"
                        )
                    )
                )
            )

            # Store the project in resources
            self.resources.add_resource(config.project_name, CodeBuildData(project))
