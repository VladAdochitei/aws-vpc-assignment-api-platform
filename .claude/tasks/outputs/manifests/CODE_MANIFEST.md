# Code Manifest: AWS VPC Assignment API Platform

_Last verified: 2026-07-21_

Granular, developer-focused reference for the Python application in `src/`. For high-level architecture, see `TECHNICAL_MANIFEST.md`. For infrastructure, see `TERRAFORM_MANIFEST.md`.

## 1. Dependency Map

`requirements.txt` (2 lines, no version pins):

```
pydantic (validation)
  → Used by: schema/vpc.py, schema/subnet.py
  → Purpose: Request/response validation and serialization for the API
  → Constraint: unpinned — v2 API used (model_validate_json, model_dump, Config.from_attributes)

boto3 (AWS SDK)
  → Used by: controllers/services/boto_ec2/*, controllers/services/dynamodb/*, models/base.py
  → Purpose: Talks to real EC2 (VPC/subnet provisioning) and DynamoDB (tracking table)
  → Constraint: unpinned — relies on whatever version `make build` resolves via pip
```

No test framework, linter, or formatter is declared anywhere (no `pytest`, no `black`, no `ruff` in requirements or config). `Makefile` (root) only builds the Lambda deployment package — it does not run tests or lint.

**Risk**: unpinned dependencies mean `make build` can pull a different boto3/pydantic minor version on each build, with no lockfile to reproduce a prior build.

## 2. Module Breakdown

### `src/lambda_vpc_handler.py` / `src/lambda_subnet_handler.py`

**Purpose**: Lambda entry points. Each is a tiny router mapping `(httpMethod, resource)` → a handler function.

**Public API**:
- `api_handler(event, context)` — dispatch function, used as the Terraform `handler` value (`lambda_vpc_handler.api_handler`, `lambda_subnet_handler.api_handler`)

**Dependencies**: imports handler functions directly from `controllers/aws_vpc_controller.py` and `controllers/aws_subnet_controller.py`.

