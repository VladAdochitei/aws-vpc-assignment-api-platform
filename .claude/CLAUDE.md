# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS VPC Assignment API Platform - A Python API service for programmatically creating and managing AWS VPC resources with multiple subnets. The API includes authentication, persistence, and infrastructure-as-code (Terraform) for deployment.

**Key Requirements:**
- REST API in Python for VPC/subnet creation and retrieval
- Authentication layer (all authenticated users authorized)
- AWS integration for resource creation
- Store and retrieve created resource data
- Infrastructure automation via Terraform

## Development Approach

- **Simplicity over efficiency:** Write clear, maintainable code that's easy to recall and modify. Prefer straightforward solutions over clever optimizations.
- **Incremental evolution:** Guide feature development step-by-step. Do not design speculatively for future needs.
- **Python stack:** All backend systems use Python.

## Repository Structure

```
.claude/          - Claude Code configuration
  memory/         - Claude code memory for this project
docs/             - Planning and documentation
  planning-board/ - Problem statement and requirements
  documentation/  - User guides and operator manuals
src/              - Python application code (TBD)
terraform/        - Infrastructure-as-code for AWS deployment
```

## Development Commands

*(To be established once project structure is defined)*

When setting up the project:
- Linting: `pytest --linter` or equivalent
- Tests: `pytest` or `pytest tests/test_module.py` for single test file
- API server: `python -m app.main` or similar (command TBD)
- Format: Black or similar code formatter (TBD)

## Technology Stack

- **Language:** Python (all backend systems)
- **Compute:** AWS Lambda (serverless functions)
- **API Gateway:** AWS API Gateway (REST API triggers)
- **Storage:** S3 (object/file storage)
- **Database:** SQL database (engine TBD — likely PostgreSQL)
- **IaC:** Terraform (modular, easy to understand)

## Database Schema

### VPC Table
```sql
CREATE TABLE vpcs (
  id SERIAL PRIMARY KEY,
  vpc_id VARCHAR(255) UNIQUE NOT NULL,      -- AWS VPC ID (vpc-xxx)
  vpc_name VARCHAR(255) NOT NULL,            -- User-friendly name
  cidr_block VARCHAR(18) NOT NULL,           -- e.g., 10.0.0.0/16
  region VARCHAR(50) NOT NULL,               -- AWS region (eu-west-1)
  created_by VARCHAR(255),                   -- API key or user who created it
  created_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'active'        -- active, pending, deleted
);
```

### Subnet Table
```sql
CREATE TABLE subnets (
  id SERIAL PRIMARY KEY,
  subnet_id VARCHAR(255) UNIQUE NOT NULL,    -- AWS subnet ID (subnet-xxx)
  vpc_id VARCHAR(255) NOT NULL,              -- Foreign key to vpcs table
  subnet_name VARCHAR(255) NOT NULL,
  cidr_block VARCHAR(18) NOT NULL,           -- e.g., 10.0.1.0/24
  availability_zone VARCHAR(50),             -- e.g., eu-west-1a
  created_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'active',
  FOREIGN KEY (vpc_id) REFERENCES vpcs(vpc_id) ON DELETE CASCADE
);
```

Design approach: Use soft deletes via status field, audit trail with created_by, proper foreign keys with cascade delete.

## Architecture (TBD)

As the project develops, document here:
- Lambda function organization and handlers
- API endpoints and request/response schemas
- Authentication mechanism (all authenticated users authorized)
- AWS service interactions (EC2, VPC APIs)
- S3 usage patterns
- Terraform module organization

## Notes for Future Work

- Keep database schema simple and explicit
- Make API endpoints straightforward and predictable
- Document authentication flow clearly
- Terraform should be modular and easy to understand
- See /memory/ directory for persistent project context and patterns
