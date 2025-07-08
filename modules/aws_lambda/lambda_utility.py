from aws_cdk import (
    CfnOutput, 
    aws_lambda as lambda_, 
    aws_iam as iam, 
    aws_s3_assets as s3_assets, 
    Duration, 
    aws_ecr as ecr,
    aws_ssm as ssm
)
from modules.iam_role.iam_utility import IamUtility, IamBlueprint, IamConfig
from constructs import Construct
from typing import Generator
import shutil
import tempfile
import boto3
import subprocess
import os

class LambdaConfig:
    """
    Configuration for an AWS Lambda function.

    Attributes:
        function_name (str): The name of the Lambda function.
        runtime (lambda_.Runtime): The runtime environment for the Lambda function (default is Python 3.12).
        memory (int): The amount of memory allocated to the function in MB (default is 512).
        timeout (int): Lambda Timeout in Seconds (default is 120).
        handler (str): The name of the method within your code that Lambda calls to execute the function (default is "main.handler").
        code_path (str): The local path to the Lambda function's code (default is "./basic-lambda").
        code_s3uri (str, optional): The S3 URI of the code for the Lambda function.
        code_imageuri (str, optional): The Image URI for ECR for the lambda code
        role (iam.Role, optional): The IAM role that the Lambda function assumes.
        libraries (str, optional): List of thirdpary libraries lambda code utilizes.
        permission (str, optional): The permission required for invoking the Lambda function.
    """

    def __init__(self, function_name: str, runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_12, 
                 memory: int = 512, timeout: int = 120, handler: str = "main.handler", code_path: str = None, 
                 code_s3uri: str = None, code_imageuri: str = None, role: iam.Role = None, permission: str = None, ssm_path_env: str = None, environment_variables: dict[str, str] = {}, libraries: list[str] = []):
        self.function_name: str = function_name
        self.runtime: lambda_.Runtime = runtime
        self.memory: int = memory
        self.timeout: int = timeout
        self.handler: str = handler
        self.code_path: str = code_path
        self.code_s3uri: str = code_s3uri
        self.code_imageuri: str = code_imageuri
        self.role: iam.Role = role
        self.ssm_path_env: str = ssm_path_env
        self.permission: str = permission
        self.environment_variables: dict[str, str] = environment_variables
        self.libraries: list[str] = libraries
        


class LambdaBlueprint:
    """
    A blueprint for managing multiple Lambda configurations.

    Attributes:
        lambda_configs (list[LambdaConfig]): A list of LambdaConfig instances representing the configurations.

    Methods:
        add_config(lambda_config: LambdaConfig): Adds a new LambdaConfig to the blueprint.
        lambda_configs (Generator[LambdaConfig, None, None]): A generator that yields LambdaConfig instances.
    """

    def __init__(self, lambda_configs: list[LambdaConfig] = []):
        self.lambda_configs: list[LambdaConfig] = lambda_configs
    
    def add_config(self, lambda_config: LambdaConfig):
        """Adds a new LambdaConfig to the blueprint."""
        self.lambda_configs.append(lambda_config)
    
    @property
    def all_configs(self) -> Generator[LambdaConfig, None, None]:
        """Generator that yields each LambdaConfig in the blueprint."""
        for config in self.lambda_configs:
            yield config


class LambdaData:
    """
    Wrapper class for an AWS Lambda function instance.

    Attributes:
        function (lambda_.Function): The AWS Lambda function instance.
    """

    def __init__(self, function: lambda_.Function):
        self.function: lambda_.Function = function


class LambdaResources:
    """
    A collection of Lambda functions.

    Attributes:
        _lambda_dict (dict): A dictionary that maps Lambda function names to LambdaData instances.

    Methods:
        add_lambda(name: str, lambda_data: LambdaData): Adds a LambdaData instance to the collection.
        get_lambda(name: str) -> LambdaData: Retrieves a LambdaData instance by name.
    """

    def __init__(self):
        self._lambda_dict = {}

    def add_lambda(self, name: str, lambda_data: LambdaData):
        """Adds a LambdaData instance to the collection."""
        self._lambda_dict[name] = lambda_data

    def get_lambda(self, name: str) -> LambdaData:
        """Retrieves a LambdaData instance by name."""
        return self._lambda_dict[name]


