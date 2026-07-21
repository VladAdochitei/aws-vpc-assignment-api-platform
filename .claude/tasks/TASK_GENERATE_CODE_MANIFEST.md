# Task: Generate Code Manifest

## Purpose

Create a granular, developer-focused reference document detailing code organization, patterns, dependencies, and implementation specifics. This goes **deeper than the high-level Technical Manifest** — it's a guide for developers modifying, extending, or debugging the codebase.

## Inputs

- Working repository with application source code
- Package/dependency files (requirements.txt, package.json, Pipfile, go.mod, etc.)
- Test files and test configuration
- Any existing code documentation (docstrings, inline comments, ADRs)
- Recent commits and pull requests

## Questions to Ask the User

Before diving in, gather context:

1. **Source Structure**
   - Are there any non-standard/hidden code folders I should know about? (e.g., vendor/, third_party/, generated/)
   - Do you have multiple language folders or is it all [Python/Go/TypeScript/etc.]?
   - Are there feature branches or experimental code I should skip?

2. **Dependencies & Constraints**
   - Are there any version pinning constraints or compatibility notes? (e.g., "must run on Python 3.9–3.11")
   - Any custom/internal libraries or vendored code I should treat differently?
   - Are there performance-sensitive modules or hot paths I should document?

3. **Testing & Quality**
   - What's the test structure? (unit/ integration/ e2e/, conftest patterns, fixtures, mocks)
   - Are there known flaky tests or coverage gaps?
   - Any linting/formatting rules or pre-commit hooks I should document?

4. **Code Patterns & Conventions**
   - Are there design patterns or abstractions I should highlight? (factories, singletons, middleware chains, decorators)
   - Any "gotchas" or non-obvious behaviors? (e.g., auto-initialization, lazy loading, mutation after creation)
   - Naming conventions or code style I should call out?

5. **External Integrations**
   - Which modules call external services/APIs? (AWS, databases, message queues, external APIs)
   - Are there retry logic, circuit breakers, or resilience patterns?
   - Any secrets/credentials management patterns?

## Outputs

**CODE_MANIFEST.md** (stored in `.claude/tasks/outputs/manifests/CODE_MANIFEST.md`) containing:

### 1. Dependency Map
- List of all top-level dependencies with versions and purpose
- Transitive dependency risks or conflicts (if any)
- Version constraints and compatibility matrix

### 2. Module Breakdown
For each significant code module/package:
- **Purpose**: What it does, why it exists
- **Public API**: Key functions/classes/exports (with signatures)
- **Dependencies**: What it imports and calls
- **Test Coverage**: Where tests live, coverage %, known gaps
- **Patterns**: Design patterns used (factory, decorator, singleton, etc.)
- **Gotchas**: Non-obvious behaviors, mutation, side effects

### 3. Code Flow Examples
- **Happy Path**: Walk through a primary feature end-to-end (with line numbers)
- **Error Paths**: Common error scenarios and how they're handled
- **Edge Cases**: Known tricky scenarios and how code handles them

### 4. Testing Strategy
- Test structure (unit/integration/e2e breakdown)
- How to run tests locally
- Test utilities, fixtures, factories
- Mocking/stubbing patterns
- CI test configuration

### 5. Performance & Scalability
- Hot paths (performance-sensitive code)
- Caching strategies
- Concurrency models (async/await, threads, goroutines, etc.)
- Known bottlenecks or TODOs

### 6. Code Style & Conventions
- Naming conventions (functions, variables, constants)
- Error handling patterns
- Logging approach
- Comment style (when, what, how much)
- Pre-commit hooks or linting rules

### 7. Common Tasks & Recipes
- "How to add a new endpoint" (if REST API)
- "How to add a new model" (if ORM)
- "How to add a new service" (if microservices)
- Debugging tips and tricks
- Common mistakes to avoid

### 8. Dependency Injection & Configuration
- How environment variables are loaded
- How services/clients are initialized
- How dependencies are passed around (constructor injection, DI container, globals, etc.)

### 9. Known Limitations & Tech Debt
- Areas marked for refactoring
- Performance optimizations still needed
- Security considerations or warnings
- Deprecated patterns or modules

## Process

### Phase 1: Gather Context
- Ask user the questions above
- Document their answers
- Identify primary language(s) and frameworks

### Phase 2: Map Code Structure
- List all top-level modules/packages
- Build a dependency graph (which module calls which)
- Identify entry points (main, __init__, handler functions)

