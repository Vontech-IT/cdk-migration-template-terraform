# modules/iam_role/iam_utility.py
from constructs import Construct
import json
from imports.aws.iam_role import IamRole
from imports.aws.iam_policy_attachment import IamPolicyAttachment

class IamRoleModule(Construct):
    """
    A reusable module for creating an AWS IAM Role with an assume role policy
    and attaching managed policies.
    """
    def __init__(self, scope: Construct, id: str, *,
                 role_name: str,
                 assume_role_policy_service: str,
                 managed_policy_arns: list[str] = None,
                 tags: dict = None):
        """
        Args:
            role_name (str): The name for the IAM role.
            assume_role_policy_service (str): The AWS service principal that can assume this role (e.g., 'ec2.amazonaws.com').
            managed_policy_arns (list[str], optional): A list of ARNs for managed policies to attach.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": assume_role_policy_service},
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        self.role = IamRole(self, "IamRole",
            name=role_name,
            assume_role_policy=json.dumps(assume_role_policy),
            tags={"Name": role_name, **(tags or {})}
        )

        if managed_policy_arns:
            for i, policy_arn in enumerate(managed_policy_arns):
                IamPolicyAttachment(self, f"PolicyAttachment{i}",
                    role=self.role.name,
                    policy_arn=policy_arn
                )

        self.arn = self.role.arn
        self.name = self.role.name
