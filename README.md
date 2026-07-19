# aws-vpc-assignment-api-platform (VPC & Subnet Management API)

A serverless API for managing AWS VPCs and subnets, built on API Gateway, Lambda, and DynamoDB. Every VPC/subnet created through this API is provisioned in real AWS and tracked in a DynamoDB table for fast lookups.

## Architecture

- **API Gateway** — routes HTTP requests to the appropriate Lambda
- **Lambda (2 functions)** — one handles VPC routes, one handles subnet routes
- **DynamoDB (single table)** — stores records of every managed VPC and subnet
  - `PK = VPC#{vpc_id}`, `SK = VPC#{vpc_id}` for VPCs
  - `PK = VPC#{vpc_id}`, `SK = SUBNET#{subnet_id}` for subnets (nested under their VPC)
  - `gsi_type` — list all resources of a given type (e.g. all subnets)
  - `gsi_reverse` — look up a subnet by its own ID, without knowing its parent VPC

Each request both calls AWS (via boto3) to create/modify the real resource, and updates DynamoDB to keep a record of it.

## Endpoints

### VPCs
| Method | Path |
|---|---|
| GET | `/vpcs` |
| POST | `/vpcs` |
| GET | `/vpcs/{vpc_id}` |
| PUT | `/vpcs/{vpc_id}` |
| DELETE | `/vpcs/{vpc_id}` |

### Subnets
| Method | Path |
|---|---|
| GET | `/subnets` |
| GET | `/subnets/{subnet_id}` |
| PUT | `/subnets/{subnet_id}` |
| DELETE | `/subnets/{subnet_id}` |
| GET | `/vpcs/{vpc_id}/subnets` |
| POST | `/vpcs/{vpc_id}/subnets` |

## Project Structure

```
src/
  controllers/
    lambda_vpc_handler.py       # VPC Lambda entry point + routing
    lambda_subnet_handler.py    # Subnet Lambda entry point + routing
    aws_vpc_controller.py       # VPC route handlers
    aws_subnet_controller.py    # Subnet route handlers
    services/
      dynamodb/                 # DynamoDB read/write logic
      boto_ec2/                 # AWS EC2 API calls
  models/                       # Dataclasses representing DynamoDB records
  schema/                       # Pydantic request/response validation
```

## Notes

- Some fields are immutable once created (e.g. `cidr_block`) and can't be updated via `PUT` — matching real AWS behavior, where changing a CIDR means deleting and recreating the resource.
- Deleting a VPC that still has subnets in it will fail at the AWS level (dependency violation), since subnets must be deleted first.