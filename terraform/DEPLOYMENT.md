# Multi-Environment Terraform Deployment Guide

## Overview

The terraform infrastructure is organized by environment: `dev`, `nprd` (non-production), and `prod`. Each environment has its own state file and configuration.

### TL&DR

Deploy Commands:

```sh
# Initialize for dev
terraform init -backend-config=environments/dev/backend.tfbackend
```

```sh
# Plan for dev
terraform plan -var-file=environments/dev/terraform.tfvars
```

```sh
# Apply to prod
terraform apply -var-file=environments/prod/terraform.tfvars
```

OR

```sh
# Run this command and perform actions from th Makefile
make help

make tf-init-dev

make tf-plan-dev

make tf-apply-dev

make tf-destroy-dev

# ...etc
```

## Directory Structure

```
terraform/
├── environments/
│   ├── dev/           # Development environment
│   │   ├── backend.tfbackend       # Dev state file config
│   │   └── terraform.tfvars        # Dev variable overrides
│   ├── nprd/          # Non-production (staging/testing)
│   │   ├── backend.tfbackend
│   │   └── terraform.tfvars
│   └── prod/          # Production
│       ├── backend.tfbackend
│       └── terraform.tfvars
├── modules/           # Shared Terraform modules
├── bootstrap/         # Initial S3 bucket setup
├── main.tf            # Infrastructure code (all environments)
├── providers.tf       # Provider and backend config
└── variables.tf       # Variable definitions
```

## Deploying to an Environment

### Step 1: Initialize Terraform

Initialize the backend for your target environment from the repo root:

```bash
terraform init \
  -backend-config=terraform/environments/dev/backend.tfbackend
```

Repeat for each environment (`nprd`, `prod`). This only needs to be done once per environment.

### Step 2: Plan Changes

Review what Terraform will create/change:

```bash
terraform plan \
  -var-file=terraform/environments/dev/terraform.tfvars
```

### Step 3: Apply Changes

Deploy to the environment:

```bash
terraform apply \
  -var-file=terraform/environments/dev/terraform.tfvars
```

Alternatively, use `-chdir` to work from the environment directory:

```bash
terraform -chdir=terraform plan \
  -var-file=environments/dev/terraform.tfvars
```

## Environment-Specific Configuration

Each environment directory (`dev/`, `nprd/`, `prod/`) contains only two files:

### `terraform.tfvars`
Environment-specific variable overrides:
- `aws_region`: AWS region
- `environment`: Environment name (dev/nprd/prod)
- `function_name`: Lambda function name (environment-prefixed)

**Example (environments/dev/terraform.tfvars):**
```hcl
aws_region  = "eu-west-1"
environment = "dev"
function_name = "vpc-assignment-api-dev"
```

### `backend.tfbackend`
State file configuration for that environment. Passed to `terraform init` via `-backend-config` flag:
```hcl
bucket = "aws-api-vpc-assignment-tfstate"
key    = "aws-api-vpc-assignment/dev/terraform.tfstate"
region = "eu-central-1"
```

This ensures each environment's state is isolated in the S3 bucket:
```
aws-api-vpc-assignment-tfstate/
├── aws-api-vpc-assignment/dev/terraform.tfstate
├── aws-api-vpc-assignment/nprd/terraform.tfstate
└── aws-api-vpc-assignment/prod/terraform.tfstate
```

## Root Terraform Configuration

The actual infrastructure code is in the root `terraform/` directory:

- **`main.tf`** — Infrastructure resources (Lambda, etc.) defined once, used by all environments
- **`providers.tf`** — Provider config and backend definition (backend details come from `-backend-config`)
- **`variables.tf`** — Input variable definitions

This way, infrastructure code changes apply to all environments automatically—no duplicated main.tf files.

## Useful Commands

All commands run from the repo root. Select environment via `-var-file` flag.

### View current state (dev environment)

```bash
terraform state list -var-file=terraform/environments/dev/terraform.tfvars
terraform state show aws_lambda_function.this -var-file=terraform/environments/dev/terraform.tfvars
```

### Destroy environment

```bash
# Destroy dev
terraform destroy -var-file=terraform/environments/dev/terraform.tfvars

# Destroy prod
terraform destroy -var-file=terraform/environments/prod/terraform.tfvars
```

### Switch environments

```bash
# Plan for production
terraform plan -var-file=terraform/environments/prod/terraform.tfvars

# Plan for development
terraform plan -var-file=terraform/environments/dev/terraform.tfvars

# Plan for non-production
terraform plan -var-file=terraform/environments/nprd/terraform.tfvars
```

## State File Location

All state files are stored in the S3 bucket `aws-api-vpc-assignment-tfstate`. The bucket was created by the bootstrap configuration (`terraform/bootstrap/`).

**State paths:**
- Dev: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/dev/terraform.tfstate`
- NPRD: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/nprd/terraform.tfstate`
- Prod: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/prod/terraform.tfstate`

## Notes

- **Single source of truth:** `main.tf` defines infrastructure once—changes automatically apply to all environments. No duplicated code.
- **State isolation:** Each environment's state is completely independent (stored in separate S3 keys)—destroying dev won't affect nprd or prod.
- **Shared modules:** The `modules/` directory is shared across all environments. Changes here affect all environments.
- **Environment-specific values:** Only `terraform.tfvars` and `backend.tfbackend` differ per environment. Everything else is shared.
