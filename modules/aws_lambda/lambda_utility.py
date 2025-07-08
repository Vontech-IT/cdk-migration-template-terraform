# modules/aws_lambda/lambda_utility.py
from constructs import Construct
from imports.aws.lambda_function import LambdaFunction
from imports.aws.iam_role import IamRole
import json

class LambdaModule(Construct):
    """
    A reusable module for creating an AWS Lambda function.
    """
    def __init__(self, scope: Construct, id: str, *,
                 function_name: str,
                 runtime: str,
                 handler: str,
                 source_code_path: str, # Path to the deployment package
                 role_arn: str,
                 timeout: int = 3,
                 memory_size: int = 128,
                 tags: dict = None):
        """
        Args:
            function_name (str): The name of the Lambda function.
            runtime (str): The runtime environment (e.g., 'python3.9', 'nodejs16.x').
            handler (str): The function entrypoint (e.g., 'index.handler').
            source_code_path (str): The local path to the zipped deployment package.
            role_arn (str): The ARN of the IAM role for the function.
            timeout (int, optional): The function timeout in seconds. Defaults to 3.
            memory_size (int, optional): The memory allocation in MB. Defaults to 128.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.lambda_function = LambdaFunction(self, "LambdaFunction",
            function_name=function_name,
            runtime=runtime,
            handler=handler,
            filename=source_code_path,
            role=role_arn,
            timeout=timeout,
            memory_size=memory_size,
            tags={"Name": function_name, **(tags or {})}
        )

        self.arn = self.lambda_function.arn
        self.name = self.lambda_function.function_name
