# modules/iot/iot_utility.py
from constructs import Construct
from imports.aws.iot_thing import IotThing

class IotThingModule(Construct):
    """
    A reusable module for creating an AWS IoT Thing.
    """
    def __init__(self, scope: Construct, id: str, *,
                 thing_name: str,
                 attributes: dict = None,
                 tags: dict = None):
        """
        Args:
            thing_name (str): The name of the IoT Thing.
            attributes (dict, optional): Key-value attributes for the thing.
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.thing = IotThing(self, "IotThing",
            name=thing_name,
            attributes=attributes,
            tags={"Name": thing_name, **(tags or {})}
        )

        self.arn = self.thing.arn
        self.name = self.thing.name
