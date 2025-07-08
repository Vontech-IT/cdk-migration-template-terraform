# modules/iot/iot_topic_rule_utility.py
from constructs import Construct
from imports.aws.iot_topic_rule import IotTopicRule, IotTopicRuleErrorAction, IotTopicRuleSqs

class IotTopicRuleModule(Construct):
    """
    A reusable module for creating an AWS IoT Topic Rule.
    This example is configured to send messages to an SQS queue.
    """
    def __init__(self, scope: Construct, id: str, *,
                 rule_name: str,
                 sql: str,
                 sql_version: str = "2016-03-23",
                 enabled: bool = True,
                 sqs_queue_url: str,
                 sqs_role_arn: str,
                 tags: dict = None):
        """
        Args:
            rule_name (str): The name of the topic rule.
            sql (str): The SQL statement used to select data from a topic (e.g., "SELECT * FROM 'iot/topic'").
            sql_version (str, optional): The SQL version. Defaults to "2016-03-23".
            enabled (bool, optional): Whether the rule is enabled. Defaults to True.
            sqs_queue_url (str): The URL of the SQS queue for the action.
            sqs_role_arn (str): The ARN of the IAM role that grants access to the SQS queue.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.topic_rule = IotTopicRule(self, "IotTopicRule",
            name=rule_name,
            sql=sql,
            sql_version=sql_version,
            enabled=enabled,
            sqs=[
                IotTopicRuleSqs(
                    queue_url=sqs_queue_url,
                    role_arn=sqs_role_arn
                )
            ],
            tags={"Name": rule_name, **(tags or {})}
        )

        self.arn = self.topic_rule.arn
