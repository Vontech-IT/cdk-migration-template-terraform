# modules/rds/rds_utility.py
from constructs import Construct
from imports.aws.db_subnet_group import DbSubnetGroup
from imports.aws.db_instance import DbInstance

class RdsModule(Construct):
    """
    A reusable module for creating an AWS RDS Database instance.
    """
    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 vpc_id: str,
                 subnet_ids: list[str],
                 security_group_ids: list[str],
                 allocated_storage: int,
                 engine: str,
                 engine_version: str,
                 instance_class: str,
                 db_name: str,
                 username: str,
                 password: str, # In a real project, use Secrets Manager
                 tags: dict = None):
        """
        Args:
            name (str): A name for the RDS resources.
            vpc_id (str): The ID of the VPC.
            subnet_ids (list[str]): A list of private subnet IDs for the database.
            security_group_ids (list[str]): Security groups for the database.
            allocated_storage (int): The allocated storage in GB.
            engine (str): The database engine (e.g., 'mysql', 'postgres').
            engine_version (str): The engine version.
            instance_class (str): The instance class (e.g., 'db.t3.micro').
            db_name (str): The name of the initial database.
            username (str): The master username.
            password (str): The master password.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.subnet_group = DbSubnetGroup(self, "DbSubnetGroup",
            name=f"{name}-sng",
            subnet_ids=subnet_ids,
            tags={"Name": f"{name}-sng", **(tags or {})}
        )

        self.db_instance = DbInstance(self, "DbInstance",
            identifier=name,
            allocated_storage=allocated_storage,
            engine=engine,
            engine_version=engine_version,
            instance_class=instance_class,
            db_name=db_name,
            username=username,
            password=password,
            db_subnet_group_name=self.subnet_group.name,
            vpc_security_group_ids=security_group_ids,
            skip_final_snapshot=True,
            tags={"Name": name, **(tags or {})}
        )

        self.address = self.db_instance.address
        self.port = self.db_instance.port
