# Task: Generate Project Context & Technical Manifest

## Purpose

Generate dual-layer documentation that enables context transfer to future conversations or AI sessions: (1) an eloquent, high-level summary for quick understanding, and (2) a technical manifest that captures code structure, architecture, and design decisions.

## Inputs

- A working git repository with application code (Python, Go, etc.), infrastructure-as-code (Terraform, CloudFormation), and documentation
- Project instructions or CLAUDE.md file describing goals, stack, and database schema
- Recent git history showing what has been built

## Outputs

1. **Eloquent Summary** (for sharing context in other conversations)
   - Purpose: High-level, compelling description of what the project does
   - Audience: Decision-makers, new team members, AI sessions picking up work
   - Style: Professional, clear, emphasizes business value and current state
   - Content: What it is, technical foundation, current implementation status, immediate objectives

2. **Technical Manifest** (stored as `.claude/tasks/outputs/manifests/TECHNICAL_MANIFEST.md`)
   - Purpose: Architecture reference and code organization guide
   - Audience: Developers, code reviewers, future AI sessions
   - Content:
     - High-level architecture diagram (text)
     - Directory structure with file purposes
     - Data flow examples (e.g., "Creating a VPC")
     - Core architectural patterns (handlers, models, validation, service isolation)
     - Database schema and table design
     - API endpoints (complete list)
     - Technology stack with rationale
     - Key design decisions and tradeoffs
     - Error handling strategy
     - IaC structure (Terraform modules)
     - Development notes and gotchas

## Process

### Phase 1: Explore the Codebase
- Read CLAUDE.md and README files to understand the project's stated goals
- List all source files to understand structure
- Check git log for recent commits and momentum
- Identify the primary language(s) and framework(s)

### Phase 2: Map Architecture
- Identify entry points (Lambdas, CLI mains, server startup)
- Trace one happy-path request through the code (e.g., "create VPC")
- Document how layers communicate (HTTP → handler → controller → services → data)
- Note where AWS/external APIs are called
- Understand data model (databases, caches, files)

### Phase 3: Extract Design Patterns
- Identify repeated structures (e.g., "every controller wraps boto3 calls")
- Document validation/serialization approach
- Note error handling patterns
- Capture naming conventions and code organization philosophy

### Phase 4: Generate Summaries
- **Eloquent Summary**: Write 3–4 paragraphs covering project vision, foundation, current state, and near-term objectives. Use clear language, avoid jargon where possible, emphasize impact.
- **Technical Manifest**: Organize findings into structured sections (architecture, directory tree, data flows, patterns, stack, decisions). Use tables and code blocks for clarity.

### Phase 5: Deliver
- Present eloquent summary to user for sharing with other sessions
- Write TECHNICAL_MANIFEST.md to repo root
- (Optional) Create a reusable task prompt for future projects

## Quality Checklist

- [ ] Eloquent summary is 3–4 sentences per section and reads smoothly
- [ ] Technical manifest includes actual file names and paths from the repo
- [ ] Architecture diagram (text) is clear and fits in <200 chars per line
- [ ] One data-flow example is walked through end-to-end
- [ ] All endpoint routes are documented
- [ ] Design decisions include tradeoffs (why this choice over alternatives)
- [ ] Technology stack includes rationale for each choice
- [ ] Manifest is stored at repo root and linked in README (if needed)
- [ ] Summaries are stored (manifest) or delivered (eloquent) and ready to share

## Example Outputs

**Eloquent Summary** (excerpt):
> "AWS VPC Assignment API Platform is a Python-based REST API service for provisioning AWS Virtual Private Cloud infrastructure with sophisticated subnet orchestration. Users can create, retrieve, and manage VPC environments through a clean, RESTful interface with authenticated access..."

**Technical Manifest** (excerpt):
> ```
> API Gateway (HTTP routing)
>   ↓
> Lambda Functions (handlers)
>   ↓
> Controllers (business logic orchestration)
>   ↓
> Services Layer (boto_ec2 + dynamodb)
> ```

## Reusability

This task is language-agnostic and works for any architecture:
- **Backend APIs** (REST, GraphQL, gRPC)
- **Infrastructure** (Terraform, CloudFormation, Pulumi)
- **Full-stack apps** (frontend + backend + infra)
- **Libraries** (packages, SDKs, utilities)
- **Microservices** (multiple services, event buses)

Adapt the "tracing one request" step to match your architecture (e.g., message queue for async, CLI parsing for CLI tools, component render for React apps).

