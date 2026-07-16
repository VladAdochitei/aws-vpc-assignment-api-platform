.PHONY: help tf-fmt tf-validate tf-init-dev tf-init-nprd tf-init-prod tf-plan-dev tf-plan-nprd tf-plan-prod tf-apply-dev tf-apply-nprd tf-apply-prod tf-destroy-dev tf-destroy-nprd tf-destroy-prod

ENV ?= dev

help:
	@echo "Terraform Multi-Environment Commands"
	@echo ""
	@echo "Formatting & Validation:"
	@echo "  make tf-fmt          Format all Terraform files"
	@echo "  make tf-validate     Validate Terraform configuration"
	@echo ""
	@echo "Initialization (run once per environment):"
	@echo "  make tf-init-dev     Initialize dev backend"
	@echo "  make tf-init-nprd    Initialize nprd backend"
	@echo "  make tf-init-prod    Initialize prod backend"
	@echo ""
	@echo "Planning & Applying:"
	@echo "  make tf-plan-dev     Plan changes for dev"
	@echo "  make tf-plan-nprd    Plan changes for nprd"
	@echo "  make tf-plan-prod    Plan changes for prod"
	@echo ""
	@echo "  make tf-apply-dev    Apply changes to dev"
	@echo "  make tf-apply-nprd   Apply changes to nprd"
	@echo "  make tf-apply-prod   Apply changes to prod"
	@echo ""
	@echo "Destruction:"
	@echo "  make tf-destroy-dev  Destroy dev resources"
	@echo "  make tf-destroy-nprd Destroy nprd resources"
	@echo "  make tf-destroy-prod Destroy prod resources"
	@echo ""
	@echo "Shortcuts (ENV=dev by default):"
	@echo "  make tf-plan         Plan for current ENV"
	@echo "  make tf-apply        Apply for current ENV"
	@echo "  make tf-destroy      Destroy for current ENV"
	@echo "  make tf-init         Initialize current ENV"
	@echo ""
	@echo "Examples:"
	@echo "  make tf-plan-nprd"
	@echo "  make tf-apply-prod"
	@echo "  make tf-plan ENV=nprd"
	@echo "  make tf-apply ENV=prod"

# Format Terraform files
tf-fmt:
	@echo "Formatting Terraform files..."
	terraform fmt -recursive

# Validate Terraform configuration      -> DOES NOT WORK PROPERLY
tf-validate:
	@echo "Validating Terraform configuration..."
	terraform validate

# Initialize backends
tf-init-dev:
	@echo "Initializing dev backend..."
	terraform init -backend-config=environments/dev/backend.tfbackend

tf-init-nprd:
	@echo "Initializing nprd backend..."
	terraform init -backend-config=environments/nprd/backend.tfbackend

tf-init-prod:
	@echo "Initializing prod backend..."
	terraform init -backend-config=environments/prod/backend.tfbackend

# Plan changes
tf-plan-dev:
	@echo "Planning changes for dev..."
	terraform plan -var-file=environments/dev/terraform.tfvars

tf-plan-nprd:
	@echo "Planning changes for nprd..."
	terraform plan -var-file=environments/nprd/terraform.tfvars

tf-plan-prod:
	@echo "Planning changes for prod..."
	terraform plan -var-file=environments/prod/terraform.tfvars

# Apply changes
tf-apply-dev:
	@echo "Applying changes to dev..."
	terraform apply -var-file=environments/dev/terraform.tfvars

tf-apply-nprd:
	@echo "Applying changes to nprd..."
	terraform apply -var-file=environments/nprd/terraform.tfvars

tf-apply-prod:
	@echo "Applying changes to prod..."
	terraform apply -var-file=environments/prod/terraform.tfvars

# Destroy resources
tf-destroy-dev:
	@echo "Destroying dev resources..."
	terraform destroy -var-file=environments/dev/terraform.tfvars

tf-destroy-nprd:
	@echo "Destroying nprd resources..."
	terraform destroy -var-file=environments/nprd/terraform.tfvars

tf-destroy-prod:
	@echo "Destroying prod resources..."
	terraform destroy -var-file=environments/prod/terraform.tfvars

# Shortcuts with ENV variable (default: dev)
tf-init:
	@$(MAKE) tf-init-$(ENV)

tf-plan:
	@$(MAKE) tf-plan-$(ENV)

tf-apply:
	@$(MAKE) tf-apply-$(ENV)

tf-destroy:
	@$(MAKE) tf-destroy-$(ENV)
