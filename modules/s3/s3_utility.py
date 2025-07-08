from constructs import Construct
from imports.aws.s3_bucket import S3Bucket
from imports.aws.s3_bucket_public_access_block import S3BucketPublicAccessBlock
from imports.aws.s3_bucket_versioning import S3BucketVersioningA

class S3Module(Construct):
    def __init__(self, scope: Construct, id: str, *, bucket_name: str, versioned: bool = False, tags: dict = None):
        super().__init__(scope, id)

        self.bucket = S3Bucket(self, "Bucket",
            bucket=bucket_name,
            tags={"Name": bucket_name, **(tags or {})}
        )

        S3BucketPublicAccessBlock(self, "PublicAccessBlock",
            bucket=self.bucket.id,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True,
            restrict_public_buckets=True
        )

        if versioned:
            S3BucketVersioningA(self, "Versioning",
                bucket=self.bucket.id,
                versioning_configuration={"status": "Enabled"}
            )