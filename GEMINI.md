# Project Overview & Strategic Goal

This repository is a `cdktf` (Cloud Development Kit for Terraform) codebase that serves as a **foundational library of reusable infrastructure modules**. We use Python for our `cdktf` constructs.

The immediate goal is to provide a robust, forkable template for deploying common AWS architectural patterns.

The **ultimate strategic goal** is for this repository to become the core infrastructure library for an automated, API-driven "Infrastructure Factory". This factory will programmatically generate new client repositories based on high-level architectural inputs (e.g., a JSON description or a diagram). Therefore, all modules within this repository must be **generic, reusable, and free of any client-specific logic**.

# Guiding Principles for AI-driven Development

*   **Modularity is Paramount:** Infrastructure must be defined in modular Python classes (constructs). Each module should represent a common architectural pattern (e.g., a VPC, an ECS service), not just a single resource.
*   **Generality over Specificity:** When adding or modifying a module, always favor generic, configurable inputs. Avoid hardcoding values that would tie a module to a specific use case. The modules should be the "building blocks," and the `main.py` file is where they are assembled for a specific purpose.
*   **Security First:** All resources should be provisioned with the principle of least privilege. IAM Roles and Security Groups should be as granular as possible.
*   **Idempotency:** Deployments are managed by Terraform and must be repeatable and predictable.

# Current vs. Future Deployment Process

*   **Current:** The deployment process is manual. A developer forks this repo, customizes `main.py`, and runs `cdktf synth` followed by `terraform apply`.
*   **Future:** An API will receive a request, fork this repository, and programmatically generate a `main.py` file based on the request. The API will then trigger a CI/CD pipeline to deploy the infrastructure. **All changes made to this template must support this future state.**

# Key Directories

*   `modules/`: Contains the library of reusable infrastructure modules. This is the core of the template.
*   `main.py`: The entry point for the `cdktf` application. It serves as a **reference implementation** showing how to compose the modules.
*   `cdktf.out/`: The output directory for synthesized Terraform JSON.
*   `README.md` & `SETUP.md`: Core project documentation.

# Special Instructions for AI

*   When asked to add a new module, ensure it is a common, reusable pattern.
*   When asked to modify `main.py`, treat it as an example to be updated, not as a client's production code.
*   Always consider the "Infrastructure Factory" goal. If a user asks for a change that is overly specific, suggest a more generic, configurable alternative that would be more valuable for the template.
*   When adding a new service module, create a new subdirectory in `modules/` (e.g., `modules/new-service/`) and add a `*_utility.py` file.