# Terraform Manifest: AWS VPC Assignment API Platform

_Last verified: 2026-07-21_

Infrastructure-focused reference for `terraform/`. For application code, see `CODE_MANIFEST.md`. For architecture overview, see `TECHNICAL_MANIFEST.md`.

## 1. Infrastructure Overview

```
                         ┌───────────────────────┐
                         │     API Gateway        │
                         │  (REST, regional,      │
                         │  authorization = NONE) │◄── no auth configured (see §12)
                         └───────────┬────────────┘
                                     │  AWS_PROXY integration
                 ┌───────────────────┴───────────────────┐
                 │                                       │
       ┌─────────▼─────────┐                   ┌─────────▼─────────┐
       │  vpc_lambda        │                   │  subnet_lambda     │
       │  (module.vpc_lambda)│                  │ (module.subnet_lambda)│
       │  handler:           │                  │  handler:           │
       │  lambda_vpc_handler │                  │  lambda_subnet_handler│
       │  .api_handler       │                  │  .api_handler        │
       └─────────┬───────────┘                  └─────────┬───────────┘
                 │                                        │
                 └───────────────────┬────────────────────┘
                                      │  boto3 (ec2:*, dynamodb:*)
                    ┌─────────────────┴─────────────────┐
                    │                                     │
          ┌─────────▼─────────┐                ┌─────────▼─────────┐
          │   AWS EC2 API      │                │   DynamoDB Table   │
          │  (real VPCs/       │                │ (module.resources_ │
          │   subnets)         │                │  table, single-    │
          └─────────────────────┘                │  table design)     │
                                                  │  PK/SK + 2 GSIs     │
                                                  └─────────────────────┘
```

**AWS services provisioned**: API Gateway (REST, regional), Lambda (2 functions), DynamoDB (1 table), IAM (2 execution roles + 6 inline policies).

**Environments**: `dev`, `nprd` (non-production), `prod` — same `main.tf`/modules, isolated via separate `-var-file` and `-backend-config` per environment. Only `dev` currently has live (uncommented) variable values; `nprd` and `prod` `.tfvars` files are fully commented out (see §5).

**Deployment flow**: developer runs `make build` (root `Makefile`) to package `src/` + dependencies into `build/package/`, which Terraform zips via `archive_file` and uploads as the Lambda deployment package. Then `terraform apply` (directly, or via `terraform/Makefile` targets) provisions/updates AWS resources.

## 2. Module Structure & Purpose

### `terraform/modules/lambda/`

**Purpose**: Creates one Lambda function plus its own dedicated IAM execution role (basic execution policy attached; resource-specific permissions attached externally in root `iam.tf`).

**Inputs** (`variables.tf`):
| Variable | Type | Default |
|---|---|---|
| `function_name` | string | required |
| `handler` | string | required |
| `runtime` | string | `"python3.12"` |
| `source_dir` | string | required |
| `environment_variables` | map(string) | `{}` |
| `architecture` | string | `"x86_64"` (validated: must be `x86_64` or `arm64`) |

**Outputs**: `function_name`, `function_arn`, `invoke_arn`, `role_name`, `role_id`

**Resources Created**: `aws_iam_role.exec`, `aws_iam_role_policy_attachment.basic_execution` (`AWSLambdaBasicExecutionRole`), `aws_lambda_function.this`, `data.archive_file.source`

**Dependencies**: none on other modules; consumes `source_dir` pointing at `${path.module}/../build/package` (i.e. the output of `make build`, run from repo root — **not** produced by Terraform itself).

**Constraints**: no `memory_size` or `timeout` variable exposed — both fall back to AWS Lambda defaults (128 MB, 3 s), which is unusually low for a function making both an EC2 API call and a DynamoDB call in sequence; worth revisiting if cold-start or timeout errors appear in practice. No `reserved_concurrent_executions` configured either.

### `terraform/modules/api-gateway/`

**Purpose**: Builds a REST API from a generic `routes` map — dynamically constructs the API Gateway resource tree (up to 3 path segments deep) and wires each route to `AWS_PROXY` Lambda integration.

**Inputs** (`variables.tf`):
| Variable | Type | Default |
|---|---|---|
| `api_name` | string | required |
| `stage_name` | string | `"dev"` |
| `routes` | `map(object({ path=list(string), http_method=string, lambda_function_arn=string, lambda_function_name=string }))` | required |

**Outputs**: `api_endpoint` (invoke URL), `api_id`, `api_execution_arn`

