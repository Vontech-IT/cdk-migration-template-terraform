# VPC Utility README

This VPC utility creates, manages, and stores VPC resources, including subnets, route tables, and an optional NAT Gateway, as configurable AWS CDK constructs. It is designed to be used in combination with a builder class, such as `StackBuilder`, for seamless VPC provisioning within larger AWS infrastructure stacks.

## Overview

`VpcUtility` accepts a list of VPC configuration dictionaries, each specifying settings for a single VPC. It initializes and organizes these resources into the `VPCResources` class, where individual VPCs can be retrieved by name for further use in other parts of your application. Each VPC setup includes optional NAT Gateway provisioning, public and private subnets, and associated route tables.

## Using VPC Utility with StackBuilder

To integrate the `VpcUtility` with the `StackBuilder` class, create an instance of `VpcUtility` within the `StackBuilder` and pass the desired VPC configurations. `StackBuilder` can access and manage the generated VPCs by name through the `VPCResources` manager.

### Example

Here’s an example of how to use `VpcUtility` in a `StackBuilder` class:

```python
import modules.vpc.vpc_utility  # Adjust the import path as needed
from aws_cdk import Stack
from constructs import Construct

class StackBuilder(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
    def add_vpc(self, vpc_configs: list[dict]) -> modules.vpc.vpc_utility.VPCResources:
        vpc_utility = modules.vpc.vpc_utility.VpcUtility(self, vpc_configs)
        return vpc_utility.resources
```

With this setup, you can use `add_vpc()` in `StackBuilder` to add VPCs and retrieve them by name for further use.

## Parameters

The following table describes the configuration options for each VPC dictionary entry:

| Parameter       | Type      | Required | Default Value      | Description |
|-----------------|-----------|----------|--------------------|-------------|
| `name`          | `str`     | No       | `"Vpc"`           | The name identifier for the VPC. |
| `vpc_cidr`      | `str`     | No       | `"172.67.0.0/16"` | The CIDR block for the VPC. |
| `provision_nat` | `bool`    | No       | `True`            | Whether to provision a NAT Gateway in the VPC's private subnets. If `False`, no NAT Gateway will be created. |

## VPCData Class

Each VPC created by `VpcUtility` is represented by the `VPCData` class, which contains references to the following resources:

- **VPC** (`ec2.Vpc`): The primary VPC object.
- **Internet Gateway** (`ec2.CfnInternetGateway`): The Internet Gateway attached to the VPC.
- **Public Route Table** (`ec2.IRouteTable`): The route table associated with the public subnets.
- **Private Route Table** (`ec2.IRouteTable`): The route table associated with the private subnets.
- **Public Subnets** (`list[ec2.ISubnet]`): List of public subnets within the VPC.
- **Private Subnets** (`list[ec2.ISubnet]`): List of private subnets within the VPC.
- **NAT Gateway** (`ec2.CfnNatGateway`, optional): NAT Gateway, if provisioned.

### Retrieving VPC Resources

You can retrieve VPC resources by name using the `get_vpc` method on the `VPCResources` instance, which returns a `VPCData` object.

```python
# Example: Accessing a VPC by name in StackBuilder
vpc_resources = stack_builder.add_vpc(vpc_configs=[{"name": "MyVpc"}])
vpc_data = vpc_resources.get_vpc("MyVpc")
print(vpc_data.public_subnets)
```

This utility simplifies VPC creation while offering flexibility through customizable configuration parameters.