# modules/security_group/sg_utility.py
from constructs import Construct
from imports.aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress

class SecurityGroupModule(Construct):
    """
    A reusable module for creating an AWS Security Group.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 vpc_id: str,
                 ingress_rules: list[dict],
                 egress_rules: list[dict],
                 tags: dict = None):
        """
        Args:
            name (str): The name for the security group.
            vpc_id (str): The ID of the VPC where the security group will be created.
            ingress_rules (list[dict]): A list of ingress rule dictionaries.
                Example: [{'from_port': 80, 'to_port': 80, 'protocol': 'tcp', 'cidr_blocks': ['0.0.0.0/0']}]
            egress_rules (list[dict]): A list of egress rule dictionaries.
                Example: [{'from_port': 0, 'to_port': 0, 'protocol': '-1', 'cidr_blocks': ['0.0.0.0/0']}]
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.sg = SecurityGroup(self, "SecurityGroup",
            name=name,
            vpc_id=vpc_id,
            ingress=[SecurityGroupIngress(**rule) for rule in ingress_rules],
            egress=[SecurityGroupEgress(**rule) for rule in egress_rules],
            tags={"Name": name, **(tags or {})}
        )

        self.id = self.sg.id
