> **Note**: All requests require an `Authorization` header with a valid API key (e.g., `dev-local-key-CHANGE-ME` in dev). Requests without a valid key will receive a 403 Forbidden response.

**List all subnets** — `GET /subnets`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/subnets`, Headers = `Authorization: dev-local-key-CHANGE-ME`, no body.

**List subnets for a VPC** — `GET /vpcs/{vpc_id}/subnets`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx/subnets \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/vpcs/{vpc_id}/subnets`, `vpc_id` = `vpc-xxxxxxxxxxxx`, Headers = `Authorization: dev-local-key-CHANGE-ME`.

**Create subnet** — `POST /vpcs/{vpc_id}/subnets`
```bash
curl -X POST https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx/subnets \
  -H "Authorization: dev-local-key-CHANGE-ME" \
  -H "Content-Type: application/json" \
  -d '{"subnet_name": "test-subnet", "cidr_block": "10.0.1.0/24", "availability_zone": "eu-central-1a"}'
```
Console: Path = `/vpcs/{vpc_id}/subnets`, `vpc_id` = the real ID, Headers = `Authorization: dev-local-key-CHANGE-ME`, Request Body = the JSON above.

**Get subnet** — `GET /subnets/{subnet_id}`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = `subnet-xxxxxxxxxxxx`, Headers = `Authorization: dev-local-key-CHANGE-ME`.

**Update subnet** — `PUT /subnets/{subnet_id}`
```bash
curl -X PUT https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME" \
  -H "Content-Type: application/json" \
  -d '{"subnet_name": "renamed-subnet"}'
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = the real ID, Headers = `Authorization: dev-local-key-CHANGE-ME`, Request Body = the JSON above.

**Delete subnet** — `DELETE /subnets/{subnet_id}`
```bash
curl -X DELETE https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = the real ID, Headers = `Authorization: dev-local-key-CHANGE-ME`, no body.

Grab a real `vpc_id` from `POST /vpcs` first, then a real `subnet_id` from the create-subnet response before testing get/update/delete.