import os
from modules.builder import StackBuilder
import aws_cdk as cdk

env = cdk.Environment(account=os.getenv("AWS_ACCOUNT_ID"), region=os.getenv("AWS_REGION"))
app = cdk.App()

builder = StackBuilder(app, "<STACK_NAME>", env=env)