**Gotchas**:
- The `ROUTES` dict keys must exactly match API Gateway's `resource` field (e.g. `"/vpcs/{vpc_id}"`), which itself must exactly match the `path` list built in `terraform/main.tf`'s `routes` map — these three places (Lambda router, Terraform routes, API Gateway resource tree) have no shared source of truth and can silently drift.
- Unmatched routes return a raw dict (404), not routed through the `_response()` helper used everywhere else — so it lacks the same header shape consistency (harmless in practice since API Gateway proxy integration doesn't care, but inconsistent).

### `src/lambda_handlers.py`

**Purpose**: Legacy/example "hello world" handler, unrelated to VPC/subnet logic. Not wired into any current Terraform module (`main.tf` only creates `vpc_lambda` and `subnet_lambda`).

**Gotchas**: `variables.tf`'s `lambda_handler` variable still defaults to `"lambda_handlers.api_handler"` but this variable is unused in `main.tf` — dead variable pointing at dead code.

### `src/controllers/aws_vpc_controller.py`

**Purpose**: Despite the name, this **is** the handler layer for VPC routes (not a separate "controller" invoked by a thin handler) — it orchestrates validation → AWS call → DynamoDB write → response serialization in one place.

**Public API**:
- `list_vpcs_handler(event)` → 200 with `VPCListResponse`
- `create_vpc_handler(event)` → 201 with `VPCResponse`, or 400 on validation error
- `get_vpc_handler(event)` → 200 with `VPCResponse`, or 404
- `update_vpc_handler(event)` → 200 with `VPCResponse`, or 400/404
- `delete_vpc_handler(event)` → 200 with `{vpc_id, message}`, or 404

**Dependencies**: `schema.vpc`, `controllers.services.dynamodb.vpc_dynamodb`, `controllers.services.boto_ec2.vpc_ec2`.

**Patterns**: dual-write orchestration (AWS first, then DynamoDB); Pydantic try/except for 400s; `botocore.exceptions.ClientError` inspected for `ConditionalCheckFailedException` to detect "not found" on update/delete.

**Tests**: none exist (`tests/` directory does not exist in the repo).

**Gotchas**:
- `create_vpc_handler` (line 25-26): calls `vpc_ec2.create_vpc()` first, then `vpc_dynamodb.create_vpc()`. If the DynamoDB write fails after the AWS call succeeds, the VPC exists in AWS but is **not tracked** — no rollback/compensation logic exists.
- `update_vpc_handler` (line 53-54): only propagates `vpc_name` changes back to AWS tags; `region`/`status` updates are DynamoDB-only bookkeeping fields that don't correspond to a real mutable AWS property.
- `delete_vpc_handler` (line 68): the 204 no-content response is commented out in favor of 200 with a body — intentional but worth knowing if a client expects strict REST semantics.
- No ordering/cascade protection: deleting a VPC that still has subnet records in DynamoDB will succeed in DynamoDB even though AWS will reject the underlying `DeleteVpc` call due to a dependency violation (subnets attached) — the AWS `ClientError` will propagate as an unhandled 500 in that case, but the DynamoDB VPC record is deleted anyway on line 63 *only if* the AWS call didn't raise first (order is EC2 delete → then DynamoDB delete, so actually failure order is fine: if AWS delete_vpc fails, exception propagates before `vpc_dynamodb.delete_vpc` runs — no orphaned state here, self-correcting via the try/except at the handler level, though the exception is re-raised as 500, not a clean 409/424).

### `src/controllers/aws_subnet_controller.py`

**Purpose**: Same handler-not-controller pattern as VPC, for subnet routes.

**Public API**:
- `list_subnets_handler(event)`, `list_subnets_by_vpc_handler(event)`, `create_subnet_handler(event)`, `get_subnet_handler(event)`, `update_subnet_handler(event)`, `delete_subnet_handler(event)`

**Dependencies**: `schema.subnet`, `controllers.services.dynamodb.{subnet_dynamodb,vpc_dynamodb}`, `controllers.services.boto_ec2.subnet_ec2`.

**Gotchas**:
- `create_subnet_handler` and `list_subnets_by_vpc_handler` both call `vpc_dynamodb.get_vpc(vpc_id)` to check the parent VPC exists before proceeding — this is the only cross-entity validation in the codebase, and it's duplicated inline rather than factored into a shared helper.
- `delete_subnet_handler` order is DynamoDB delete → then AWS delete (line 81-85) — the **opposite** order from the VPC controller. If the AWS `delete_subnet` call fails after the DynamoDB record is already gone, the subnet record disappears from tracking while the real AWS subnet still exists — an orphan in the *opposite* direction from the VPC case. This inconsistency between the two controllers is worth fixing if strict consistency matters.

### `src/controllers/services/boto_ec2/base_ec2.py`

**Purpose**: Shared EC2 client + tagging helper.

**Public API**:
- `client()` → shared `boto3.client("ec2")` singleton (module-level, created once per Lambda cold start)
- `build_tags(name, extra=None)` → list of AWS tag dicts, always injects `Name` and the managed marker `vpc-assignment-platform:managed = "true"`

**Gotchas**: `MANAGED_TAG_KEY` here (`vpc-assignment-platform:managed`) is duplicated as a raw string literal in `terraform/iam.tf`'s IAM condition (`ec2:ResourceTag/vpc-assignment-platform:managed`). If this constant is ever renamed in Python, the Terraform IAM policy must be updated to match, or delete permissions silently break (deny, not error — `DeleteVpc`/`DeleteSubnet` calls would fail with an `UnauthorizedOperation` AWS error since the tag condition would no longer match).

### `src/controllers/services/boto_ec2/vpc_ec2.py` / `subnet_ec2.py`

**Purpose**: Thin one-function-per-operation wrappers around EC2 API calls (`create_vpc`, `describe_vpc`, `delete_vpc`, `update_vpc_name`, and subnet equivalents).

**Patterns**: pure passthrough functions, no error handling — `botocore.exceptions.ClientError` propagates up to the controller/handler layer.

**Gotchas**: `vpc_ec2.update_vpc_name` docstring-style comment notes VPCs can't have their CIDR modified in AWS — must delete/recreate. `describe_vpc` in `vpc_ec2.py` is defined but never called anywhere in the codebase (dead code, likely intended for future drift-detection).

### `src/controllers/services/dynamodb/base_dynamodb.py`

**Purpose**: Low-level DynamoDB table access — all query/put/update/delete operations funnel through this module.

**Public API**:
- `put_item(item)`, `get_item(key)`, `query_by_type(entity_type)`, `update_item(key, fields)`, `delete_item(key)`, `query_by_pk(pk, sk_prefix=None)`, `query_by_sk(sk)`

**Dependencies**: reads `TABLE_NAME` env var at **import time** (`os.environ["TABLE_NAME"]`, line 5) — will raise `KeyError` at Lambda cold start if unset, rather than a clear runtime error at first use.

**Patterns**: `update_item`/`delete_item` both use `ConditionExpression="attribute_exists(PK)"` so updates/deletes on a missing item raise `ClientError` with code `ConditionalCheckFailedException` — this is the mechanism the VPC controller catches to return 404.

**Gotchas**: `query_by_type` and `query_by_sk` use GSIs (`gsi_type`, `gsi_reverse`) that must exist exactly as named in `terraform/main.tf`'s `module.resources_table.global_secondary_indexes` — another cross-layer name coupling with no shared constant.

### `src/controllers/services/dynamodb/vpc_dynamodb.py` / `subnet_dynamodb.py`

**Purpose**: Entity-specific repository functions wrapping `base_dynamodb`.

**Public API** (vpc_dynamodb): `create_vpc(...)`, `get_vpc(vpc_id)`, `list_vpcs()`, `update_vpc(vpc_id, **fields)`, `delete_vpc(vpc_id)`
**Public API** (subnet_dynamodb): `create_subnet(...)`, `get_subnet(subnet_id)`, `list_subnets()`, `list_subnets_by_vpc(vpc_id)`, `update_subnet(subnet_id, **fields)`, `delete_subnet(subnet_id) -> bool`

**Patterns**: Repository pattern — all item shaping/keying is delegated to the dataclass models (`VPC.key()`, `Subnet.key()`).

**Gotchas**:
- `subnet_dynamodb._find_by_subnet_id` (line 19-21) does a GSI query (`gsi_reverse`) just to resolve a subnet's parent `VPC#{vpc_id}` PK before it can update/delete — every subnet mutation costs 2 DynamoDB requests (1 GSI query + 1 write) instead of 1, because the public API only takes `subnet_id` without the parent `vpc_id`.
- `update_vpc`/`update_subnet` both filter out `None` values from `**fields` (line 27 in vpc_dynamodb.py, line 38 in subnet_dynamodb.py) — **you cannot explicitly null out a field** via the update API; a `None` in the request body is silently dropped rather than clearing the field.
- `vpc_dynamodb.delete_vpc` (line 34-36) doesn't check whether the item existed first and always returns `None` — the handler relies on `ConditionalCheckFailedException` bubbling up from `base_dynamodb.delete_item`, whereas `subnet_dynamodb.delete_subnet` (line 48-53) does an existence check and returns a `bool` instead of relying on the exception. Two different "not found" idioms for structurally identical operations.

### `src/models/vpc_model.py` / `subnet_model.py`

**Purpose**: Plain `@dataclass` models mapping directly to DynamoDB items — no ORM.

**Public API**:
- `VPC(vpc_id, vpc_name, cidr_block, region, created_by=None, created_at=<utc now>, status="active")`
- `Subnet(subnet_id, vpc_id, subnet_name, cidr_block, availability_zone=None, created_by=None, created_at=<utc now>, status="active")`
- Both expose: `.key()` (DynamoDB PK/SK dict), `.to_dict()`, `.to_dynamodb()`, `.from_dynamodb(item)` (classmethod)

**Patterns**: `from_dynamodb` filters incoming dict keys against `cls.__dataclass_fields__`, so extra DynamoDB attributes (like `PK`, `SK`, `entity_type`) are silently dropped during reconstruction — this is what lets `to_dynamodb()` freely add those keys without `from_dynamodb()` choking on them.

**Gotchas**: `created_at` defaults via `field(default_factory=...)` to `datetime.now(timezone.utc).isoformat()` — this runs **once per model instantiation**, meaning it's only ever set on `create_*`, never touched again; there is no `updated_at` field anywhere, so DynamoDB update timestamps aren't tracked at all.

### `src/models/base.py`

**Purpose**: Defines `get_table()` — a DynamoDB table accessor with its own `boto3.resource` client.

**Dead code**: not imported or called anywhere in the codebase (verified via grep). `base_dynamodb.py` duplicates this exact pattern independently (its own `boto3.resource("dynamodb")` + `_table` at line 4-5). Safe to delete `models/base.py`, or the intent may have been for `base_dynamodb.py` to use it instead of duplicating.

### `src/schema/vpc.py` / `subnet.py`

**Purpose**: Pydantic v2 request/response contracts — the "view" layer per `src/MVC.md`'s explicit MVC mapping note (worth reading; it documents *why* there's no `views/` folder).

