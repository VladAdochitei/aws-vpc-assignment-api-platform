**List all subnets** — `GET /subnets`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets
```
Console: Path = `/subnets`, no body.

**List subnets for a VPC** — `GET /vpcs/{vpc_id}/subnets`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx/subnets
```
Console: Path = `/vpcs/{vpc_id}/subnets`, `vpc_id` = `vpc-xxxxxxxxxxxx`.

**Create subnet** — `POST /vpcs/{vpc_id}/subnets`
```bash
curl -X POST https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/vpcs/vpc-xxxxxxxxxxxx/subnets \
  -H "Content-Type: application/json" \
  -d '{"subnet_name": "test-subnet", "cidr_block": "10.0.1.0/24", "availability_zone": "eu-central-1a"}'
```
Console: Path = `/vpcs/{vpc_id}/subnets`, `vpc_id` = the real ID, Request Body = the JSON above.

**Get subnet** — `GET /subnets/{subnet_id}`
```bash
curl https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = `subnet-xxxxxxxxxxxx`.

**Update subnet** — `PUT /subnets/{subnet_id}`
```bash
curl -X PUT https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx \
  -H "Content-Type: application/json" \
  -d '{"subnet_name": "renamed-subnet"}'
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = the real ID, Request Body = the JSON above.

**Delete subnet** — `DELETE /subnets/{subnet_id}`
```bash
curl -X DELETE https://<api-id>.execute-api.eu-central-1.amazonaws.com/dev/subnets/subnet-xxxxxxxxxxxx
```
Console: Path = `/subnets/{subnet_id}`, `subnet_id` = the real ID, no body.

Grab a real `vpc_id` from `POST /vpcs` first, then a real `subnet_id` from the create-subnet response before testing get/update/delete.