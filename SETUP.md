# Developer Setup Guide

This guide provides step-by-step instructions for setting up your local development environment to work on this `cdktf` project, including how to effectively use the Gemini CLI for AI-assisted development.

## 1. Core Prerequisites

Ensure you have the following base tools installed and configured on your system:

*   **Git:** For version control.
*   **Visual Studio Code:** The recommended code editor.
*   **AWS CLI:** With your AWS credentials configured (`aws configure`).
*   **Terraform (v1.0.0+):** [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
*   **Node.js and NPM:** [Installation Guide](https://nodejs.org/en/download/)
*   **Python:** This project uses `pipenv` for dependency management.
    ```bash
    pip install pipenv
    ```

## 2. VS Code Workspace Setup

A well-configured editor is key to productivity.

### Recommended Extensions

Open VS Code and install the following extensions from the Marketplace:

*   **Python** (by Microsoft): Essential for Python development.
*   **HashiCorp Terraform** (by HashiCorp): Provides syntax highlighting and validation for Terraform files.
*   **GitLens** (by GitKraken): Supercharges the Git capabilities built into VS Code.
*   **Docker** (by Microsoft): Useful if you are building and testing container images for ECS/ECR.

### Project Setup

Clone the repository and open the project in VS Code. Then, set up the Python virtual environment:

```bash
# Clone the repository
git clone <your-repository-url>
cd <repository-name>

# Open the project in VS Code
code .

# Install dependencies into a virtual environment
pipenv install

# Activate the virtual environment in your terminal
pipenv shell
```

VS Code should automatically detect the Python interpreter in your new virtual environment.

## 3. Gemini CLI Setup

The Gemini CLI is a powerful tool for making changes to this codebase.

### Installation

Follow the official installation instructions to install the Gemini CLI on your system.

*(Note: As of this writing, the installation process is typically provided by the tool's vendor. Please refer to their official documentation for the most up-to-date instructions.)*

### Configuration

Once installed, ensure Gemini is aware of your project's context. The `.gemini` directory and `GEMINI.md` file in this repository are designed for this purpose. When you run the `gemini` command from the project root, it will automatically use this context.

## 4. Working with Gemini in This Repository

To maintain consistency and leverage the project's structure, use clear and specific prompts when working with Gemini.

### Example Prompts

Here are some examples of effective prompts for common tasks:

**Task: Adding a new module**

> "Create a new, reusable module for AWS ElastiCache (Redis). It should allow for specifying the node type and number of nodes. Place it in the `modules/` directory and follow the existing conventions. Then, update the README to include it in the module list."

**Task: Modifying an existing resource**

> "Modify the `RdsModule` in `modules/rds/rds_utility.py` to add an input parameter for `multi_az_deployment`. It should be a boolean that defaults to `False`."

**Task: Adding a resource to the example stack**

> "I need to add a public S3 bucket to the example `ProductionStack` in `main.py`. Use the existing `S3Module` to create a bucket named 'prod-webapp-public-assets' and output its URL."

**Task: Asking for guidance**

> "What's the best way to add a CloudFront distribution in front of the Application Load Balancer in the `main.py` example? Should I create a new module for CloudFront first?"

By following these setup instructions and prompt patterns, you can ensure that all contributions, whether human or AI-driven, adhere to the project's goals and conventions.
