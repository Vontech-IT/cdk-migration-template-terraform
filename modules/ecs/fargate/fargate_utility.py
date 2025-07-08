from aws_cdk import CfnOutput, aws_ecs as ecs, aws_ec2 as ec2
from constructs import Construct

from modules.iam_role.iam_utility import IamUtility


class EcsFargateTaskData:
    def __init__(self, cluster: ecs.Cluster, task_definition: ecs.TaskDefinition):
        self.cluster = cluster
        self.task_definition = task_definition

class EcsFargateServiceData(EcsFargateTaskData):
    def __init__(self, cluster: ecs.Cluster, task_definition: ecs.TaskDefinition, service: ecs.FargateService):
        super().__init__(cluster, task_definition)
        self.service = service  # For long-running services

class EcsFargateResources:
    def __init__(self):
        self._services_dict = {}
        self._tasks_dict = {}

    def add_service(self, name: str, ecs_data: EcsFargateServiceData):
        self._services_dict[name] = ecs_data

    def get_service(self, name: str) -> EcsFargateServiceData:
        return self._services_dict.get(name)

    def add_task(self, name: str, ecs_data: EcsFargateTaskData):
        self._tasks_dict[name] = ecs_data

    def get_task(self, name: str) -> EcsFargateTaskData:
        return self._tasks_dict.get(name)


class EcsFargateUtility:
    def __init__(self, scope: Construct, ecs_configs: list[dict]) -> None:
        self.resources = EcsFargateResources()

        for config in ecs_configs:
            service_name = config.get("name", "EcsFargateService")
            image_uri = config["image_uri"]
            container_port = config.get("container_port", 80)
            cpu = config.get("cpu", 512)
            vpc = config.get("vpc", None)
            resources = config.get("resources", [])
            actions = config.get("actions", [])
            memory_limit = config.get("memory_limit", 1024)
            assign_public_ip = config.get("assign_public_ip", False)
            is_service = config.get("is_service", True)  # Default to creating a long-running service

            # Use the default VPC if none is provided
            if vpc is None:
                vpc = ec2.Vpc.from_lookup(scope, "DefaultVpc", is_default=True)
            
            if len(actions) > 0 and len(resources) == 0:
                resources = ["*"]



            # Create ECS Cluster
            cluster = ecs.Cluster(scope, f"{service_name}Cluster", cluster_name=f"{service_name}-Cluster", vpc=vpc)

            iam = IamUtility(scope, role_configs=[
                {
                    "role_name": f"{service_name}-TaskExecutionRole", 
                    "service": f"ecs-tasks",
                    "managed_policies": ["AmazonECSTaskExecutionRolePolicy"]
                },
                {
                    "role_name": f"{service_name}-TaskRole",
                    "service": f"ecs-tasks",
                    "permissions": [
                        {
                            "actions": actions,
                            "resources": resources
                        }
                    ]
                }
                
                ])
            # Task Definition
            task_definition = ecs.FargateTaskDefinition(
                scope, 
                f"{service_name}TaskDef",
                family=f"{service_name}-TaskDef",
                cpu=cpu,
                execution_role=iam.resources.get_role(f"{service_name}-TaskExecutionRole").role,
                task_role=iam.resources.get_role(f"{service_name}-TaskRole").role,
                memory_limit_mib=memory_limit
            )

            # Add container to the task definition
            container = task_definition.add_container(
                f"{service_name}Container",
                container_name=f"{service_name}-Container",
                image=ecs.ContainerImage.from_registry(image_uri),
                logging=ecs.LogDrivers.aws_logs(stream_prefix=service_name)
            )

            if is_service:
                # Create Fargate Service (for long-running)
                container.add_port_mappings(
                    ecs.PortMapping(container_port=container_port)
                )
                service = ecs.FargateService(
                    scope, f"{service_name}Service",
                    service_name=f"{service_name}-Service",
                    cluster=cluster,
                    task_definition=task_definition,
                    desired_count=config.get("desired_count", 1),
                    assign_public_ip=assign_public_ip,
                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
                )
                self.resources.add_service(service_name, EcsFargateServiceData(cluster, task_definition, service=service))

                # Output the service ARN
                CfnOutput(scope, f"{service_name}ServiceArn", value=service.service_arn)

            else:
                # Create Fargate Task (for short-lived tasks)
                self.resources.add_task(service_name, EcsFargateTaskData(cluster, task_definition))

            CfnOutput(scope, f"{service_name}TaskDefArn", value=task_definition.task_definition_arn)
