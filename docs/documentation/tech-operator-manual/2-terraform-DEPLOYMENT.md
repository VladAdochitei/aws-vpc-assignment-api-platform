# Multi-Environment Terraform Deployment Guide

## Overview

The terraform infrastructure is organized by environment: `dev`, `nprd` (non-production), and `prod`. Each environment has its own state file and configuration.

## Directory Structure

```
terraform/
├── environments/
│   ├── dev/           # Development environment
│   ├── nprd/          # Non-production (staging/testing)
│   └── prod/          # Production
├── modules/           # Shared Terraform modules
├── bootstrap/         # Initial S3 bucket setup
├── main.tf            # (deprecated - use environments/)
├── providers.tf       # (deprecated - use environments/)
└── variables.tf       # (deprecated - use environments/)
```

## Deploying to an Environment

### Step 1: Initialize Terraform

Initialize the backend for your target environment:

```bash
cd terraform/environments/dev

terraform init \
  -backend-config=backend.tfbackend \
  -var-file=terraform.tfvars
```

Repeat for each environment (`nprd`, `prod`).

### Step 2: Plan Changes

Review what Terraform will create/change:

```bash
cd terraform/environments/dev

terraform plan \
  -var-file=terraform.tfvars
```

### Step 3: Apply Changes

Deploy to the environment:

```bash
cd terraform/environments/dev

terraform apply \
  -var-file=terraform.tfvars
```

## Environment-Specific Configuration

Each environment directory contains:

### `terraform.tfvars`
Environment-specific variable overrides:
- `aws_region`: AWS region
- `environment`: Environment name (dev/nprd/prod)
- `function_name`: Lambda function name (environment-prefixed)

**Example (dev/terraform.tfvars):**
```hcl
aws_region  = "eu-west-1"
environment = "dev"
function_name = "vpc-assignment-api-dev"
```

### `backend.tfbackend`
State file configuration for that environment:
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

### `main.tf`
Defines resources for the environment. Currently includes:
- Lambda module call with environment-specific function name
- Provider configuration

### `variables.tf`
Input variable definitions (same across all environments).

## Useful Commands

### View current state

```bash
cd terraform/environments/dev
terraform state list
terraform state show aws_lambda_function.this
```

### Destroy environment

```bash
cd terraform/environments/dev
terraform destroy -var-file=terraform.tfvars
```

### Switch environments

```bash
# Deploy to production
cd ../prod
terraform plan -var-file=terraform.tfvars

# Back to development
cd ../dev
terraform plan -var-file=terraform.tfvars
```

## State File Location

All state files are stored in the S3 bucket `aws-api-vpc-assignment-tfstate`. The bucket was created by the bootstrap configuration (`terraform/bootstrap/`).

**State paths:**
- Dev: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/dev/terraform.tfstate`
- NPRD: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/nprd/terraform.tfstate`
- Prod: `s3://aws-api-vpc-assignment-tfstate/aws-api-vpc-assignment/prod/terraform.tfstate`

## Notes

- **State isolation:** Each environment's state is completely independent — destroying dev won't affect nprd or prod.
- **Shared modules:** The `modules/` directory is shared across all environments. Changes here affect all environments.
- **Root config (deprecated):** The old `main.tf`, `providers.tf`, and `variables.tf` at the terraform root are deprecated and shouldn't be used directly.
