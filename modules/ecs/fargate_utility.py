# modules/ecs/fargate_utility.py
from constructs import Construct
from imports.aws.ecs_cluster import EcsCluster
from imports.aws.ecs_task_definition import EcsTaskDefinition
from imports.aws.ecs_service import EcsService, EcsServiceNetworkConfiguration
import json

class FargateModule(Construct):
    """
    A reusable module for creating a full ECS Fargate service.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 vpc_id: str,
                 subnet_ids: list[str],
                 security_group_ids: list[str],
                 task_cpu: str,
                 task_memory: str,
                 container_image: str,
                 container_port: int,
                 execution_role_arn: str,
                 task_role_arn: str = None,
                 desired_count: int = 1,
                 tags: dict = None):
        """
        Args:
            name (str): A name prefix for the ECS resources.
            vpc_id (str): The ID of the VPC.
            subnet_ids (list[str]): A list of private subnet IDs for the tasks.
            security_group_ids (list[str]): Security groups for the tasks.
            task_cpu (str): The CPU units for the task (e.g., '256').
            task_memory (str): The memory for the task (e.g., '512').
            container_image (str): The Docker image to use for the container.
            container_port (int): The port the container listens on.
            execution_role_arn (str): The ARN of the IAM role for ECS task execution.
            task_role_arn (str, optional): The ARN of the IAM role for the task itself.
            desired_count (int, optional): The desired number of tasks. Defaults to 1.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.cluster = EcsCluster(self, "EcsCluster",
            name=f"{name}-cluster",
            tags={"Name": f"{name}-cluster", **(tags or {})}
        )

        container_definitions = json.dumps([
            {
                "name": f"{name}-container",
                "image": container_image,
                "portMappings": [
                    {
                        "containerPort": container_port,
                        "hostPort": container_port
                    }
                ]
            }
        ])

        self.task_definition = EcsTaskDefinition(self, "TaskDefinition",
            family=f"{name}-task",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            cpu=task_cpu,
            memory=task_memory,
            execution_role_arn=execution_role_arn,
            task_role_arn=task_role_arn,
            container_definitions=container_definitions,
            tags={"Name": f"{name}-task", **(tags or {})}
        )

        self.service = EcsService(self, "FargateService",
            name=f"{name}-service",
            cluster=self.cluster.id,
            task_definition=self.task_definition.arn,
            launch_type="FARGATE",
            desired_count=desired_count,
            network_configuration=EcsServiceNetworkConfiguration(
                subnets=subnet_ids,
                security_groups=security_group_ids
            ),
            tags={"Name": f"{name}-service", **(tags or {})}
        )
