from aws_cdk import aws_ssm as ssm, SecretValue


def get_ssm_parameter_secure_string(parameter_name, version=None):
    return SecretValue.ssm_secure(parameter_name, version).to_string()
