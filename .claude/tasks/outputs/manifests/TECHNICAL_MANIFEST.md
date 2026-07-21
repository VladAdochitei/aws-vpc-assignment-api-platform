# Technical Manifest: AWS VPC Assignment API Platform

## High-Level Architecture

The project follows a **Lambda-based serverless API** architecture with a clear separation of concerns:

```
API Gateway (HTTP routing)
  ↓
Lambda Functions (handlers)
  ↓
Controllers (business logic orchestration)
  ↓
Services Layer (split into two concerns)
  ├─ boto_ec2/ (AWS resource provisioning)
  └─ dynamodb/ (persistent state tracking)
```

## Directory Structure

```
src/
├── lambda_vpc_handler.py         # VPC Lambda entry point (routes HTTP requests)
├── lambda_subnet_handler.py      # Subnet Lambda entry point
├── lambda_handlers.py            # Legacy hello-world handler
├── controllers/
│   ├── aws_vpc_controller.py     # VPC request handlers (list, create, get, update, delete)
│   ├── aws_subnet_controller.py  # Subnet request handlers
│   └── services/
│       ├── boto_ec2/
│       │   ├── base_ec2.py       # AWS EC2 client initialization & tagging utilities
│       │   ├── vpc_ec2.py        # AWS VPC API calls (create, describe, delete, tag)
│       │   └── subnet_ec2.py     # AWS subnet API calls
│       └── dynamodb/
│           ├── base_dynamodb.py  # DynamoDB table access & query logic
│           ├── vpc_dynamodb.py   # VPC CRUD operations in DynamoDB
│           └── subnet_dynamodb.py # Subnet CRUD operations in DynamoDB
├── models/
│   ├── base.py                   # Base utilities for data models
│   ├── vpc_model.py              # VPC dataclass (maps to/from DynamoDB)
│   └── subnet_model.py           # Subnet dataclass
└── schema/
    ├── vpc.py                    # Pydantic request/response validation for VPCs
    └── subnet.py                 # Pydantic request/response validation for subnets

terraform/
├── modules/
│   ├── api-gateway/              # API Gateway + routes
│   ├── dynamodb/                 # DynamoDB table definition
│   └── lambda/                   # Lambda functions + IAM roles
├── main.tf                        # Orchestrates modules
├── iam.tf                         # IAM roles & policies
├── providers.tf                   # AWS provider config
└── bootstrap/                     # One-time setup (S3 for state, etc.)
```

## Data Flow Example: Creating a VPC

1. **API Gateway** receives `POST /vpcs` with JSON body
2. **Lambda Handler** (`lambda_vpc_handler.py`) deserializes the request
3. **Controller** (`aws_vpc_controller.py:create_vpc_handler`) is invoked:
   - Validates input with Pydantic schema (`VPCCreateRequest`)
   - Calls `boto_ec2.vpc_ec2.create_vpc()` → creates real AWS VPC, returns AWS VPC ID
   - Calls `dynamodb.vpc_dynamodb.create_vpc()` → stores record in DynamoDB
   - Serializes response with Pydantic schema (`VPCResponse`)
4. **Response** is returned as JSON with HTTP status code

### Why the Two-Tier Service Layer?
- **boto_ec2**: Calls AWS APIs to provision real infrastructure (authoritative source of truth for existence)
- **dynamodb**: Tracks all created resources in a fast, queryable index for the API (audit trail + quick lookups)

Both must succeed or the operation is considered failed. If AWS succeeds but DynamoDB fails, the VPC exists but isn't tracked.

## Core Architectural Patterns

### 1. Handler Pattern (Lambda Functions)
Each Lambda has an entry point that routes incoming requests based on HTTP method and path parameters.

### 2. Model → DynamoDB Mapping
Models are dataclasses with serialization methods:
- `to_dict()` — Python dict representation
- `to_dynamodb()` — Adds DynamoDB keys (PK, SK) and type marker
- `from_dynamodb()` — Reconstructs from DynamoDB item

### 3. Pydantic for Validation
Request/response contracts are enforced via Pydantic:
- `*CreateRequest` — validates incoming POST body
- `*Response` — validates outgoing JSON and enforces schema consistency
- `*ListResponse` — wraps lists with metadata

