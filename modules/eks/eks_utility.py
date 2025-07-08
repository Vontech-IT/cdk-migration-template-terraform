import os
from aws_cdk import (
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    Tags,
)

from constructs import Construct
from typing import Optional, List, Dict, Generator
from modules.iam_role.iam_utility import IamBlueprint, IamConfig, IamUtility


class EKSNodeGroupConfig:
    """
    Configuration for creating a node group in the EKS cluster.

    Attributes:
        nodegroup_name (str): Name of the node group.
        instance_types (List[str]): List of EC2 instance types for the nodes !!! Instace Family should not be less than large (t3.large).
        min_size (int): Minimum number of nodes in the group.
        max_size (int): Maximum number of nodes in the group.
        desired_size (int): Desired number of nodes.
        disk_size (int): Disk size in GB for the nodes.
        ami_type (str): AMI type for the nodes (AL2_x86_64, AL2_x86_64_GPU, etc).
        subnets (Optional[ec2.SubnetSelection]): The subnets where nodes will be created.
    """

    def __init__(
        self,
        nodegroup_name: str,
        instance_types: List[str] = ["t3.large"],
        min_size: int = 1,
        max_size: int = 1,
        desired_size: int = 1,
        disk_size: int = 20,
        node_role: Optional[iam.Role] = None,
        ami_type: str = eks.NodegroupAmiType.AL2_X86_64,
        subnets: Optional[ec2.Subnet] = None,
    ):
        self.nodegroup_name = nodegroup_name
        self.instance_types = [ec2.InstanceType(instance_type) for instance_type in instance_types]
        self.min_size = min_size
        self.max_size = max_size if desired_size <= max_size else desired_size
        self.desired_size = desired_size
        self.disk_size = disk_size
        self.ami_type = ami_type
        self.subnets = ec2.SubnetSelection(subnets=subnets)
        self.node_role = node_role


