from constructs import Construct
from imports.aws.instance import Instance

class EC2InstanceModule(Construct):
    def __init__(self, scope: Construct, id: str, *,
                 instance_name: str,
                 ami: str,
                 instance_type: str,
                 subnet_id: str,
                 key_name: str = None,
                 tags: dict = None):
        super().__init__(scope, id)

        self.instance = Instance(self, "Instance",
            ami=ami,
            instance_type=instance_type,
            subnet_id=subnet_id,
            key_name=key_name,
            tags={"Name": instance_name, **(tags or {})}
        )