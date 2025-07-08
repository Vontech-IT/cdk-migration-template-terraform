from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    Duration
)
from constructs import Construct
from typing import Optional, List, Dict, Union


class EventPatternConfig:
    """
    Configuration for EventBridge event patterns.
    
    Attributes:
        source (Optional[List[str]]): List of event sources.
        detail_type (Optional[List[str]]): List of event detail types.
        detail (Optional[Dict]): Event detail pattern.
        account (Optional[List[str]]): List of account IDs.
        region (Optional[List[str]]): List of regions.
        time (Optional[List[str]]): List of time patterns.
        version (Optional[List[str]]): List of version patterns.
        id (Optional[List[str]]): List of event IDs.
        resources (Optional[List[str]]): List of resource patterns.
        detail_type (Optional[List[str]]): List of detail type patterns.
    """

    def __init__(
        self,
        source: Optional[List[str]] = None,
        detail_type: Optional[List[str]] = None,
        detail: Optional[Dict] = None,
        account: Optional[List[str]] = None,
        region: Optional[List[str]] = None,
        time: Optional[List[str]] = None,
        version: Optional[List[str]] = None,
        id: Optional[List[str]] = None,
        resources: Optional[List[str]] = None
    ):
        self.source = source
        self.detail_type = detail_type
        self.detail = detail
        self.account = account
        self.region = region
        self.time = time
        self.version = version
        self.id = id
        self.resources = resources

    def to_event_pattern(self) -> events.EventPattern:
        """
        Converts the configuration to an EventBridge EventPattern.
        
        Returns:
            events.EventPattern: The EventBridge event pattern.
        """
        return events.EventPattern(
            source=self.source,
            detail_type=self.detail_type,
            detail=self.detail,
            account=self.account,
            region=self.region,
            time=self.time,
            version=self.version,
            id=self.id,
            resources=self.resources
        )


class EventRuleConfig:
    """
    Configuration class for EventBridge rule.
    
    Attributes:
        rule_name (str): Name of the EventBridge rule.
        description (Optional[str]): Description of the rule.
        event_pattern_config (EventPatternConfig): Event pattern configuration.
        schedule (Optional[Union[events.Schedule, str]]): Schedule expression for the rule.
        enabled (bool): Whether the rule is enabled.
        targets (Optional[List[targets.Target]]): List of targets for the rule.
    """

    def __init__(
        self,
        rule_name: str,
        event_bus: Optional[events.EventBus] = None,
        description: Optional[str] = None,
        event_pattern_config: EventPatternConfig = None,
        schedule: Optional[Union[events.Schedule, str]] = None,
        enabled: bool = True,
        targets: Optional[List[events.IRuleTarget]] = None
    ):
        self.rule_name = rule_name
        self.event_bus = event_bus
        self.description = description
        self.event_pattern_config = event_pattern_config
        self.schedule = schedule
        self.enabled = enabled
        self.targets = targets


class EventBridgeData:
    """
    Stores references to created EventBridge rule.
    
    Attributes:
        rule (events.Rule): The created EventBridge rule.
    """

    def __init__(self, rule: events.Rule):
        self.rule = rule


class EventBridgeResources:
    """
    Manages the resources for EventBridge rules.
    
    Attributes:
        _resources (Dict[str, EventBridgeData]): A dictionary mapping rule names to EventBridgeData instances.
    """

    def __init__(self):
        self._resources = {}

    def add_resource(self, name: str, rule_data: EventBridgeData):
        """
        Adds an EventBridge rule to the resources.
        
        Args:
            name (str): The name of the EventBridge rule.
            rule_data (EventBridgeData): The EventBridge data containing the rule.
        """
        self._resources[name] = rule_data

    def get_rule(self, name: str) -> events.Rule:
        """
        Retrieves an EventBridge rule by name.
        
        Args:
            name (str): The name of the EventBridge rule.
            
        Returns:
            events.Rule: The associated EventBridge rule.
        """
        return self._resources[name].rule


class EventBridgeBlueprint:
    """
    Blueprint for creating multiple EventBridge rules based on predefined configurations.
    
    Attributes:
        rule_configs (List[EventRuleConfig]): A list of EventBridge rule configurations.
    """

    def __init__(self, rule_configs: List[EventRuleConfig] = []):
        """
        Initializes an EventBridgeBlueprint instance.
        
        Args:
            rule_configs (List[EventRuleConfig], optional): List of EventBridge rule configurations. Defaults to an empty list.
        """
        self.rule_configs = rule_configs

    def add_config(self, rule_config: EventRuleConfig):
        """
        Adds a new EventBridge rule configuration to the blueprint.
        
        Args:
            rule_config (EventRuleConfig): The EventBridge rule configuration to add.
        """
        self.rule_configs.append(rule_config)

    @property
    def all_configs(self) -> List[EventRuleConfig]:
        return self.rule_configs


class EventBridgeUtility:
    """
    Utility class for creating and managing EventBridge rules based on EventRuleConfig.
    
    Attributes:
        rules (dict): A dictionary of EventBridge rules created by name.
    """

    def __init__(self, scope: Construct, rule_configs: EventBridgeBlueprint):
        self.resources = EventBridgeResources()
        for config in rule_configs.all_configs:
            # Create event bus
            event_bus = config.event_bus
            
            # Create the EventBridge rule
            rule = events.Rule(
                scope,
                config.rule_name,
                rule_name=config.rule_name,
                event_bus=event_bus,
                description=config.description,
                event_pattern=config.event_pattern_config.to_event_pattern() if config.event_pattern_config else None,
                schedule=config.schedule if isinstance(config.schedule, events.Schedule) else events.Schedule.expression(config.schedule) if config.schedule else None,
                enabled=config.enabled
            )

            # Add targets if specified
            if config.targets:
                for target in config.targets:
                    rule.add_target(target)

            # Store the rule in resources
            self.resources.add_resource(config.rule_name, EventBridgeData(rule))
