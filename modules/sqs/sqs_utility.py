# modules/sqs/sqs_utility.py
from constructs import Construct
from imports.aws.sqs_queue import SqsQueue

class SqsModule(Construct):
    """
    A reusable module for creating an AWS SQS queue.
    """
    def __init__(self, scope: Construct, id: str, *,
                 queue_name: str,
                 fifo_queue: bool = False,
                 visibility_timeout_seconds: int = 30,
                 tags: dict = None):
        """
        Args:
            queue_name (str): The name for the SQS queue.
            fifo_queue (bool, optional): Whether to create a FIFO queue. Defaults to False.
            visibility_timeout_seconds (int, optional): The visibility timeout. Defaults to 30.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        # FIFO queue names must end with .fifo
        if fifo_queue and not queue_name.endswith(".fifo"):
            queue_name += ".fifo"

        self.queue = SqsQueue(self, "SqsQueue",
            name=queue_name,
            fifo_queue=fifo_queue,
            visibility_timeout_seconds=visibility_timeout_seconds,
            tags={"Name": queue_name, **(tags or {})}
        )

        self.arn = self.queue.arn
        self.id = self.queue.id
