# Lambda Utility for AWS CDK

This Lambda Utility allows you to create and configure multiple AWS Lambda functions programmatically within your CDK application. This utility is integrated with a `StackBuilder` class for simplified management and resource reuse. 

## Usage with the Builder Class

The `StackBuilder` class is designed to use the `LambdaUtility` for streamlined Lambda function creation and configuration. Here’s how to incorporate the Lambda utility in your project:

### Step 1: Define Lambda Configuration

Define a list of Lambda function configurations as dictionaries to specify the `function_name`, `runtime`, `memory`, `handler`, and code source (`code_path` or `code_s3uri`).

Example:

```python
lambda_configs = [
    {
        "function_name": "MyFunction",
        "runtime": lambda_.Runtime.PYTHON_3_8,
        "memory": 512,
        "handler": "app.handler",
        "code_path": "./path/to/code"
    },
    {
        "function_name": "AnotherFunction",
        "runtime": lambda_.Runtime.NODEJS_14_X,
        "memory": 1024,
        "handler": "index.handler",
        "code_s3uri": "my-bucket/code.zip"
    }
]
```

### Step 2: Initialize `StackBuilder` and Add Lambda Functions

In the CDK app, initialize `StackBuilder` and use the `add_lambda` method to create Lambda functions from the configurations.

```python
from aws_cdk import App
from modules.stack_builder import StackBuilder

app = App()
stack_builder = StackBuilder(app, "LambdaStack")

lambda_resources = stack_builder.add_lambda(lambda_configs=lambda_configs)

app.synth()
```

The `add_lambda` method returns a `LambdaResources` object containing all Lambda functions created, accessible by their configuration-defined names.

## Lambda Configuration Parameters

| Parameter       | Type               | Required       | Description                                                                                                           | Default                               |
|-----------------|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `function_name` | `str`              | Yes            | The unique name for the Lambda function.                                                                              | None                                  |
| `runtime`       | `lambda_.Runtime`  | No             | The runtime environment for the Lambda function.                                                                      | `lambda_.Runtime.PYTHON_3_12`         |
| `memory`        | `int`              | No             | The amount of memory allocated to the function in MB.                                                                 | `512`                                 |
| `handler`       | `str`              | No             | The handler method for the Lambda function.                                                                           | `"main.handler"`                      |
| `code_path`     | `str`              | Conditional    | Path to the local code asset directory. Must be provided if `code_s3uri` is not used, and vice versa.                 | None                                  |
| `code_s3uri`    | `str`              | Conditional    | S3 URI for the code source in the format `"bucket/key"`. Must be provided if `code_path` is not used, and vice versa. | None                                  |
| `role`          | `iam.Role`         | No             | An existing IAM role for the Lambda function.                                                                         | New role with basic execution policy  |
| `permission`    | `str`              | No             | Service principal to grant invoke permissions to.                                                                     | None                                  |

> **Note**: Either `code_path` or `code_s3uri` **must** be provided, but **not both**.