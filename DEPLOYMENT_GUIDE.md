# AWS Deployment Guide

This guide provides a detailed, step-by-step walkthrough for deploying the example infrastructure defined in this repository to your AWS account. Following these steps will provision a multi-tier web application as defined in `main.py`.

## Prerequisites

Before you begin, you must have the following:

1.  **An AWS Account:** You will need an active AWS account with permissions to create the resources defined in the stack (VPC, EC2, S3, RDS, etc.).
2.  **Configured AWS CLI:** Your AWS CLI must be installed and configured with credentials for your account. You can configure it by running `aws configure` and providing your Access Key ID, Secret Access Key, and default region.
    *   [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3.  **All development tools listed in [SETUP.md](./SETUP.md):** This includes Terraform, Node.js, Python/pipenv, and the `cdktf-cli`.

---

## Deployment Steps

### Step 1: Clone the Repository

If you haven't already, clone this repository to your local machine:

```bash
git clone <your-repository-url>
cd <repository-name>
```

### Step 2: Install Project Dependencies

This project uses `pipenv` to manage Python dependencies. Run the following commands to install them and activate the virtual environment:

```bash
# Install dependencies
pipenv install

# Activate the virtual environment for your shell session
pipenv shell
```

### Step 3: Review and Customize Configuration

The infrastructure is defined in `main.py`. Before deploying, you should review the configuration and customize it for your needs.

Open `main.py` and pay close attention to the **Configuration** section:

```python
# --- Configuration ---
# Define project-specific tags and configuration variables here.
project_tags = {
    "ManagedBy": "CDKTF",
    "Project": "WebApp-Production"
}
# WARNING: Do not hardcode secrets in production. Use a secret manager.
db_password = "YourSecurePassword123"
# Example AMI for Amazon Linux 2 in us-east-1. Find the latest for your region.
latest_ami = "ami-0c55b159cbfafe1f0"
```

*   **`db_password`**: **CRITICAL!** The default password is for demonstration purposes only. **DO NOT** use this password in a real environment. For production, you should store the password in AWS Secrets Manager and retrieve it in your code.
*   **`latest_ami`**: The default Amazon Machine Image (AMI) is for the `us-east-1` region. If you are deploying to a different region, you **must** find a valid Amazon Linux 2 AMI ID for that region. You can find AMIs in the EC2 console.
*   **`project_tags`**: You can customize these tags to fit your organization's tagging strategy.

### Step 4: Synthesize the Terraform Code

The `cdktf synth` command reads your Python code and compiles it into a standard Terraform configuration file (in JSON format).

```bash
cdktf synth
```

This will create a `cdktf.out` directory containing the synthesized Terraform code.

### Step 5: Navigate to the Output Directory

The generated code for your stack is located in a subdirectory within `cdktf.out`. Navigate into this directory to run the standard Terraform commands:

```bash
cd cdktf.out/stacks/aws-production-stack/
```

### Step 6: Initialize Terraform

The `terraform init` command initializes the directory, downloads the necessary provider plugins (in this case, for AWS), and sets up the backend for storing state.

```bash
terraform init
```

You should see a message confirming that "Terraform has been successfully initialized."

### Step 7: Plan the Deployment

The `terraform plan` command creates an execution plan. It shows you exactly what resources Terraform will create, modify, or destroy without actually making any changes. This is a crucial step to verify that the configuration is correct.

```bash
terraform plan
```

Review the output carefully. You should see a list of resources to be added.

### Step 8: Apply the Deployment

The `terraform apply` command executes the plan and creates the resources in your AWS account.

```bash
terraform apply
```

Terraform will show you the plan again and ask for confirmation. Type `yes` and press Enter to proceed. The deployment will take several minutes as it provisions the VPC, database, and other resources.

### Step 9: Access Your Application

Once the `apply` command is complete, Terraform will print the defined outputs. You can view these at any time with `terraform output`.

```
Outputs:

alb_dns_name = "Prod-WebApp-ALB-1234567890.us-east-1.elb.amazonaws.com"
db_endpoint = "prod-webapp-db.abcdefghijkl.us-east-1.rds.amazonaws.com"
```

You can now access your web application by pasting the `alb_dns_name` into your web browser.

---

## Cleaning Up

To avoid ongoing charges, you should destroy the infrastructure when you are finished experimenting.

### Step 10: Destroy All Resources

The `terraform destroy` command will remove all resources created by this deployment.

```bash
# Make sure you are still in the cdktf.out/stacks/aws-production-stack/ directory
terraform destroy
```

Terraform will show you all the resources that will be destroyed and ask for confirmation. Type `yes` and press Enter. This process will also take several minutes.

Once complete, all the infrastructure you deployed will be removed from your AWS account.
