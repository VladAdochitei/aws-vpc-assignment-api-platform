# Task: Generate Terraform/Infrastructure Manifest

## Purpose

Create an infrastructure-focused reference document detailing IaC organization, resource provisioning logic, deployment flow, and operational considerations. This is a guide for DevOps engineers, platform engineers, or developers managing infrastructure changes.

## Inputs

- Infrastructure-as-code directory (Terraform, CloudFormation, Pulumi, etc.)
- Configuration files (terraform.tfvars, .env, config files)
- Deployment scripts or CI/CD pipeline definitions
- Resource state history or drift reports (if applicable)
- Runbooks or operational documentation

## Questions to Ask the User

Before diving in, gather context:

1. **IaC Structure & Organization**
   - Do you use workspaces or separate environments (dev/staging/prod)?
   - Where is the remote state stored? (S3, Terraform Cloud, local?)
   - Are there multiple root modules or a single monolithic one?
   - Any shared/reusable modules? Where are they located?

2. **Resource Provisioning**
   - What AWS services are actually provisioned? (just API Gateway + Lambda + DynamoDB, or more?)
   - Are there any manual setup steps that aren't automated? (e.g., VPC peering, secrets pre-populated)
   - Are there dependencies on pre-existing resources? (IAM roles, VPCs, subnets)
   - Any resources that are excluded from Terraform and managed separately?

3. **Deployment & Rollback**
   - How is infrastructure deployed? (terraform apply via CI/CD, manual, git-ops?)
   - Are there approval gates or manual review steps?
   - How do you roll back failed deployments?
   - What's the deployment frequency? (per PR, per merge, manual triggers)

4. **Secrets & Sensitive Data**
   - Where are secrets stored? (AWS Secrets Manager, Parameter Store, .env files, HashiCorp Vault?)
   - How are they injected into Lambda/containers? (environment variables, mounted files, API calls?)
   - Are there any secrets that need pre-population before Terraform runs?

5. **Scaling & Performance**
   - Are there auto-scaling configurations? (Lambda concurrency limits, DynamoDB capacity)
   - Any performance tuning or optimization that's infrastructure-side? (Lambda memory, DynamoDB throughput)
   - Are there cost optimizations in place? (reserved capacity, spot instances, data transfer optimization)

6. **Monitoring & Observability**
   - What's logged/monitored? (CloudWatch, X-Ray, third-party tools)
   - Are alarms/dashboards defined in IaC or manually created?
   - How do you track infrastructure costs?

7. **Known Issues & Constraints**
   - Any resources that can't be destroyed (soft deletes, manual cleanup)?
   - Any Terraform state corruption or drift issues?
   - Any resource limits hit (API throttling, quotas)?
   - Any gotchas with creating/destroying in a specific order?

## Outputs

**TERRAFORM_MANIFEST.md** (stored in `.claude/tasks/outputs/manifests/TERRAFORM_MANIFEST.md`) containing:

### 1. Infrastructure Overview
- Diagram (ASCII or text-based) showing resource layout
- List of all AWS services provisioned
- Environment setup (dev/staging/prod/other)
- Deployment flow (code → Terraform → AWS)

### 2. Module Structure & Purpose
For each Terraform module:
- **Purpose**: What resources it creates, why
- **Inputs (variables)**: All input variables with types and defaults
- **Outputs**: What resources/values it exports to other modules
- **Resources Created**: List of AWS resources (e.g., "Creates 1 API Gateway, 2 Lambdas, 1 DynamoDB table")
- **Dependencies**: What other modules it depends on
- **Constraints**: Any limitations or assumptions

### 3. Resource Inventory
Complete list of all provisioned AWS resources:
```
λ Lambda Functions
  - lambda_vpc_handler (128MB memory, 30s timeout, 10 reserved concurrency)
  - lambda_subnet_handler (128MB memory, 30s timeout, 10 reserved concurrency)

📊 DynamoDB Tables
  - resource_tracking (on-demand pricing, GSIs for type/reverse queries)

🔌 API Gateway
  - vpc-subnet-api (regional, 5 stages, custom domain: api.example.com)

🔐 IAM Roles
  - lambda-execution-role (permissions for EC2, DynamoDB, S3, CloudWatch)
```