### 4. Service Isolation
Services are thin, focused modules:
- **boto_ec2 services**: Pure AWS API wrappers (one function per operation)
- **dynamodb services**: Pure DynamoDB wrappers (one function per operation)
- **No cross-service calls**: Controllers orchestrate; services don't talk to each other

## DynamoDB Table Design

Single-table design with composite keys:

| Partition Key (PK) | Sort Key (SK) | Usage |
|---|---|---|
| `VPC#{vpc_id}` | `VPC#{vpc_id}` | Store VPC record |
| `VPC#{vpc_id}` | `SUBNET#{subnet_id}` | Store subnet under parent VPC |

**Global Secondary Indexes (GSIs):**
- `gsi_type`: Query all resources of a type (e.g., all subnets)
- `gsi_reverse`: Look up subnet by ID alone (without parent VPC)

## API Endpoints (Implemented)

### VPCs
| Method | Path | Handler |
|---|---|---|
| POST | `/vpcs` | create_vpc_handler |
| GET | `/vpcs` | list_vpcs_handler |
| GET | `/vpcs/{vpc_id}` | get_vpc_handler |
| PUT | `/vpcs/{vpc_id}` | update_vpc_handler |
| DELETE | `/vpcs/{vpc_id}` | delete_vpc_handler |

### Subnets
| Method | Path | Handler |
|---|---|---|
| POST | `/vpcs/{vpc_id}/subnets` | create_subnet_handler |
| GET | `/vpcs/{vpc_id}/subnets` | list_subnets_by_vpc_handler |
| GET | `/subnets/{subnet_id}` | get_subnet_handler |
| PUT | `/subnets/{subnet_id}` | update_subnet_handler |
| DELETE | `/subnets/{subnet_id}` | delete_subnet_handler |

## Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Compute | AWS Lambda | Serverless, event-driven, scales automatically |
| API Routing | API Gateway | Managed HTTP endpoint, integrates with Lambda |
| Storage | DynamoDB | Fast, schema-less, no operational overhead |
| Infrastructure | Terraform | IaC, version-controlled, reproducible, modular |
| Validation | Pydantic | Type-safe, auto-generates schemas, excellent DX |
| AWS SDK | boto3 | Only official Python AWS library |
| Models | Dataclasses | Lightweight, standard library, minimal dependencies |

## Key Design Decisions

1. **Dual Writes (AWS + DynamoDB)**: Every resource creation triggers both AWS (real infrastructure) and DynamoDB (tracking). This ensures the API can list what it created without querying AWS repeatedly.

2. **Immutable Fields**: CIDR blocks are immutable (matching AWS reality). Updates only affect tags/metadata.

3. **No ORM**: Plain boto3 + dataclasses keep dependencies minimal and control explicit. This is a Lambda environment where cold-start latency matters.

4. **Single-Table DynamoDB**: Composite keys (`VPC#{id}`, `SUBNET#{id}`) nest subnets under VPCs hierarchically, reducing queries needed.

5. **Thin Lambda Handlers**: All routing and HTTP response formatting is delegated to handlers; business logic lives in controllers.

## Error Handling Strategy

- **Validation Errors (400)**: Pydantic validation fails → return validation details
- **Not Found (404)**: Resource doesn't exist in DynamoDB
- **Conflict (409)**: Resource already exists (uniqueness violation)
- **AWS Errors**: boto3 `ClientError` exceptions → logged, propagated as 500 or context-specific error code

## Infrastructure as Code (Terraform)

**Modular structure** with clear separation:
- **api-gateway module**: API Gateway configuration, routes, integrations
- **dynamodb module**: Table definition, indexes, capacity settings
- **lambda module**: Function packages, IAM roles, environment variables
- **iam.tf**: Cross-cutting IAM policies (Lambda execution roles, service permissions)
- **main.tf**: Orchestrates modules together
- **bootstrap/**: One-time setup (remote state S3 bucket, etc.)

Each module is self-contained with clear inputs (`variables.tf`) and outputs (`outputs.tf`).

## Development Notes

- **Cold Start**: Lambda cold starts are minimized by avoiding heavy dependencies; boto3 and Pydantic are pre-installed in Lambda runtimes or lightweight enough.
- **Local Testing**: Use `sam local start-api` or invoke handlers directly with test events.
- **Deployment**: Terraform manages all infrastructure; code is packaged and deployed as part of Lambda module build.
- **Monitoring**: CloudWatch logs for all Lambda invocations; consider adding X-Ray for distributed tracing.

