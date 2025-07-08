from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_apigatewayv2 as apigatewayv2
from aws_cdk import aws_apigatewayv2_integrations as apigatewayv2_integrations
from aws_cdk import aws_lambda as lambda_
from constructs import Construct
from typing import Generator


class HTTPRouteConfig:
    """
    Configuration for an HTTP route.

    Attributes:
        path (str): The path of the route.
        methods (list[apigatewayv2.HttpMethod]): The HTTP methods allowed for the route.
        lambda_function (lambda_.Function): The Lambda function to invoke.
    """
    GET = apigatewayv2.HttpMethod.GET
    POST = apigatewayv2.HttpMethod.POST
    PUT = apigatewayv2.HttpMethod.PUT
    DELETE = apigatewayv2.HttpMethod.DELETE
    PATCH = apigatewayv2.HttpMethod.PATCH
    HEAD = apigatewayv2.HttpMethod.HEAD
    OPTIONS = apigatewayv2.HttpMethod.OPTIONS
    ANY = apigatewayv2.HttpMethod.ANY

    def __init__(self, path: str, methods: list[apigatewayv2.HttpMethod], lambda_function: lambda_.Function):
        self.path: str = path
        self.methods: list[apigatewayv2.HttpMethod] = methods
        self.lambda_function: lambda_.Function = lambda_function

class ApiGatewayConfig:
    """
    Configuration for an API Gateway.

    Attributes:
        api_name (str): The name of the API Gateway.
        description (str, optional): Description of the API Gateway.
        stage_name (str, optional): The deployment stage name (default is 'prod').
        type (str, optional): The type of API Gateway (default is 'HTTP'), values: HTTP, REST.
        http_routes (list[HTTPRouteConfig], optional): A list of HTTPRouteConfig instances.
    """
    def __init__(self, api_name: str, description: str = "API Gateway", stage_name: str = "$default", type: str = "HTTP", http_routes: list[HTTPRouteConfig] = [], default_route_lambda_function: lambda_.Function = None):
        self.api_name: str = api_name
        self.description: str = description
        self.stage_name: str = stage_name
        self.type: str = type
        self.http_routes: list[HTTPRouteConfig] = http_routes
        self.default_route_lambda_function: lambda_.Function = default_route_lambda_function


class ApiGatewayBlueprint:
    """
    A blueprint for managing multiple API Gateway configurations.

    Attributes:
        api_configs (list[ApiGatewayConfig]): A list of API Gateway configurations.
    """
    def __init__(self, api_configs: list[ApiGatewayConfig] = []):
        self.api_configs: list[ApiGatewayConfig] = api_configs
    
    def add_config(self, api_config: ApiGatewayConfig):
        """Adds a new ApiGatewayConfig to the blueprint."""
        self.api_configs.append(api_config)
    
    @property
    def all_configs(self) -> Generator[ApiGatewayConfig, None, None]:
        """Generator that yields each ApiGatewayConfig in the blueprint."""
        for config in self.api_configs:
            yield config


class ApiGatewayData:
    """
    Wrapper class for an API Gateway instance.

    Attributes:
        api (apigateway.RestApi): The API Gateway instance.
    """
    def __init__(self, api: apigateway.RestApi):
        self.api: apigateway.RestApi|apigatewayv2.HttpApi = api


class ApiGatewayResources:
    """
    A collection of API Gateway instances.

    Attributes:
        _api_dict (dict): A dictionary that maps API names to ApiGatewayData instances.
    """
    def __init__(self):
        self._api_dict = {}

    def add_api(self, name: str, api_data: ApiGatewayData):
        """Adds an ApiGatewayData instance to the collection."""
        self._api_dict[name] = api_data

    def get_api(self, name: str) -> ApiGatewayData:
        """Retrieves an ApiGatewayData instance by name."""
        return self._api_dict[name]


class ApiGatewayUtility:
    """
    Utility class for creating and managing API Gateway instances based on an ApiGatewayBlueprint.
    """
    def __init__(self, scope: Construct, api_blueprint: ApiGatewayBlueprint) -> None:
        self.resources = ApiGatewayResources()
        self.scope = scope
        
        for config in api_blueprint.all_configs:
            api_mapping = {
                "HTTP": self.create_http_api,
                "REST": self.create_rest_api
            }
            api = api_mapping[config.type](config)
            self.resources.add_api(config.api_name, ApiGatewayData(api))

    def create_http_api(self, config: ApiGatewayConfig) -> apigatewayv2.HttpApi:
        default_lambda_integration = None

        if config.default_route_lambda_function:
            integration_id = config.api_name+"DefaultIntegration"
            default_lambda_integration = apigatewayv2_integrations.HttpLambdaIntegration(integration_id, config.default_route_lambda_function)

        api = apigatewayv2.HttpApi(
                    self.scope,
                    id=config.api_name,
                    api_name=config.api_name,
                    description=config.description,
                    default_integration=default_lambda_integration
                )
        
        for route_config in config.http_routes:
            integration_id = config.api_name+route_config.lambda_function.function_name+"Integration"
            lambda_integration = apigatewayv2_integrations.HttpLambdaIntegration(integration_id, route_config.lambda_function)
            route = api.add_routes(path=route_config.path, methods=route_config.methods, integration=lambda_integration)

        return api
    
    def create_rest_api(self, config: ApiGatewayConfig) -> apigateway.RestApi:
        api = apigateway.RestApi(
                    self.scope,
                    id=config.api_name,
                    rest_api_name=config.api_name,
                    description=config.description,
                    deploy_options=apigateway.StageOptions(stage_name=config.stage_name)
                )
        return api
    
