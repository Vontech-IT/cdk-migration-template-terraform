# modules/ecr/ecr_utility.py
from constructs import Construct
from imports.aws.ecr_repository import EcrRepository

class EcrModule(Construct):
    """
    A reusable module for creating an AWS ECR repository.
    """
    def __init__(self, scope: Construct, id: str, *,
                 repository_name: str,
                 image_tag_mutability: str = "MUTABLE",
                 tags: dict = None):
        """
        Args:
            repository_name (str): The name for the ECR repository.
            image_tag_mutability (str, optional): 'MUTABLE' or 'IMMUTABLE'. Defaults to "MUTABLE".
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.repository = EcrRepository(self, "EcrRepository",
            name=repository_name,
            image_tag_mutability=image_tag_mutability,
            tags={"Name": repository_name, **(tags or {})}
        )

        self.repository_url = self.repository.repository_url
        self.repository_arn = self.repository.arn
