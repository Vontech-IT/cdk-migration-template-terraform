import aws_cdk as cdk
from constructs import Construct
from aws_cdk import Stack, CfnOutput, aws_ec2 as ec2

# from modules.vpc.vpc_utility import VPCResources, VPCUtility
from modules.rds.rds_utility import  RDSUtility, RDSResources, RDSBlueprint
from modules.aws_lambda.lambda_utility import LambdaResources, LambdaUtility, LambdaBlueprint
from modules.ecs.fargate.fargate_utility import EcsFargateResources, EcsFargateUtility
from modules.iam_role.iam_utility import IamResources, IamUtility, IamBlueprint
from modules.s3.s3_utility import S3Resources, S3Utility, S3Blueprint
from modules.ec2_asg.asg_utility import  ASGUtility, ASGBlueprint, ASGResources
from modules.vpc.vpc_utility import  VPCUtility, VPCResources, VPCBlueprint
from modules.security_group.sg_utility import SecurityGroupUtility, SecurityGroupBlueprint, SecurityGroupResources
from modules.eks.eks_utility import EKSResources, EKSUtility, EKSBlueprint
from modules.ecr.ecr_utility import ECRBlueprint, ECRUtility, ECRResources
from modules.amazon_mq.mq_utility import AmazonMQUtility, AmazonMQResources, AmazonMQBlueprint
from modules.api_gateway.api_gateway_utility import ApiGatewayUtility, ApiGatewayResources,  ApiGatewayBlueprint
from modules.alb.alb_utility import ALBBlueprint, ALBResources, ALBUtility
from modules.codebuild.codebuild_utility import CodeBuildBlueprint, CodeBuildResources, CodeBuildUtility
from modules.eventbridge.eventbridge_utility import EventBridgeBlueprint, EventBridgeResources, EventBridgeUtility
from modules.dynamodb.dynamodb_utility import DynamoDBBlueprint, DynamoDBResources, DynamoDBUtility
from modules.vpn.vpn_utility import VPNUtility, VPNResources, VPNBlueprint
from modules.ec2_instance.instance_utility import InstanceUtility, InstanceResources, InstanceBlueprint
from modules.cloudfront.cloudfront_utility import CloudFrontBlueprint, CloudFrontResources, CloudFrontUtility
from modules.nlb.nlb_utility import NLBBlueprint, NLBResources, NLBUtility


class StackBuilder(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
    def add_vpc(self, vpc_blueprint: VPCBlueprint) -> VPCResources:
        vpc_utility = VPCUtility(self, vpc_blueprint)
        return vpc_utility.resources
    
    def add_security_group(self, sg_blueprint: SecurityGroupBlueprint) -> SecurityGroupResources:
        sg_utility = SecurityGroupUtility(self, sg_blueprint)
        return sg_utility.resources

    def add_iam(self, iam_blueprint: IamBlueprint) -> IamResources:
        iam_utility = IamUtility(self, iam_blueprint)
        return iam_utility.resources

    def add_mq(self, mq_blueprint: AmazonMQBlueprint) -> AmazonMQResources:
        mq_utility = AmazonMQUtility(self, mq_blueprint)
        return mq_utility.resources

    def add_s3(self, s3blueprint: S3Blueprint) -> S3Resources:
        s3_utility = S3Utility(self, s3blueprint.all_configs)
        return s3_utility.resources
    
    def add_asg(self, asg_blueprint: ASGBlueprint) -> ASGResources:
        asg_utility = ASGUtility(self, asg_blueprint)
        return asg_utility.resources
    
    def add_eks(self, eks_blueprint: EKSBlueprint) -> EKSResources:
        eks_utility = EKSUtility(self, eks_blueprint)
        return eks_utility.resources
    
    def add_rds(self, rds_blueprint: RDSBlueprint) -> RDSResources:
        rds_utility = RDSUtility(self, rds_blueprint)
        return rds_utility.resources
    
    def add_ecr(self, ecr_blueprint: ECRBlueprint) -> ECRResources:
        ecr_utility = ECRUtility(self, ecr_blueprint)
        return ecr_utility.resources
    
    def add_lambda(self, lambda_bleuprint: LambdaBlueprint) -> LambdaResources:
        lambda_utility = LambdaUtility(self, lambda_bleuprint)
        return lambda_utility.resources
    
    def add_ecs_fargate(self, ecs_configs: list[dict]) -> EcsFargateResources:
        ecs_fargate_utility = EcsFargateUtility(self, ecs_configs)
        return ecs_fargate_utility.resources

    def add_api_gateway(self, api_blueprint: ApiGatewayBlueprint) -> ApiGatewayResources:
        api_gateway_utility = ApiGatewayUtility(self, api_blueprint)
        return api_gateway_utility.resources

    def add_alb(self, alb_blueprint: ALBBlueprint) -> ALBResources:
        """
        Creates Application Load Balancers based on the provided blueprint.

        Args:
            alb_blueprint (ALBBlueprint): The blueprint containing ALB configurations.

        Returns:
            ALBResources: Resources containing the created ALBs and their listeners.
        """
        alb_utility = ALBUtility(self, alb_blueprint)
        return alb_utility.resources

    def add_codebuild(self, codebuild_blueprint: CodeBuildBlueprint) -> CodeBuildResources:
        codebuild_utility = CodeBuildUtility(self, codebuild_blueprint)
        return codebuild_utility.resources

    def add_eventbridge(self, eventbridge_blueprint: EventBridgeBlueprint) -> EventBridgeResources:
        eventbridge_utility = EventBridgeUtility(self, eventbridge_blueprint)
        return eventbridge_utility.resources

    def add_dynamodb(self, dynamodb_blueprint: DynamoDBBlueprint) -> DynamoDBResources:
        dynamodb_utility = DynamoDBUtility(self, dynamodb_blueprint)
        return dynamodb_utility.resources

    def add_vpn(self, vpn_blueprint: VPNBlueprint) -> VPNResources:
        vpn_utility = VPNUtility(self, vpn_blueprint)
        return vpn_utility.resources
    
    def add_instance(self, ec2_blueprint: InstanceBlueprint) -> InstanceResources:
        ec2_utility = InstanceUtility(self, ec2_blueprint)
        return ec2_utility.resources

    def add_cloudfront(self, cloudfront_blueprint: CloudFrontBlueprint) -> CloudFrontResources:
        cloudfront_utility = CloudFrontUtility(self, cloudfront_blueprint)
        return cloudfront_utility.resources
    
    def add_nlb(self, nlb_blueprint: NLBUtility) -> NLBResources:
        nlb_utility = NLBUtility(self, nlb_blueprint)
        return nlb_utility.resources