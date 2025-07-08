from constructs import Construct
from imports.aws.vpc import Vpc
from imports.aws.subnet import Subnet
from imports.aws.internet_gateway import InternetGateway
from imports.aws.route_table import RouteTable, RouteTableRoute
from imports.aws.route_table_association import RouteTableAssociation

class VpcModule(Construct):
    def __init__(self, scope: Construct, id: str, *, name: str, cidr_block: str, public_subnet_cidrs: list, private_subnet_cidrs: list, tags: dict = None):
        super().__init__(scope, id)

        self.vpc = Vpc(self, "Vpc",
            cidr_block=cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={"Name": name, **(tags or {})}
        )

        self.igw = InternetGateway(self, "InternetGateway",
            vpc_id=self.vpc.id,
            tags={"Name": f"{name}-igw", **(tags or {})}
        )

        self.public_route_table = RouteTable(self, "PublicRouteTable",
            vpc_id=self.vpc.id,
            route=[
                RouteTableRoute(
                    cidr_block="0.0.0.0/0",
                    gateway_id=self.igw.id
                )
            ],
            tags={"Name": f"{name}-public-rt", **(tags or {})}
        )

        self.public_subnets = []
        for i, cidr in enumerate(public_subnet_cidrs):
            subnet = Subnet(self, f"PublicSubnet{i}",
                vpc_id=self.vpc.id,
                cidr_block=cidr,
                map_public_ip_on_launch=True,
                availability_zone=f"us-east-1{chr(97+i)}", # Simple AZ rotation
                tags={"Name": f"{name}-public-subnet-{i}", **(tags or {})}
            )
            RouteTableAssociation(self, f"PublicSubnet{i}RouteTableAssociation",
                subnet_id=subnet.id,
                route_table_id=self.public_route_table.id
            )
            self.public_subnets.append(subnet)

        self.private_subnets = []
        for i, cidr in enumerate(private_subnet_cidrs):
            subnet = Subnet(self, f"PrivateSubnet{i}",
                vpc_id=self.vpc.id,
                cidr_block=cidr,
                availability_zone=f"us-east-1{chr(97+i)}", # Simple AZ rotation
                tags={"Name": f"{name}-private-subnet-{i}", **(tags or {})}
            )
            self.private_subnets.append(subnet)