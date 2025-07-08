# modules/alb/alb_utility.py
from constructs import Construct
from imports.aws.lb import Lb
from imports.aws.lb_target_group import LbTargetGroup
from imports.aws.lb_listener import LbListener, LbListenerDefaultAction

class AlbModule(Construct):
    """
    A reusable module for creating an Application Load Balancer (ALB),
    Target Group, and Listener.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 vpc_id: str,
                 subnet_ids: list[str],
                 security_group_ids: list[str],
                 health_check_path: str = "/",
                 tags: dict = None):
        """
        Args:
            name (str): A name prefix for the ALB resources.
            vpc_id (str): The ID of the VPC.
            subnet_ids (list[str]): A list of public subnet IDs for the ALB.
            security_group_ids (list[str]): A list of security group IDs for the ALB.
            health_check_path (str, optional): The path for the health check. Defaults to "/".
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.alb = Lb(self, "Alb",
            name=name,
            internal=False,
            load_balancer_type="application",
            security_groups=security_group_ids,
            subnets=subnet_ids,
            tags={"Name": name, **(tags or {})}
        )

        self.target_group = LbTargetGroup(self, "TargetGroup",
            name=f"{name}-tg",
            port=80,
            protocol="HTTP",
            vpc_id=vpc_id,
            target_type="instance",
            health_check={
                "path": health_check_path,
                "protocol": "HTTP"
            },
            tags={"Name": f"{name}-tg", **(tags or {})}
        )

        self.listener = LbListener(self, "Listener",
            load_balancer_arn=self.alb.arn,
            port=80,
            protocol="HTTP",
            default_action=[
                LbListenerDefaultAction(
                    type="forward",
                    target_group_arn=self.target_group.arn
                )
            ]
        )

        self.dns_name = self.alb.dns_name
        self.target_group_arn = self.target_group.arn
