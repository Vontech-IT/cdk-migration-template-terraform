# modules/comprehend/comprehend_utility.py
from constructs import Construct
from imports.aws.comprehend_document_classifier import ComprehendDocumentClassifier, ComprehendDocumentClassifierInputDataConfig

class ComprehendClassifierModule(Construct):
    """
    A reusable module for creating an Amazon Comprehend Document Classifier.
    """
    def __init__(self, scope: Construct, id: str, *,
                 classifier_name: str,
                 data_access_role_arn: str,
                 input_data_s3_uri: str,
                 language_code: str = "en",
                 mode: str = "MULTI_CLASS",
                 tags: dict = None):
        """
        Args:
            classifier_name (str): The name of the document classifier.
            data_access_role_arn (str): IAM role with permissions to access S3 data.
            input_data_s3_uri (str): S3 URI for the training data.
            language_code (str, optional): Language of the documents. Defaults to "en".
            mode (str, optional): 'MULTI_CLASS' or 'MULTI_LABEL'. Defaults to "MULTI_CLASS".
            tags (dict, optional): Additional tags for the resources.
        """
        super().__init__(scope, id)

        self.classifier = ComprehendDocumentClassifier(self, "DocumentClassifier",
            name=classifier_name,
            data_access_role_arn=data_access_role_arn,
            input_data_config=ComprehendDocumentClassifierInputDataConfig(
                s3_uri=input_data_s3_uri
            ),
            language_code=language_code,
            mode=mode,
            tags={"Name": classifier_name, **(tags or {})}
        )

        self.arn = self.classifier.arn
