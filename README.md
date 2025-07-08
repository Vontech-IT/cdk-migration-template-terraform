# CDKTF Python Infrastructure Template

This repository is a template for creating and managing cloud infrastructure using the Cloud Development Kit for Terraform (CDKTF) with Python. It provides a structured, modular approach to defining reusable infrastructure components, which can be composed to build complex, client-specific deployments on AWS.

This template is designed to be the foundation of an "infrastructure factory," where new client environments can be quickly instantiated by forking this repository and customizing a few key files.

**Technology Stack:**
*   **[Terraform](https://www.terraform.io/):** The underlying engine for provisioning and managing infrastructure.
*   **[CDKTF](https://developer.hashicorp.com/terraform/cdktf):** The framework that allows you to define Terraform infrastructure using Python.
*   **[Python](https://www.python.org/):** The language used to define the infrastructure logic.

---

## Architecture Example

The `main.py` in this template provisions a realistic, multi-tier web application architecture in AWS, demonstrating how to use and connect the included modules.

![Architecture Diagram](https://i.imgur.com/8nL4vF5.png)

This architecture includes:
*   A **VPC** with public and private subnets.
*   A public-facing **Application Load Balancer (ALB)** to distribute incoming traffic.
*   An **Auto Scaling Group (ASG)** of EC2 instances in the private subnets to run the application.
*   An **RDS (MySQL) database** in the private subnets for data persistence.
*   **Security Groups** to tightly control traffic between the different tiers.
*   An **IAM Role** for the EC2 instances to grant necessary permissions securely.

---

## Prerequisites

Before you begin, ensure you have the following tools installed. For a detailed walkthrough of setting up your editor and the Gemini CLI, see the [**Developer Setup Guide (SETUP.md)**](./SETUP.md).

1.  **Terraform (v1.0.0+):** [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
2.  **Node.js and NPM:** [Installation Guide](https://nodejs.org/en/download/)
3.  **Python and Pipenv:** `pip install pipenv`
4.  **CDKTF CLI:** `npm install -g cdktf-cli`
5.  **AWS CLI:** [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (and configure your credentials)

---

## How to Use This Template

For a detailed, step-by-step guide on provisioning the example architecture to an AWS account, see the [**AWS Deployment Guide (DEPLOYMENT_GUIDE.md)**](./DEPLOYMENT_GUIDE.md).

1.  **Fork This Repository:** Create a new repository for your project by forking this template.
2.  **Set Up Local Environment:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    pipenv install
    pipenv shell
    ```
3.  **Customize `main.py`:** Open `main.py` and modify the `ProductionStack` class to match your requirements. You can change resource names, CIDR blocks, instance types, and add or remove modules.
4.  **Synthesize Terraform Configuration:**
    ```bash
    cdktf synth
    ```
5.  **Deploy Your Infrastructure:**
    ```bash
    # Navigate to the directory containing the generated Terraform plan
    cd cdktf.out/stacks/aws-production-stack/

    # Initialize Terraform (downloads providers)
    terraform init

    # (Optional) Review the planned changes
    terraform plan

    # Apply the changes to your cloud provider
    terraform apply
    ```

---

## Available Modules

This template includes the following reusable modules in the `modules/` directory, categorized by domain.

### Core & Networking
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **VPC**            | Creates a VPC with public and private subnets.                              |
| **Security Group** | Creates a Security Group with specified ingress and egress rules.           |
| **IAM Role**       | Creates an IAM Role with an assume role policy and attaches policies.       |
| **ALB**            | Creates an Application Load Balancer, Target Group, and Listener.           |
| **S3**             | Creates a private S3 bucket with versioning.                                |

### Compute
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **ASG**            | Creates an Auto Scaling Group using a Launch Template for EC2 instances.    |
| **EC2 Instance**   | Creates a single EC2 instance (less common, prefer ASG).                    |
| **Lambda**         | Creates a serverless Lambda function from a deployment package.             |
| **ECR**            | Creates an ECR repository to store Docker container images.                 |
| **ECS Fargate**    | Creates a full Fargate service (Cluster, Task Definition, Service).         |

### Database & Storage
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **RDS**            | Creates an RDS database instance with a subnet group.                       |

### Messaging
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **SQS**            | Creates a Standard or FIFO SQS queue.                                       |
| **SNS**            | Creates a Standard or FIFO SNS topic for pub/sub messaging.                 |

### AI & Machine Learning
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **SageMaker**      | Creates a SageMaker Notebook Instance for ML development.                   |
| **Comprehend**     | Creates a Comprehend Document Classifier for custom text classification.    |

### Internet of Things (IoT)
| Module             | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **IoT Thing**      | Creates a representation of a physical device or logical entity.            |
| **IoT Topic Rule** | Creates a rule to process and route messages from IoT devices.              |

---

### Contributing a New Module

1.  Create a new directory: `modules/new-service/`.
2.  Create a new file: `modules/new-service/new_service_utility.py`.
3.  In the file, create a class `NewServiceModule(Construct)`.
4.  Define the resources for the service using the official `cdktf` provider bindings from the `imports.aws` package.
5.  Import and use your new module in `main.py`.
