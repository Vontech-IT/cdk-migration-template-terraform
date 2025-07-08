# modules/sagemaker/sagemaker_utility.py
from constructs import Construct
from imports.aws.sagemaker_notebook_instance import SagemakerNotebookInstance

class SageMakerNotebookModule(Construct):
    """
    A reusable module for creating an AWS SageMaker Notebook Instance.
    """
    def __init__(self, scope: Construct, id: str, *,
                 instance_name: str,
                 instance_type: str,
                 role_arn: str,
                 tags: dict = None):
        """
        Args:
            instance_name (str): The name of the notebook instance.
            instance_type (str): The type of the instance (e.g., 'ml.t2.medium').
            role_arn (str): The ARN of the IAM role for the notebook.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.notebook_instance = SagemakerNotebookInstance(self, "SageMakerNotebook",
            name=instance_name,
            instance_type=instance_type,
            role_arn=role_arn,
            tags={"Name": instance_name, **(tags or {})}
        )

        self.arn = self.notebook_instance.arn
        self.name = self.notebook_instance.name