**Resources Created**: 1 `aws_api_gateway_rest_api`, up to 3 levels of `aws_api_gateway_resource` (built from `distinct`/`flatten` locals over route paths), 1 `aws_api_gateway_method` + `aws_api_gateway_integration` + `aws_api_gateway_method_response` + `aws_api_gateway_integration_response` per route, 1 `aws_api_gateway_deployment`, 1 `aws_api_gateway_stage`, 1 `aws_lambda_permission` per unique Lambda referenced by any route.

**Dependencies**: none on other modules; consumes Lambda ARNs/names from `module.vpc_lambda` and `module.subnet_lambda` outputs.

**Constraints**: hardcoded max path depth of 3 (`level1_paths`/`level2_paths`/`level3_paths` locals) — a documented comment in `main.tf:26-27` notes a 4th level block would need to be added manually if a deeper route (e.g. `/vpcs/{vpc_id}/subnets/{subnet_id}`) is ever introduced. `authorization = "NONE"` is hardcoded on every method (`aws_api_gateway_method.route`, line 84) — the module has no parameter for wiring in an authorizer.

### `terraform/modules/dynamodb/`

**Purpose**: Generic single-table DynamoDB module — attributes and GSIs passed in as variables, not hardcoded to VPC/subnet specifically (reusable).

**Inputs** (`variables.tf`):
| Variable | Type | Default |
|---|---|---|
| `table_name` | string | required |
| `hash_key` | string | required |
| `range_key` | string | `null` |
| `attributes` | `list(object({name=string, type=string}))` | required |
| `global_secondary_indexes` | `list(object({name, hash_key, range_key=optional, projection_type}))` | `[]` |
| `billing_mode` | string | `"PAY_PER_REQUEST"` |

**Outputs**: `table_name`, `table_arn`

**Resources Created**: 1 `aws_dynamodb_table.this` with `dynamic "attribute"` and `dynamic "global_secondary_index"` blocks.

**Dependencies**: none.

**Constraints**: no TTL, no point-in-time recovery, no server-side encryption customization (falls back to AWS default encryption at rest), no DynamoDB Streams — none of these are exposed as variables, so enabling any of them requires editing the module itself.

## 3. Resource Inventory

Root module (`terraform/main.tf`, `terraform/iam.tf`) instantiates:

```
λ Lambda Functions (2)
  - vpc-assignment-api-{env}-vpc     — handler: lambda_vpc_handler.api_handler
  - vpc-assignment-api-{env}-subnet  — handler: lambda_subnet_handler.api_handler
  Runtime: python3.12 (root variables.tf default) / python3.14 (dev.tfvars override — see §12 mismatch note)
  Architecture: x86_64
  Memory/timeout: AWS defaults (128 MB / 3s) — not overridden

📊 DynamoDB Table (1)
  - vpc-assignment-api-{env}-DATABASE-resources
  Billing: PAY_PER_REQUEST (on-demand)
  Keys: PK (hash, S), SK (range, S)
  Non-key attribute declared: entity_type (S) — used only by GSI
  GSIs:
    - gsi_reverse: hash_key=SK, projection=ALL       (look up a subnet by SK alone)
    - gsi_type:    hash_key=entity_type, range_key=PK, projection=ALL  (list all of a type)

🔌 API Gateway (1)
  - vpc-assignment-api-{env}-api (REST, regional by default — no explicit endpoint_configuration)
  1 stage: {environment} (dev/nprd/prod)
  10 routes total (5 VPC + 5 subnet, listed in TECHNICAL_MANIFEST.md)
  Authorization: NONE on every route

🔐 IAM Roles (2, one per Lambda)
  - vpc-assignment-api-{env}-vpc-role
      + AWSLambdaBasicExecutionRole (managed policy)
      + inline: vpc-dynamodb (GetItem/PutItem/DeleteItem/Query/Scan/UpdateItem on table + indexes, TransactWriteItems on table)
      + inline: vpc-ec2 (CreateVpc/CreateTags unconditional; DeleteVpc conditional on managed tag; DescribeVpcs)
  - vpc-assignment-api-{env}-subnet-role
      + AWSLambdaBasicExecutionRole
      + inline: subnet-dynamodb (same shape as vpc-dynamodb policy)
      + inline: subnet-ec2 (CreateSubnet/CreateTags unconditional; DeleteSubnet conditional on managed tag; DescribeSubnets/DescribeVpcs)

🪣 S3 (bootstrap only, separate root module: terraform/bootstrap/)
  - aws-api-vpc-assignment-tfstate (versioned, all public access blocked)
```

