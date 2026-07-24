Here's a quick reference — for API Gateway's console **Test** view, the important parts are the **path** field, **Query Strings**, **Headers**, and **Request Body**, since it doesn't take a real URL. I'll give both curl (for actual invoke URL testing) and note what maps to the console fields.

> **Note**: All requests require an `Authorization` header with a valid API key (e.g., `dev-local-key-CHANGE-ME` in dev). Requests without a valid key will receive a 403 Forbidden response.

**List VPCs** — `GET /vpcs`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/vpcs`, Headers = `Authorization: dev-local-key-CHANGE-ME`, no body.

**Create VPC** — `POST /vpcs`
```bash
curl -X POST https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs \
  -H "Authorization: dev-local-key-CHANGE-ME" \
  -H "Content-Type: application/json" \
  -d '{"vpc_name": "test-vpc", "cidr_block": "10.0.0.0/16", "region": "eu-central-1"}'
```
Console: Path = `/vpcs`, Headers = `Authorization: dev-local-key-CHANGE-ME`, Request Body = the JSON above.

**Get VPC** — `GET /vpcs/{vpc_id}`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/vpcs/{vpc_id}`, Path field `vpc_id` = `vpc-xxxxxxxxxxxx`, Headers = `Authorization: dev-local-key-CHANGE-ME`.

**Update VPC** — `PUT /vpcs/{vpc_id}`
```bash
curl -X PUT https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME" \
  -H "Content-Type: application/json" \
  -d '{"vpc_name": "renamed-vpc"}'
```
Console: Path = `/vpcs/{vpc_id}`, `vpc_id` = the real ID, Headers = `Authorization: dev-local-key-CHANGE-ME`, Request Body = the JSON above.

**Delete VPC** — `DELETE /vpcs/{vpc_id}`
```bash
curl -X DELETE https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx \
  -H "Authorization: dev-local-key-CHANGE-ME"
```
Console: Path = `/vpcs/{vpc_id}`, `vpc_id` = the real ID, Headers = `Authorization: dev-local-key-CHANGE-ME`, no body.

Grab a real `vpc_id` from the `POST` or `GET /vpcs` response before testing get/update/delete.