**Public API** (vpc.py): `VPCCreateRequest`, `VPCUpdateRequest`, `VPCResponse`, `VPCListResponse`
**Public API** (subnet.py): `SubnetCreateRequest`, `SubnetUpdateRequest`, `SubnetResponse`, `SubnetListResponse`

**Patterns**: `*CreateRequest` omits server-assigned fields (`vpc_id`/`subnet_id`, `created_by`, `created_at`, `status`); `*UpdateRequest` omits immutable fields (`cidr_block`, and for subnets also `availability_zone`) with an inline comment explaining why (AWS immutability); `*Response` uses `Config.from_attributes = True` intending `model_validate(obj)` on an object with attributes, but every call site in the controllers actually passes `.to_dict()` (a plain dict) — `from_attributes` is therefore unused/vestigial since Pydantic validates dicts natively regardless of that config flag.

**Gotchas**: no `created_by` is ever actually populated by any handler — `VPCCreateRequest`/`SubnetCreateRequest` don't accept it as input, and no handler derives it from an authenticated identity (see Known Limitations — there is no authentication layer at all currently).

## 3. Code Flow Examples

### Happy Path: `POST /vpcs` → create a VPC

1. API Gateway invokes `vpc_lambda` → `lambda_vpc_handler.api_handler` (`src/lambda_vpc_handler.py:13`)
2. Router matches `("POST", "/vpcs")` → `create_vpc_handler` (`src/lambda_vpc_handler.py:7`, function defined in `src/controllers/aws_vpc_controller.py:19`)
3. `VPCCreateRequest.model_validate_json(event["body"])` (`aws_vpc_controller.py:21`) — raises `ValidationError` → caught, returns 400 with Pydantic's `.errors()`
4. `vpc_ec2.create_vpc(body.cidr_block, body.vpc_name)` (`aws_vpc_controller.py:25`) → real `ec2:CreateVpc` call via `base_ec2.client()`, tagged via `base_ec2.build_tags()`
5. `vpc_dynamodb.create_vpc(vpc_id=aws_vpc["VpcId"], **body.model_dump())` (`aws_vpc_controller.py:26`) — constructs a `VPC` dataclass, writes via `base_dynamodb.put_item(vpc.to_dynamodb())`
6. `VPCResponse.model_validate(vpc.to_dict()).model_dump(mode="json")` (`aws_vpc_controller.py:27`) — serializes to JSON-safe dict
7. `_response(201, ...)` wraps it in the API Gateway proxy-integration shape (`statusCode`, `headers`, `body`)

