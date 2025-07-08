# Amplify Stack Template - AWS CDK

This AWS CDK stack deploys an AWS Amplify application using configurations provided as parameters. It creates an Amplify application along with a corresponding branch and IAM service role for managing resources.

## Table of Contents

1. [Pre-requisites](#pre-requisites)
2. [Parameters](#parameters)
3. [Stack Components](#stack-components)
4. [How to Use](#how-to-use)
5. [Outputs](#outputs)

---

## Pre-requisites

1. **AWS CDK**: Make sure you have AWS CDK installed. You can install it by running:
   ```bash
   npm install -g aws-cdk
   ```

2. **AWS Credentials**: Ensure that your AWS credentials are set up and configured correctly.

3. **IAM Permissions**: The user deploying this stack should have sufficient IAM permissions to create roles, Amplify applications, and manage related resources like S3, Lambda, CloudFront, DynamoDB, and IAM.

---

## Parameters

The stack accepts the following parameters in the `amplify_configs` list passed during initialization:

| Parameter        | Description                                                                 | Required | Default Value |
|------------------|-----------------------------------------------------------------------------|----------|---------------|
| `app_name`       | The name of the Amplify app to be created.                                  | Yes      | N/A           |
| `github_repo`    | The GitHub repository URL where the application source code is located.     | Yes      | N/A           |
| `access_token`   | The access token for accessing the GitHub repository.                       | Yes if 'oauth_token' is not provided | N/A           |
| `oauth_token`    | The OAuth token for accessing the GitHub repository.                        | Yes if 'access_token' is not provided | N/A           |
| `branch_name`    | The branch name to deploy from the GitHub repository.                       | No       | `main`        |
| `build_spec`     | The Amplify build specification for the application (YAML format).          | No       | Default build spec (shown below) |
| `envs`           | A list of environment variables to be passed to the Amplify app.            | No       | Empty List    |

### Default `build_spec`

The following is the default build specification if none is provided:

```yaml
version: 1
frontend:
    phases:
        preBuild:
            commands:
                - npm install
        build:
            commands:
                - npm run build
    artifacts:
        baseDirectory: build
        files:
            - '**/*'
    cache:
        paths:
            - node_modules/**/*
```

---

## Stack Components

The stack creates the following resources:

1. **IAM Role**: An IAM role that allows Amplify to access and manage AWS resources (e.g., S3, Lambda, CloudFront, DynamoDB).
   
2. **Amplify App**: An AWS Amplify app that is connected to a GitHub repository and configured with environment variables and a build specification.

3. **Amplify Branch**: A branch for the Amplify app that is automatically built and deployed whenever code is pushed to the corresponding GitHub branch.

4. **CDK Outputs**: The Amplify App ID and branch URL are output for easy access.

---

## How to Use

1. **Clone the Repository**:
   Clone this repository and navigate to the directory:
   ```bash
   git clone <your-repo-url>
   cd <repo-directory>
   ```

2. **Install Dependencies**:
   Install the necessary dependencies for the CDK project:
   ```bash
   npm install
   ```

3. **Configure Your App**:
   Modify the `amplify_configs` list in the CDK stack file to include the appropriate configuration for your Amplify app(s). Example configuration:
   ```python
   amplify_configs = [
       {
           "app_name": "MyAmplifyApp",
           "github_repo": "https://github.com/my-user/my-repo",
           "oauth_token": "my-github-oauth-token",
           "branch_name": "main",
           "envs": [
               {"key": "REACT_APP_API_URL", "value": "https://api.example.com"},
               {"key": "NODE_ENV", "value": "production"}
           ]
       }
   ]
   ```

4. **Deploy the Stack**:
   Run the following command to deploy the stack:
   ```bash
   cdk deploy
   ```

---

## Outputs

After deploying the stack, the following outputs will be available:

| Output            | Description                                      |
|-------------------|--------------------------------------------------|
| **App ID**        | The ID of the Amplify app created.                |
| **Branch URL**    | The URL of the deployed branch in Amplify.        |

---

Feel free to adjust configurations as necessary for your use case. For any issues or questions, please raise an issue in the repository or consult the AWS CDK and Amplify documentation.

--- 

