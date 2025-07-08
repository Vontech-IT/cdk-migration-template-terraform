# modules/api_gateway/api_gateway_utility.py
from constructs import Construct
from imports.aws.apigatewayv2_api import Apigatewayv2Api
from imports.aws.apigatewayv2_integration import Apigatewayv2Integration
from imports.aws.apigatewayv2_route import Apigatewayv2Route
from imports.aws.apigatewayv2_stage import Apigatewayv2Stage
from imports.aws.lambda_permission import LambdaPermission

class ApiGatewayHttpApiModule(Construct):
    """
    A reusable module for creating an API Gateway HTTP API with a Lambda integration.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 route_key: str, # e.g., "GET /items"
                 lambda_function_arn: str,
                 lambda_function_name: str,
                 tags: dict = None):
        """
        Args:
            name (str): The name for the API Gateway.
            route_key (str): The route key (e.g., 'GET /items', 'POST /users').
            lambda_function_arn (str): The ARN of the Lambda function to integrate with.
            lambda_function_name (str): The name of the Lambda function (for permissions).
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.api = Apigatewayv2Api(self, "HttpApi",
            name=name,
            protocol_type="HTTP",
            tags={"Name": name, **(tags or {})}
        )

        self.integration = Apigatewayv2Integration(self, "LambdaIntegration",
            api_id=self.api.id,
            integration_type="AWS_PROXY",
            integration_uri=lambda_function_arn,
            payload_format_version="2.0"
        )

        self.route = Apigatewayv2Route(self, "ApiRoute",
            api_id=self.api.id,
            route_key=route_key,
            target=f"integrations/{self.integration.id}"
        )

        self.stage = Apigatewayv2Stage(self, "ApiStage",
            api_id=self.api.id,
            name="$default",
            auto_deploy=True
        )

        LambdaPermission(self, "ApiGatewayLambdaPermission",
            statement_id="AllowExecutionFromAPIGateway",
            action="lambda:InvokeFunction",
            function_name=lambda_function_name,
            principal="apigateway.amazonaws.com",
            source_arn=f"{self.api.execution_arn}/*/*"
        )

        self.endpoint = self.api.api_endpoint