### Phase 3: Deep-Dive Each Module
- Read public API (function signatures, exports)
- Trace 2–3 code flows through the module
- Identify patterns (is it a repository? a factory? a service handler?)
- Locate and review tests for the module
- Note any TODOs, FIXMEs, or deprecated code

### Phase 4: Extract Patterns & Conventions
- Identify repeating structures (every service has X, every handler does Y)
- Document naming conventions
- Capture error handling approach
- Note logging patterns

### Phase 5: Walk Through Happy Path & Error Cases
- Pick a primary feature (e.g., "create VPC")
- Trace from entry point to persistence, noting line numbers
- Trace an error case (validation failure, AWS timeout, etc.)
- Document edge cases (concurrency, retries, idempotence)

### Phase 6: Generate Code Manifest
- Organize findings into the output structure above
- Use actual code excerpts (line numbers) as examples
- Include real file paths
- Add recipes for common tasks

### Phase 7: Validate & Deliver
- Cross-check against actual code (spot-check a few claims)
- Confirm it's useful for a developer picking up the code
- Deliver as CODE_MANIFEST.md

## Quality Checklist

- [ ] All top-level modules are documented with purpose and public API
- [ ] Dependency graph shows which modules call which (can be text or ASCII diagram)
- [ ] One happy-path example is walked through with actual line numbers
- [ ] One error-path example is documented (how errors are caught, logged, returned)
- [ ] Test structure is clear (unit vs. integration, where fixtures live, how to run locally)
- [ ] Naming conventions are explicit (function_names vs. FunctionNames, CONSTANT_NAMES, _private_vars)
- [ ] Performance hot paths are identified and marked
- [ ] At least 3 "common tasks" recipes included (step-by-step with file names)
- [ ] Known tech debt or limitations are listed with context
- [ ] File paths and line numbers are accurate (spot-checked against repo)
- [ ] Gotchas and non-obvious behaviors are highlighted with warnings

## Example Outputs

**Dependency Map** (excerpt):
```
boto3 (AWS SDK)
  → Used by: controllers/services/boto_ec2/
  → Purpose: Provision real AWS VPCs and subnets
  → Constraint: v1.26+, pre-installed in Lambda runtime

pydantic (validation)
  → Used by: schema/*, models/*
  → Purpose: Request/response validation and serialization
  → Constraint: v2.0+, lightweight, minimal overhead
```

**Module Breakdown** (excerpt):
```
## controllers/services/dynamodb/vpc_dynamodb.py

**Purpose**: CRUD operations on VPC records in DynamoDB

**Public API**:
- create_vpc(vpc_id, vpc_name, cidr_block, region, created_by=None) → VPC
- get_vpc(vpc_id) → VPC | None
- list_vpcs() → list[VPC]
- update_vpc(vpc_id, **fields) → VPC | None
- delete_vpc(vpc_id) → None

**Dependencies**:
- models.vpc_model.VPC (data structure)
- controllers.services.dynamodb.base_dynamodb (table access)

**Patterns**: Repository pattern — all DynamoDB access is wrapped by this module

**Tests**: tests/services/test_vpc_dynamodb.py (8 tests, 95% coverage)

**Gotchas**:
- update_vpc() filters out None values, so you can't explicitly set a field to null
- from_dynamodb() reconstructs VPC from raw item; caller is responsible for catching KeyError
```

**Common Task Recipe** (excerpt):
```
## How to Add a New VPC Field

1. Update model: `src/models/vpc_model.py`
   - Add field to @dataclass VPC (line 6–14)
   - Update to_dynamodb() if field needs special handling

2. Update schema: `src/schema/vpc.py`
   - Add field to VPCResponse (line 20–27)
   - Add field to VPCCreateRequest if user can set it (line 7–10)
   - Mark as Optional[type] if nullable

3. Update service: `src/controllers/services/dynamodb/vpc_dynamodb.py`
   - No change needed if using **fields pattern (line 26–31)

4. Update handler: `src/lambda_vpc_handler.py`
   - No change needed if handler uses controller (line 19)

5. Add tests: `tests/services/test_vpc_dynamodb.py`
   - Test create_vpc with new field
   - Test update_vpc setting/clearing new field
```

## Reusability

This task works for any codebase:
- **Monoliths** (one large service)
- **Microservices** (adapt to per-service manifest)
- **Libraries** (export API, usage patterns)
- **CLIs** (command structure, plugins)
- **Backends** (REST, GraphQL, gRPC)
- **Frontends** (component hierarchy, state management, routing)

Adjust Phase 5 (happy path) to match your architecture (e.g., message flow for async, command dispatch for CLIs, component render tree for UI).