### Error Path: updating a non-existent VPC

1. `update_vpc_handler` (`aws_vpc_controller.py:37`) validates the body, then calls `vpc_dynamodb.update_vpc(vpc_id, **fields)`
2. `base_dynamodb.update_item` (`base_dynamodb.py:25-33`) issues `UpdateItem` with `ConditionExpression="attribute_exists(PK)"`
3. DynamoDB raises `ClientError` with `Error.Code == "ConditionalCheckFailedException"` because the PK doesn't exist
4. Caught at `aws_vpc_controller.py:48-51`, re-raised only if the code doesn't match; here it matches → returns `_response(404, {"message": "not found"})`

### Edge Case: parent-VPC existence check before subnet creation

`create_subnet_handler` and `list_subnets_by_vpc_handler` (`aws_subnet_controller.py:18-31`) both explicitly call `vpc_dynamodb.get_vpc(vpc_id)` before proceeding — this is the only place cross-entity referential integrity is enforced at the application layer (DynamoDB itself has no foreign-key constraint, unlike the SQL schema originally sketched in the project's `CLAUDE.md`).

## 4. Testing Strategy

**There is no test suite.** No `tests/` directory, no `pytest` in `requirements.txt`, no CI config found in the repo. This is the single biggest gap for a developer picking up this codebase — every gotcha listed above (dual-write ordering inconsistency, silent `None`-field-update drop, dead `describe_vpc`/`models/base.py`) would be easy to catch or protect against with even minimal unit tests around the `dynamodb`/`boto_ec2` service wrappers (mocking `boto3` via `moto` or `botocore.stub.Stubber`) and the model `to_dynamodb`/`from_dynamodb` round-trip.

**How to run tests locally**: not applicable yet — no test runner configured.

## 5. Performance & Scalability

- **Cold start**: each Lambda module-level `boto3.client("ec2", ...)` (`base_ec2.py:4`) and `boto3.resource("dynamodb")` (`base_dynamodb.py:4`) is created once per Lambda execution environment and reused across warm invocations — standard boto3 connection-reuse pattern, no explicit connection pooling needed.
- **Hot path**: `subnet_dynamodb` update/delete operations always cost an extra GSI query (`_find_by_subnet_id`) before the actual write, because the public API is `subnet_id`-only. If subnet update/delete volume becomes high, changing the API to accept `vpc_id` alongside `subnet_id` (as the create path already does) would halve the DynamoDB request count for those operations.
- **Concurrency**: no explicit Lambda reserved/provisioned concurrency is configured in `terraform/modules/lambda/main.tf` — defaults to AWS account-level unreserved concurrency, shared across both Lambdas.
- **DynamoDB capacity**: `PAY_PER_REQUEST` billing mode (`terraform/modules/dynamodb/variables.tf:33`) — no throughput planning needed, scales automatically, but costs more per-request at sustained high volume than provisioned capacity would.

## 6. Code Style & Conventions

- **Naming**: `snake_case` functions/variables, `PascalCase` dataclasses/Pydantic models, no `CONSTANT_CASE` except `MANAGED_TAG_KEY` and `ROUTES`.
- **Handler suffix convention**: every function callable from a route ends in `_handler` (e.g. `create_vpc_handler`), even though these live in files named `*_controller.py` — see the module breakdown note above; there's no separate "controller calls handler" indirection, the handler function *is* the controller.
- **Error handling**: no logging anywhere in `src/` (no `logging` module usage, no `print` except in the unrelated `lambda_handlers.py` hello-world). Errors either become an explicit 4xx `_response(...)` or propagate unhandled to Lambda's default error response (500-equivalent, surfaced as an API Gateway 502/500 depending on integration response mapping — the `api-gateway` Terraform module only defines a `200` `method_response`/`integration_response` with `selection_pattern = ""`, meaning **all** Lambda responses, including unhandled exceptions, get passed through as whatever API Gateway does with an unmapped Lambda proxy error — worth verifying against a real deployment).
- **Comments**: sparse, used only to explain a non-obvious constraint (e.g. "VPCs cannot be modified..." in `vpc_ec2.py:21`, "cidr_block intentionally omitted" in `schema/vpc.py:17`).
- **No pre-commit hooks or linter config** found (no `.pre-commit-config.yaml`, `pyproject.toml`, `setup.cfg`, or `ruff.toml`).

## 7. Common Tasks & Recipes

### How to add a new field to VPC (e.g. `owner_team`)

1. **Model**: `src/models/vpc_model.py` — add the field to the `@dataclass VPC` (after line 12, before `created_at` if it needs no default, or after if optional).
2. **Schema**: `src/schema/vpc.py` — add to `VPCResponse` (always), `VPCCreateRequest` if client-settable, `VPCUpdateRequest` (as `Optional[...] = None`) if mutable post-creation.
3. **No service-layer change needed** — `vpc_dynamodb.create_vpc(**body.model_dump())` and `update_vpc(**fields)` both forward arbitrary kwargs, so new fields flow through automatically as long as the model and schema agree.
4. **AWS side**: if the field should also be tagged on the real VPC, add a call in `aws_vpc_controller.py`'s `update_vpc_handler` (mirroring the existing `if "vpc_name" in fields: vpc_ec2.update_vpc_name(...)` block at line 53-54).

### How to add a new endpoint (e.g. `GET /vpcs/{vpc_id}/tags`)

1. Add the handler function to `src/controllers/aws_vpc_controller.py` (or a new controller module if it's a new resource entirely).
2. Register the route in `src/lambda_vpc_handler.py`'s `ROUTES` dict — key must be `(http_method, resource_path)` exactly matching what API Gateway will send.
3. Add the corresponding entry to the `routes` map in `terraform/main.tf`'s `module.api_gateway` block, with matching `path` segments (as a list, e.g. `["vpcs", "{vpc_id}", "tags"]`).
4. Add any new IAM permissions needed to `terraform/iam.tf` if the new endpoint calls an AWS API action not already granted.

### How to add a new Lambda/service (e.g. a third resource type)

1. Create `src/controllers/aws_<resource>_controller.py` with `*_handler` functions following the existing pattern (validate → AWS call → DynamoDB call → serialize).
2. Create `src/models/<resource>_model.py` (dataclass with `.key()`, `.to_dict()`, `.to_dynamodb()`, `.from_dynamodb()`).
3. Create `src/schema/<resource>.py` (Create/Update/Response/ListResponse Pydantic models).
4. Create `src/controllers/services/boto_ec2/<resource>_ec2.py` and/or `src/controllers/services/dynamodb/<resource>_dynamodb.py` following the thin-wrapper pattern.
5. Create `src/lambda_<resource>_handler.py` with its own `ROUTES` dict and `api_handler`.
6. Add a new `module "<resource>_lambda"` block in `terraform/main.tf`, wire its routes into `module.api_gateway`, and add IAM policies in `terraform/iam.tf`.

### Debugging tips

- To trace a request end-to-end without deploying, invoke handler functions directly with a hand-built `event` dict shaped like an API Gateway proxy integration event (`httpMethod`, `resource`, `pathParameters`, `body`) — there's no `sam local` config or test harness currently checked in, so this would be done ad hoc in a Python REPL with `TABLE_NAME`/`AWS_REGION` env vars set and either real AWS credentials or `moto`.
- `ConditionalCheckFailedException` handling is the main non-obvious control-flow mechanism in this codebase — if a 404 that should happen isn't happening, check whether the relevant DynamoDB call actually used a `ConditionExpression`.

## 8. Dependency Injection & Configuration

- **Environment variables**: `TABLE_NAME` (required, read at import time in `base_dynamodb.py` and unused `models/base.py`), `AWS_REGION` (optional, read in `base_ec2.py` via `os.environ.get`), `ENVIRONMENT` and `LOG_LEVEL` (set by Terraform, only actually read by the unused `lambda_handlers.py`).
- **No DI container or factory pattern** — every service module creates its own module-level boto3 client/resource as a bare global, initialized at import time (i.e., at Lambda cold start). There's no way to inject a mock client for testing without monkeypatching the module-level `_ec2`/`_dynamodb`/`_table` globals directly.

## 9. Known Limitations & Tech Debt

- **No authentication or authorization is implemented.** `.claude/memory/authorization_decision.md` records a decision to use a Lambda Authorizer validating `X-API-Key`, but `terraform/modules/api-gateway/main.tf:84` sets `authorization = "NONE"` on every method, and no authorizer Lambda or API-key logic exists in `src/`. This directly contradicts the CLAUDE.md requirement for an authentication layer and is the most significant gap in the current implementation — **every endpoint is currently open to the internet with no auth check.**
- **Database diverges from the documented decision.** `.claude/memory/database_decision.md` records Aurora Serverless v2 (PostgreSQL) as the chosen store, and `CLAUDE.md` documents a full SQL schema (`vpcs`/`subnets` tables with foreign keys and cascade delete). The actual implementation uses a single-table DynamoDB design instead — functional, but the SQL schema in `CLAUDE.md` and the memory file are stale/aspirational relative to the real code.
- **No test suite** (see Section 4).
- **Dead code**: `src/models/base.py` (unused), `src/lambda_handlers.py` (unused hello-world, not wired into Terraform), `vpc_ec2.describe_vpc` (defined, never called).
- **Inconsistent dual-write ordering** between VPC delete (AWS → DynamoDB) and subnet delete (DynamoDB → AWS) — see Module Breakdown gotchas above; no compensation/rollback logic exists for either direction if the second write fails.
- **No `created_by` is ever populated** — the field exists on both models/schemas but no handler sets it, consistent with there being no auth layer to derive an identity from.
- **Unpinned dependencies**, no lockfile — `make build` isn't reproducible across time.
- **Cross-layer string coupling with no shared constant**: the managed-resource tag key (`vpc-assignment-platform:managed`), the DynamoDB GSI names (`gsi_type`, `gsi_reverse`), and the route path structure are each duplicated between Python and Terraform with nothing enforcing they stay in sync.