**Single points of failure**: both Lambdas share nothing at the infra level (separate roles, separate functions) — no SPOF between them. The DynamoDB table and the S3 state bucket are each unique regional resources with no cross-region replication.

**Cost drivers**: DynamoDB `PAY_PER_REQUEST` (scales with traffic, no idle cost), Lambda invocation + duration (no reserved concurrency, so no idle cost either), API Gateway per-request pricing. No NAT Gateway, no VPC-attached Lambda (these Lambdas are NOT deployed inside a VPC themselves — despite the project managing VPCs as a *product*, the Lambdas run in the default AWS-managed Lambda network, not customer VPCs), so no VPC-related networking costs.

## 4. Deployment & Provisioning Flow

**Init** (once per environment):
```bash
terraform -chdir=terraform init -backend-config=environments/dev/backend.tfbackend
```

**Plan**:
```bash
terraform -chdir=terraform plan -var-file=environments/dev/terraform.tfvars
```

**Apply**:
```bash
terraform -chdir=terraform apply -var-file=environments/dev/terraform.tfvars
```

**Destroy**:
```bash
terraform -chdir=terraform destroy -var-file=environments/dev/terraform.tfvars
```

Equivalent shortcuts exist via `terraform/Makefile` (`make tf-init-dev`, `make tf-plan-dev`, `make tf-apply-dev`, `make tf-destroy-dev`, or `make tf-plan ENV=nprd`, etc. — run from `terraform/` directory since the Makefile doesn't `-chdir`).

**Prerequisite not automated by Terraform**: `make build` (root `Makefile`) must be run **before** `terraform apply`, since the Lambda module's `archive_file` zips `${path.module}/../build/package`, which only exists after `make build` runs. There is no CI/CD pipeline definition found in the repo (no `.github/workflows/`, no `buildspec.yml`) — deployment today is entirely manual (`make build && terraform apply`).

**Rollback**: no documented rollback procedure beyond standard Terraform practice (revert the offending commit, `terraform apply` the prior state) or restoring a previous S3-versioned state file. `terraform/DEPLOYMENT.md` doesn't cover rollback explicitly.

**No approval gates**: nothing in the repo enforces plan review before apply (e.g., no CI gate) — this is manual discipline only.

## 5. Environment Configuration

| | dev | nprd | prod |
|---|---|---|---|
| `aws_region` | `eu-central-1` | *(commented out — inherits `variables.tf` default `eu-west-1`)* | *(commented out — inherits `eu-west-1`)* |
| `environment` | `dev` | *(commented out — would default to `dev` from `variables.tf`!)* | *(commented out — would default to `dev`!)* |
| `function_name` | `vpc-assignment-api-dev` | *(commented out — would default to `vpc-assignment-api-dev`!)* | *(commented out — would default to `vpc-assignment-api-dev`!)* |
| `lambda_runtime` | `python3.14` (dev.tfvars) vs. `python3.12` (variables.tf default) | not set | not set |
| Backend key | `aws-api-vpc-assignment/dev/terraform.tfstate` | `aws-api-vpc-assignment/nprd/terraform.tfstate` (commented) | `aws-api-vpc-assignment/prod/terraform.tfstate` (commented) |

**⚠️ nprd and prod are not actually configured.** `environments/nprd/terraform.tfvars` and `environments/prod/terraform.tfvars` contain only commented-out lines — every value is commented, meaning `terraform plan -var-file=environments/nprd/terraform.tfvars` today would fall back to root `variables.tf` defaults, producing a stack literally named/tagged `vpc-assignment-api-dev` in whatever account/region the AWS provider defaults to. Similarly, `environments/nprd/backend.tfbackend` and `environments/prod/backend.tfbackend` are **fully commented out** — running `terraform init -backend-config=environments/nprd/backend.tfbackend` would pass an empty backend config, likely erroring or falling back to asking interactively for backend values. **These two environments are scaffolded but not yet functional.**

**⚠️ Runtime version mismatch**: root `variables.tf:28` defaults `lambda_runtime` to `python3.12`, but `environments/dev/terraform.tfvars:4` overrides it to `python3.14`. `python3.14` may not exist as a published AWS Lambda managed runtime as of this writing — worth verifying against the current AWS Lambda runtime support list before applying to dev, since an invalid runtime string will fail at `apply` time with an AWS API error, not a Terraform-time validation error (no `validation` block exists on `lambda_runtime` unlike `lambda_architecture`).

**Local**: no local/LocalStack setup found — there's no way to run this infrastructure without a real AWS account.

## 6. State Management

- **Location**: S3 bucket `aws-api-vpc-assignment-tfstate` (created by `terraform/bootstrap/bootstrap.tf`), region `eu-central-1` (per `environments/dev/backend.tfbackend`; nprd/prod backend files are commented — see §5).
- **Keys**: `aws-api-vpc-assignment/{dev,nprd,prod}/terraform.tfstate` — one key per environment, fully isolated state.
- **Locking**: **no DynamoDB lock table configured anywhere** — `terraform { backend "s3" {} }` in `providers.tf` has no `dynamodb_table` / `use_lockfile` argument. Concurrent `apply` runs against the same environment are not protected against state corruption from simultaneous writes. This is a gap worth closing (either add a DynamoDB lock table to the bootstrap config, or use S3-native state locking if on a Terraform version that supports it — `~> 1.15.0` per `main.tf`, which does support the native S3 lockfile mechanism (`use_lockfile = true`) introduced in Terraform 1.10+, so this could be added without a separate lock table).
- **Backup**: S3 bucket versioning is enabled (`aws_s3_bucket_versioning.tfstate`), so every state write is retained as a version — this is the only backup mechanism; no automated snapshot/export process exists.
- **Drift detection**: no automated drift detection (no scheduled `terraform plan` in CI) — must be run manually per environment.
- **Bootstrap is a separate, unconnected root module** (`terraform/bootstrap/`) — it has its own `providers.tf` (AWS provider `~> 5.0`, vs. root's `~> 6.54.0` — a version constraint mismatch between the two root modules) and no backend block itself (its own state is presumably local, or was applied once and the state discarded — not documented).

## 7. Secrets & Configuration

- **No secrets are used or stored anywhere in this stack.** No Secrets Manager, no Parameter Store, no `.env` files referenced by Terraform. This is consistent with there being no authentication mechanism implemented (see `CODE_MANIFEST.md` §9) — there's currently nothing that would need a secret (no DB password, no API key store).
- `lambda_environment_variables` (map, default `{}`) is the only mechanism for passing extra config into the Lambdas, and it's empty in all three `.tfvars` files (dev's is present but commented-out example only).
- If the previously-decided Lambda Authorizer + API key approach (`.claude/memory/authorization_decision.md`) is implemented later, this section will need a Secrets Manager or Parameter Store entry for the key list, plus IAM permissions for the authorizer Lambda to read it — none of that scaffolding exists yet.

## 8. Scaling & Performance Configuration

- **Lambda**: memory/timeout left at AWS defaults (128 MB / 3s) — not tuned; no layers used; no provisioned concurrency.
- **DynamoDB**: `PAY_PER_REQUEST` — auto-scales, no manual capacity planning; no TTL attribute configured (soft-deleted/`status`-flagged items accumulate forever).
- **API Gateway**: no throttling, no caching, no usage plans/API keys configured — fully open, unmetered per-client.
- **No auto-scaling configuration** exists anywhere (nothing to scale beyond what's already serverless/on-demand by default).

## 9. Monitoring & Alarms

- **CloudWatch**: Lambda functions get default CloudWatch log groups via the `AWSLambdaBasicExecutionRole` managed policy (auto-created log group per function, default indefinite retention since no `aws_cloudwatch_log_group` resource with an explicit `retention_in_days` is defined in Terraform).
- **No alarms, dashboards, or X-Ray tracing are defined in Terraform.** No `aws_cloudwatch_metric_alarm`, no `aws_xray_*` resources, no `tracing_config` block on the Lambda functions.
- **Logs location**: `/aws/lambda/vpc-assignment-api-{env}-vpc` and `/aws/lambda/vpc-assignment-api-{env}-subnet` in CloudWatch Logs, once deployed.
- **Cost tracking**: no billing alarms or AWS Budgets defined in Terraform.

## 10. Cost Breakdown

Rough estimate for light dev/test usage (order-of-magnitude only — no real usage data exists yet since this appears to not be deployed, or only in dev):

- **Lambda**: negligible at low invocation volume (AWS free tier covers 1M requests + 400,000 GB-seconds/month); 128 MB default memory keeps per-invocation cost low.
- **DynamoDB on-demand**: negligible at low volume — first 25 GB storage and a portion of read/write request units may fall within free tier depending on account age.
- **API Gateway**: ~$3.50 per million REST API requests (no free tier after 12 months for new accounts, or limited free tier for eligible accounts).
- **S3 (state bucket)**: negligible — small state files, versioned.
- **No cost optimization is configured** (no reserved capacity, no savings plans) — appropriate given the on-demand/serverless nature and presumably low current traffic.

## 11. Deployment Checklist

1. **Prerequisites**: Terraform `~> 1.15.0`, AWS CLI credentials with sufficient permissions (IAM, Lambda, API Gateway, DynamoDB, S3), Python 3.14 + pip (for `make build`, per root `Makefile:1`).
2. **One-time bootstrap** (if the state bucket doesn't exist yet): `cd terraform/bootstrap && terraform init && terraform apply`.
3. **Build the Lambda package**: from repo root, `make build` (produces `build/package/`).
4. **Initialize the target environment**: `cd terraform && terraform init -backend-config=environments/dev/backend.tfbackend` (first time only, per environment).
5. **Plan**: `terraform plan -var-file=environments/dev/terraform.tfvars` — review the plan output carefully, especially resource counts for the dynamically-built API Gateway resource tree.
6. **Apply**: `terraform apply -var-file=environments/dev/terraform.tfvars`.
7. **Verify**: `aws lambda list-functions | grep vpc-assignment-api`, `aws apigateway get-rest-apis`, then hit the API endpoint from `terraform output` (no explicit root-level output block was found exporting `module.api_gateway.api_endpoint` — would need to add one, or query via `aws apigateway get-stages`).
8. **Rollback if needed**: `terraform apply` against the prior commit's code, or restore a previous version of the state object from the versioned S3 bucket.

**Before this can be used for nprd/prod**: uncomment and fill in `environments/{nprd,prod}/terraform.tfvars` and `backend.tfbackend`, and verify the `lambda_runtime` value is a real, currently-supported AWS Lambda runtime.

## 12. Known Issues & Limitations

- **No authorization on any API Gateway route** (`authorization = "NONE"` hardcoded in the api-gateway module) — the entire API is open to anyone who has the invoke URL. This is the most significant infrastructure-level gap; see `CODE_MANIFEST.md` §9 for the corresponding application-layer note.
- **nprd and prod environments are non-functional as scaffolded** — all `.tfvars` and `.tfbackend` values are commented out (§5).
- **No state locking mechanism configured** — concurrent applies against the same environment are unprotected (§6).
- **Runtime version mismatch**: `python3.14` (dev override) vs `python3.12` (root default) vs. `bootstrap`'s AWS provider `~> 5.0` vs root's `~> 6.54.0` — these inconsistencies suggest the two Terraform roots (`terraform/` and `terraform/bootstrap/`) and the environment overrides have drifted from each other over time.
- **No root-level Terraform outputs** exposing the API Gateway invoke URL, Lambda ARNs, or DynamoDB table name for easy post-apply retrieval — everything is buried in module outputs with no root `outputs.tf` surfacing them.
- **`ec2:CreateVpc`/`ec2:CreateSubnet`/`ec2:DescribeVpcs`/`ec2:DescribeSubnets` IAM actions use `resources = ["*"]`** (`terraform/iam.tf`) — required by AWS (these EC2 actions don't support resource-level permissions before the resource exists), but worth documenting explicitly as an accepted risk since it means the Lambda execution roles can create/describe VPCs and subnets account-wide, not scoped to resources this platform created. Delete actions *are* scoped via the managed-tag condition, which is the actual safety boundary in practice.
- **Ordering constraint**: deleting a VPC that still has subnets attached will fail at the AWS API level (dependency violation) — not enforced or surfaced clearly by Terraform or the application; see `CODE_MANIFEST.md` for how this surfaces as an unhandled exception in the delete handler.
- **`tf-validate` is noted as broken** directly in `terraform/Makefile:48` (`# DOES NOT WORK PROPERLY`) — no explanation of why; worth investigating before relying on it in any future CI setup.

## 13. Disaster Recovery

- **Backup strategy**: S3 versioning on the state bucket is the only backup mechanism for Terraform state. DynamoDB has no point-in-time recovery or on-demand backups configured — **table data loss (accidental delete, corrupted write) is not recoverable** as currently provisioned.
- **RTO/RPO**: not formally defined anywhere in the repo. Given the entire stack is defined in Terraform and rebuildable from `terraform apply` within minutes, infrastructure RTO is low — but DynamoDB *data* (tracked VPC/subnet records) has no backup, so data RPO is effectively "whatever was written since the last successful state, with no way to restore lost items" if the table were ever deleted or corrupted.
- **Recovery steps**: re-run `terraform apply` to recreate infrastructure from code; DynamoDB data cannot be recovered without backups — this is a gap worth closing (enable `point_in_time_recovery` in the `dynamodb` module) before this platform manages anything beyond dev/test data.