class EKSConfig:
    """
    Configuration for creating an EKS Cluster.

    Attributes:
        cluster_name (str): Name of the EKS cluster.
        vpc (ec2.Vpc): VPC for the EKS cluster.
        version (string): Kubernetes version for the EKS cluster.
        endpoint_access (eks.EndpointAccess): Endpoint access configuration.
        node_groups (List[EKSNodeGroupConfig]): List of node group configurations.
        cluster_role (Optional[iam.Role]): IAM role for the EKS cluster.
        security_group (Optional[ec2.SecurityGroup]): Security group for the cluster control plane.
        tags (Optional[Dict[str, str]]): Tags for the cluster.
    """

    def __init__(
        self,
        cluster_name: str,
        vpc: ec2.Vpc,
        version: Optional[str] = None,
        endpoint_access: eks.EndpointAccess = eks.EndpointAccess.PUBLIC_AND_PRIVATE,
        node_groups: Optional[List[EKSNodeGroupConfig]] = [],
        security_group: Optional[ec2.SecurityGroup] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.cluster_name = cluster_name
        self.vpc = vpc
        self.version = version or "1.31" 
        self.endpoint_access = endpoint_access
        self.node_groups = node_groups or []
        self.security_group = security_group
        self.tags = tags or {}
        self.version = eks.KubernetesVersion.of(self.version)


class EKSBlueprint():
    def __init__(self, eks_configs: List[EKSConfig] = []):
        self.eks_configs = eks_configs
    
    def add_config(self, eks_config: EKSConfig):
        self.eks_configs.append(eks_config)
    
    @property
    def all_configs(self) -> Generator[EKSConfig, None, None]:
        for config in self.eks_configs:
            yield config

class EKSData:
    """
    Stores the created EKS Cluster for easy access.

    Attributes:
        cluster (eks.Cluster): The created EKS cluster.
    """

    def __init__(self, cluster: eks.Cluster):
        self.cluster = cluster


class EKSResources:
    """
    Manages created EKS resources.

    Attributes:
        _resources (dict): A dictionary of created EKS clusters, indexed by cluster names.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, eks_data: EKSData):
        """
        Adds an EKS cluster to resources.

        Args:
            name (str): Name of the EKS cluster.
            eks_data (EKSData): The EKS cluster data instance.
        """
        self._resources[name] = eks_data

    def get_cluster(self, name: str) -> eks.Cluster:
        """
        Retrieves an EKS cluster by name.

        Args:
            name (str): The name of the EKS cluster.

        Returns:
            eks.Cluster: The associated EKS cluster.
        """
        return self._resources[name].cluster


class EKSUtility:
    """
    Utility for creating and managing EKS clusters based on configurations.

    Attributes:
        resources (EKSResources): Manages created EKS clusters by name.
    """

    def __init__(self, scope: Construct, eks_blueprint: EKSBlueprint):
        """
        Initializes the EKSUtility and creates EKS clusters based on provided configurations.

        Args:
            scope (Construct): The scope to define the EKS clusters.
            eks_blueprint (EKSBlueprint): The blueprint defining the EKS clusters to create.
        """
        self.resources = EKSResources()
        aws_account_id = os.getenv("AWS_ACCOUNT_ID")
        for config in eks_blueprint.all_configs:
            # Create the EKS cluster
            cluster_role_obj = IamUtility(scope, IamBlueprint([IamConfig(f"{config.cluster_name}ClusterRole", service="eks", managed_policies=["AmazonEKSClusterPolicy"])]))
            cluster_role = cluster_role_obj.resources.get_role(f"{config.cluster_name}ClusterRole").role
            eks_cluster = eks.Cluster(
                scope,
                config.cluster_name,
                cluster_name=config.cluster_name,
                vpc=config.vpc,
                version=config.version,
                authentication_mode=eks.AuthenticationMode.API_AND_CONFIG_MAP,
                endpoint_access=config.endpoint_access,
                default_capacity=0,  # Disable default node group
                role=cluster_role,
                cluster_logging=[eks.ClusterLoggingTypes.API, eks.ClusterLoggingTypes.AUDIT, eks.ClusterLoggingTypes.AUTHENTICATOR],
                security_group=config.security_group,
            )

            # Add node groups if specified
            iam_config = IamConfig(f"{config.cluster_name}NodeRole", service="ec2", managed_policies=["AmazonEC2ContainerRegistryReadOnly", "AmazonEKSWorkerNodePolicy", "AmazonEKS_CNI_Policy", "AmazonSSMManagedInstanceCore"])
            iam_blueprint = IamBlueprint([iam_config])

            if len(config.node_groups) > 0:
                node_role_obj = IamUtility(scope, iam_blueprint)
                default_node_role = node_role_obj.resources.get_role(f"{config.cluster_name}NodeRole").role
            
            node_group = None
            for ng_config in config.node_groups:
                node_role = ng_config.node_role
                if not node_role:
                    node_role = default_node_role

                node_group = eks_cluster.add_nodegroup_capacity(
                    ng_config.nodegroup_name,
                    nodegroup_name=ng_config.nodegroup_name,
                    instance_types=ng_config.instance_types,
                    min_size=ng_config.min_size,
                    max_size=ng_config.max_size,
                    desired_size=ng_config.desired_size,
                    node_role=node_role,
                    disk_size=ng_config.disk_size,
                    ami_type=ng_config.ami_type,
                    subnets=ng_config.subnets,
                )

            if node_group:
                eks.AlbController(scope, f"{config.cluster_name}AlbController", cluster=eks_cluster, version=eks.AlbControllerVersion.V2_8_2).node.add_dependency(node_group)

            # Add CodeBuild access to the cluster
            eks.AccessEntry(
                scope,
                f"{config.cluster_name}CodeBuildAccessEntry",
                access_entry_name=f"{config.cluster_name}CodeBuildAccessEntry",
                cluster=eks_cluster,
                principal=f"arn:aws:iam::{aws_account_id}:role/CodeBuildDeploymentRole",
                access_policies=[
                    eks.AccessPolicy.from_access_policy_name("AmazonEKSClusterAdminPolicy", access_scope_type=eks.AccessScopeType.CLUSTER),
                    eks.AccessPolicy.from_access_policy_name("AmazonEKSAdminPolicy", access_scope_type=eks.AccessScopeType.CLUSTER),
                ]
                )
            
            # Attach tags to the cluster
            for key, value in config.tags.items():
                Tags.of(eks_cluster).add(key, value)


            
            eks.Addon(
                scope,
                "eks-pod-identity-agent",
                addon_name="eks-pod-identity-agent",
                cluster=eks_cluster
            )
            eks.Addon(
                scope,
                "vpc-cni",
                addon_name="vpc-cni",
                cluster=eks_cluster
            )
            eks.Addon(
                scope,
                "coredns",
                cluster=eks_cluster,
                addon_name="coredns"
            )
            eks.Addon(
                scope,
                "kube-proxy",
                addon_name="kube-proxy",
                cluster=eks_cluster
            )

            # Store the cluster in resources for access
            self.resources.add_resource(config.cluster_name, EKSData(eks_cluster))