### 4. Deployment & Provisioning Flow
- **Init**: terraform init (state setup, module download)
- **Plan**: terraform plan (what changes will be made)
- **Apply**: terraform apply (create/update resources)
- **Destroy**: terraform destroy (cleanup steps, what's not deleted)
- **Rollback**: How to revert a failed deployment

### 5. Environment Configuration
- **Dev**: Variables and resource sizes for development
- **Staging**: Variables and resource sizes for staging/testing
- **Prod**: Variables and resource sizes for production
- **Local**: How to run infrastructure locally (if applicable)

### 6. State Management
- **Location**: Where Terraform state is stored (S3 bucket, path, access control)
- **Locking**: How state is locked during apply (DynamoDB table, Terraform Cloud, etc.)
- **Backup**: How state backups are created/stored
- **Drift Detection**: How to detect and reconcile state drift

### 7. Secrets & Configuration
- **Secrets**: Where sensitive data is stored (Parameter Store, Secrets Manager, .env)
- **Injection**: How secrets are passed to Lambda (environment variables, mounted files)
- **Rotation**: How secrets are rotated (if applicable)
- **Access Control**: Who can read/write secrets

### 8. Scaling & Performance Configuration
- **Lambda**: Memory, timeout, reserved concurrency, layers
- **DynamoDB**: Capacity mode (on-demand vs. provisioned), throughput, TTL
- **API Gateway**: Rate limiting, throttling, caching
- **Auto-scaling**: Rules and thresholds (if applicable)

### 9. Monitoring & Alarms
- **CloudWatch**: Dashboards, log groups, log retention
- **Alarms**: What's monitored (Lambda errors, DynamoDB throttling, API latency)
- **X-Ray**: Tracing configuration (if enabled)
- **Logs**: Where to find logs for each component

### 10. Cost Breakdown
- **Estimated monthly costs** (Lambda invocations, DynamoDB, data transfer, API calls)
- **Cost optimization** (if any: reserved capacity, spot instances, caching)
- **Billing alerts**: Where to monitor AWS costs

### 11. Deployment Checklist
- Step-by-step guide to deploy infrastructure
- Prerequisites (AWS account, Terraform, CLI tools)
- How to validate before applying
- How to verify deployment succeeded
- Rollback steps

### 12. Known Issues & Limitations
- Resources that can't be destroyed (manual cleanup required)
- State corruption issues or workarounds
- Quota/limit issues
- Performance bottlenecks in provisioning
- Ordering constraints (e.g., "delete subnets before VPCs")

### 13. Disaster Recovery
- **Backup strategy**: How data/state is backed up
- **Recovery time objective (RTO)**: How quickly can you recover
- **Recovery point objective (RPO)**: How much data loss is acceptable
- **Disaster recovery steps**: Manual runbook for recovery

## Process

### Phase 1: Gather Context
- Ask user the questions above
- Document their answers
- Identify IaC tool (Terraform, CloudFormation, Pulumi, etc.)

### Phase 2: Map Infrastructure
- Read the root module (main.tf, variables.tf, outputs.tf)
- List all modules and their purpose
- Build a dependency graph (which module calls which)
- Identify all AWS services provisioned

### Phase 3: Deep-Dive Each Module
- Read variables.tf → understand inputs
- Read main.tf → understand resources created
- Read outputs.tf → understand what's exported
- Trace resource dependencies
- Identify any conditionals or loops (resource count, for_each)

### Phase 4: Resource Inventory
- Count and list every AWS resource
- Note sizes, capacity, and configuration (Lambda memory, DynamoDB capacity, etc.)
- Identify single points of failure
- Note cost drivers (DynamoDB on-demand vs. provisioned, Lambda invocations, etc.)

### Phase 5: Deployment & State Analysis
- Trace how Terraform is invoked (CI/CD, manual, git-ops)
- Understand state management (where stored, how locked, backup strategy)
- Document deployment flow (init → plan → apply)
- Identify approval gates, monitoring, rollback steps

### Phase 6: Configuration & Secrets
- Identify all variables and their defaults
- Find where secrets are stored/injected
- Document environment-specific configurations
- Trace how secrets flow into Lambda/containers

### Phase 7: Generate Terraform Manifest
- Organize findings into the output structure above
- Use actual file names and line numbers
- Include ASCII diagram of infrastructure
- Add cost breakdown and scaling info

### Phase 8: Validate & Deliver
- Cross-check against actual Terraform files (spot-check a few resources)
- Confirm diagram matches actual infrastructure
- Verify all modules are documented
- Deliver as TERRAFORM_MANIFEST.md

## Quality Checklist

- [ ] All modules are documented with purpose, inputs, outputs, and resources
- [ ] ASCII diagram shows all major resources and how they connect
- [ ] Complete inventory of AWS resources (count, configuration, costs)
- [ ] Deployment flow is step-by-step with commands and expected outputs
- [ ] State management is documented (location, locking, backup)
- [ ] Environment configurations (dev/staging/prod) are explicit
- [ ] Secrets handling is clear (where stored, how injected, rotation)
- [ ] Scaling configuration is documented (Lambda, DynamoDB, API Gateway)
- [ ] Monitoring and alarms are listed with thresholds
- [ ] Known issues/limitations are documented with workarounds
- [ ] Deployment checklist is step-by-step, testable
- [ ] Cost breakdown is estimated with justification
- [ ] All file paths and resource names match actual Terraform

## Example Outputs

**Infrastructure Diagram** (excerpt):
```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │  (regional)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌────▼─────┐
    │   Lambda  │      │   Lambda  │      │  ...     │
    │  VPC Ops  │      │ Subnet Ops│      │          │
    └─────┬─────┘      └─────┬─────┘      └────┬─────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   DynamoDB      │
                    │ (Single Table)  │
                    │ - VPC records   │
                    │ - Subnet records│
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  AWS EC2 API    │
                    │ (Create VPCs)   │
                    └─────────────────┘
```

**Module Breakdown** (excerpt):
```
## modules/lambda/

**Purpose**: Package, deploy, and manage Lambda functions with IAM roles

**Inputs**:
- function_name (string) — Lambda function name
- handler (string) — Function handler (e.g., "lambda_vpc_handler.create_vpc_handler")
- runtime (string, default: "python3.11")
- memory_size (number, default: 128)
- timeout (number, default: 30)
- source_dir (string) — Path to code directory

**Outputs**:
- function_arn (string) — ARN of created Lambda
- function_name (string) — Name for reference in API Gateway
- role_arn (string) — IAM role ARN

**Resources Created**:
- aws_lambda_function — actual Lambda
- aws_iam_role — execution role
- aws_iam_role_policy_attachment — attach policies (EC2, DynamoDB, CloudWatch)
- aws_lambda_permission — allow API Gateway to invoke

**Dependencies**:
- modules/iam (for policy templates)
- Python code in src/ (packaged as ZIP)

**Constraints**:
- Maximum 10GB uncompressed code size
- Memory: 128–10,240 MB
- Timeout: 1–900 seconds
- Cold start adds ~1–5s for first invocation
```

**Deployment Checklist** (excerpt):
```
## Deploy to Production

1. Verify changes locally
   $ terraform plan -var-file=prod.tfvars | less

2. Create Git tag for audit trail
   $ git tag infra-prod-v$(date +%Y%m%d-%H%M%S)
   $ git push origin --tags

3. Apply changes (approver required)
   $ terraform apply -var-file=prod.tfvars
   (interactive approval step)

4. Verify deployment
   $ aws lambda list-functions --region eu-west-1 | grep vpc_handler
   $ aws apigateway get-rest-apis --region eu-west-1

5. Run smoke tests
   $ curl https://api.example.com/vpcs
   (expect 200 OK with VPC list)

6. Monitor CloudWatch
   https://console.aws.amazon.com/cloudwatch/...
   (check for errors in Lambda logs)
```

## Reusability

This task works for any IaC:
- **Terraform** (HCL, modules, workspaces)
- **CloudFormation** (YAML/JSON templates, stacks)
- **Pulumi** (Python/Go/TypeScript, stacks)
- **Kubernetes** (Helm, YAML manifests, operators)
- **Serverless Framework** (serverless.yml, functions, plugins)

Adapt Phase 2 (module structure) to match your IaC tool's abstractions (e.g., CloudFormation stacks instead of Terraform modules, Helm charts instead of modules).