class LambdaUtility:
    """
    Utility class for creating and managing AWS Lambda functions based on a LambdaBlueprint.

    Attributes:
        resources (LambdaResources): An instance of LambdaResources that stores created Lambda functions.

    Methods:
        __init__(scope: Construct, lambda_blueprint: LambdaBlueprint): Initializes the utility with a given scope and blueprint.
    """

    def __init__(self, scope: Construct, lambda_blueprint: LambdaBlueprint) -> None:
        self.resources = LambdaResources()
        self.scope = scope
        
        for config in lambda_blueprint.all_configs:
            # Extract configuration values with defaults
            self.function_name = config.function_name
            self.runtime = config.runtime
            memory_size = config.memory
            handler = config.handler
            code_path = config.code_path
            code_s3uri = config.code_s3uri
            code_imageuri = config.code_imageuri
            role = config.role
            timeout = Duration.seconds(config.timeout)
            permission = config.permission
            libraries = config.libraries

            # Determine Lambda code based on provided options
            if code_s3uri:
                bucket_name, key = code_s3uri.split("/", 1)  # Format assumed as "bucket/key"
                code = lambda_.Code.from_bucket(bucket=bucket_name, key=key)
            elif code_imageuri:
                region = os.getenv("AWS_REGION")
                account_id = os.getenv("AWS_ACCOUNT_ID")
                repository_name = code_imageuri.split("/")[1].split(":")[0]
                ecr_repository = ecr.Repository.from_repository_name(
                    self.scope, self.function_name+repository_name, repository_name=repository_name
                )
                handler=lambda_.Handler.FROM_IMAGE
                self.runtime = lambda_.Runtime.FROM_IMAGE
                code = lambda_.Code.from_ecr_image(ecr_repository, tag_or_digest=code_imageuri.split(":")[1])

            elif code_path:
                code = lambda_.Code.from_asset(code_path)
            else:
                raise ValueError(f"Lambda function {self.function_name} must specify a code source.")

            # Create a default IAM role if none is provided
            if not role:
                default_role_config = IamConfig(f"{self.function_name}LambdaRole", "lambda", managed_policies=["service-role/AWSLambdaBasicExecutionRole"])
                iam_blueprint = IamBlueprint([default_role_config])
                iam_role = IamUtility(scope, iam_blueprint)
                role = iam_role.resources.get_role(f"{self.function_name}LambdaRole").role

            # Create the Lambda function
            lambda_function = lambda_.Function(
                scope, 
                f"{self.function_name}",
                function_name=self.function_name,
                runtime=self.runtime,
                handler=handler,
                memory_size=memory_size,
                code=code,
                timeout=timeout,
                role=role
            )
            for key, value in config.environment_variables.items():
                lambda_function.add_environment(key, value)
            
            if config.ssm_path_env:
                ssm_environment_variables = self._get_environment_variables(config.ssm_path_env)

                for key, value in ssm_environment_variables.items():
                    lambda_function.add_environment(key, value)

            if libraries:
                layer = self.create_layer(libraries)
                lambda_function.add_layers(layer)

            # Grant specified permissions if provided
            if permission:
                lambda_function.grant_invoke(iam.ServicePrincipal(permission))

            # Store Lambda function in LambdaResources
            self.resources.add_lambda(self.function_name, LambdaData(lambda_function))

            # Output the Lambda ARN for reference
            # CfnOutput(scope, f"{self.function_name}Arn", value=lambda_function.function_arn)

    def _get_environment_variables(self, ssm_path_env: str):
        env_vars = {}
        if ssm_path_env:
            ssm_client = boto3.client("ssm", region_name=os.getenv("AWS_REGION"))

            next_token = None

            while True:
                kwargs = {
                    "Path": ssm_path_env,
                    "WithDecryption": False,
                    "Recursive": True  # Optional, fetches parameters recursively in sub-paths
                }
                if next_token:
                    kwargs["NextToken"] = next_token

                response = ssm_client.get_parameters_by_path(**kwargs)

                for param in response.get("Parameters", []):
                    param_name = param["Name"].split("/")[-1]
                    param_value = ssm.StringParameter.value_for_string_parameter(self.scope, param["Name"])
                    env_vars[param_name] = param_value

                next_token = response.get("NextToken")
                if not next_token:
                    break

        return env_vars
    
    def create_layer(self, libraries: list[str]) -> lambda_.LayerVersion:
        """
        Creates and returns a Lambda layer with the specified libraries.

        Returns:
            lambda_.LayerVersion: The created Lambda layer.
        """
        # Create a temporary directory for packaging the layer
        temp_dir = tempfile.mkdtemp()
        layer_dir = os.path.join(temp_dir, "python")
        os.makedirs(layer_dir, exist_ok=True)

        try:
            # Install the specified libraries in the layer directory
            print(layer_dir)
            subprocess.check_call([
                "pip", "install", *libraries, 
                "--target", layer_dir,
                "--no-cache-dir"  # Avoid caching to reduce layer size
            ])

            # Package the layer directory as a zip file
            layer_zip = shutil.make_archive(temp_dir, 'zip', temp_dir)

            # Use CDK to create an asset from the zip file
            asset = s3_assets.Asset(self.scope, f"{self.function_name}LayerAsset", path=layer_zip)

            # Define the Lambda layer using the asset
            layer = lambda_.LayerVersion(
                self.scope,
                f"{self.function_name}Layer",
                layer_version_name=f"{self.function_name}Layer",
                code=lambda_.Code.from_bucket(asset.bucket, asset.s3_object_key),
                compatible_runtimes=[self.runtime]
            )

            return layer
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir)  
