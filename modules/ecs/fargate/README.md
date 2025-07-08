# EcsFargateUtility README

`EcsFargateUtility` is a utility for deploying and managing AWS Fargate services and tasks using the AWS Cloud Development Kit (CDK). This utility simplifies the setup and management of Elastic Container Service (ECS) resources, allowing developers to configure clusters, task definitions, and services for both long-running and short-lived tasks efficiently.

## Overview

The `EcsFargateUtility` class accepts a list of configuration dictionaries, each specifying settings for a single Fargate service or task. It organizes these resources into the `EcsFargateResources` class, where individual services and tasks can be easily retrieved for further management. The utility automatically creates ECS clusters, task definitions, and necessary outputs.

## Example Usage with StackBuilder

You can integrate the `EcsFargateUtility` into a stack builder class that manages ECS resources. Below is an example of how to use the utility in a `StackBuilder` class to add ECS Fargate services and tasks.

### Example StackBuilder Implementation

```python
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from modules.builder import StackBuilder
from modules.ecs.fargate.fargate_utility import EcsFargateResources, EcsFargateUtility

env = cdk.Environment(account=os.getenv("AWS_ACCOUNT_ID"), region=os.getenv("AWS_REGION"))

app = cdk.App()

# Initialize the StackBuilder
builder = StackBuilder(app, "test-ecs")

# Define ECS configuration
ecs_configs = [
    {
        "name": "MyFargateTask",
        "image_uri": "my-task-image:latest",
        "cpu": 256,
        "memory_limit": 512,
        "assign_public_ip": False,
        "is_service": False,  # Short-lived task
    },
]

# Add ECS Fargate resources using the builder
builder.add_ecs_fargate(ecs_configs=ecs_configs)

# Synthesize the app
app.synth()
```

In this example, the `StackBuilder` initializes an ECS configuration for a short-lived task and adds it to the stack using the `add_ecs_fargate` method. This allows for easy integration and management of ECS resources within the overall infrastructure.

## Parameters

The following table describes the configuration options for each Fargate configuration dictionary entry:

| Parameter          | Type              | Required | Default Value        | Description |
|--------------------|-------------------|----------|----------------------|-------------|
| `name`     | `str`             | No       | `"EcsFargateService"`| The name of the Fargate service or task. |
| `image_uri`        | `str`             | Yes      | N/A                  | The URI of the Docker image to use. |
| `container_port`   | `int`             | No       | `80`                 | The port on which the container listens. |
| `cpu`              | `int`             | No       | `512`                | The number of CPU units to allocate. |
| `vpc`              | `ec2.Vpc`         | No       | Default VPC          | The VPC to deploy the resources in. If not provided, the default VPC is used. |
| `memory_limit`     | `int`             | No       | `1024`               | The amount of memory (in MiB) to allocate. |
| `assign_public_ip` | `bool`            | No       | `False`              | Whether to assign a public IP to the service/task. |
| `is_service`       | `bool`            | No       | `True`               | Flag indicating if the configuration is for a long-running service (default) or a short-lived task. |
| `desired_count`    | `int`             | No       | `1`                  | The desired number of service instances (only applicable if `is_service` is `True`). |

## Classes

### EcsFargateData

This is the base class containing information about the ECS cluster and task definition.

### EcsFargateServiceData

Inherits from `EcsFargateData` and includes the Fargate service, which is used for long-running tasks.

### EcsFargateTaskData

Inherits from `EcsFargateData` and includes the Fargate task, which is used for short-lived tasks.

### EcsFargateResources

This class manages collections of Fargate services and tasks. It provides methods to add and retrieve services and tasks by name.

### EcsFargateUtility

The main utility class for creating ECS Fargate services and tasks based on the provided configurations. It automatically handles the creation of clusters and task definitions and manages necessary output resources.

## Outputs

The utility outputs relevant ARNs for both the created services and task definitions, allowing for easy reference in other parts of your AWS infrastructure.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.