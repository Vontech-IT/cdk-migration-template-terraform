# modules/sns/sns_utility.py
from constructs import Construct
from imports.aws.sns_topic import SnsTopic

class SnsModule(Construct):
    """
    A reusable module for creating an AWS SNS topic.
    """
    def __init__(self, scope: Construct, id: str, *,
                 topic_name: str,
                 fifo_topic: bool = False,
                 tags: dict = None):
        """
        Args:
            topic_name (str): The name for the SNS topic.
            fifo_topic (bool, optional): Whether to create a FIFO topic. Defaults to False.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        # FIFO topic names must end with .fifo
        if fifo_topic and not topic_name.endswith(".fifo"):
            topic_name += ".fifo"

        self.topic = SnsTopic(self, "SnsTopic",
            name=topic_name,
            fifo_topic=fifo_topic,
            tags={"Name": topic_name, **(tags or {})}
        )

        self.arn = self.topic.arn
