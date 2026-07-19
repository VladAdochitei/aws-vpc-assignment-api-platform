import json
from pydantic import ValidationError
from schema.subnet import SubnetCreateRequest, SubnetUpdateRequest, SubnetResponse, SubnetListResponse
from controllers.services.dynamodb import subnet_dynamodb, vpc_dynamodb
from controllers.services.boto_ec2 import subnet_ec2


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def list_subnets_handler(event):
    subnets = subnet_dynamodb.list_subnets()
    payload = SubnetListResponse(items=[s.to_dict() for s in subnets], count=len(subnets))
    return _response(200, payload.model_dump(mode="json"))


def list_subnets_by_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    if not vpc_dynamodb.get_vpc(vpc_id):
        return _response(404, {"message": "vpc not found"})

    subnets = subnet_dynamodb.list_subnets_by_vpc(vpc_id)
    payload = SubnetListResponse(items=[s.to_dict() for s in subnets], count=len(subnets))
    return _response(200, payload.model_dump(mode="json"))


def create_subnet_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    if not vpc_dynamodb.get_vpc(vpc_id):
        return _response(404, {"message": "vpc not found"})

    try:
        body = SubnetCreateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})

    aws_subnet = subnet_ec2.create_subnet(
        vpc_id=vpc_id,
        cidr_block=body.cidr_block,
        name=body.subnet_name,
        availability_zone=body.availability_zone,
    )
    subnet = subnet_dynamodb.create_subnet(
        subnet_id=aws_subnet["SubnetId"],
        vpc_id=vpc_id,
        **body.model_dump(),
    )
    return _response(201, SubnetResponse.model_validate(subnet.to_dict()).model_dump(mode="json"))


def get_subnet_handler(event):
    subnet = subnet_dynamodb.get_subnet(event["pathParameters"]["subnet_id"])
    if not subnet:
        return _response(404, {"message": "not found"})
    return _response(200, SubnetResponse.model_validate(subnet.to_dict()).model_dump(mode="json"))


def update_subnet_handler(event):
    subnet_id = event["pathParameters"]["subnet_id"]
    try:
        body = SubnetUpdateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})

    fields = body.model_dump(exclude_none=True)

    subnet = subnet_dynamodb.update_subnet(subnet_id, **fields)
    if not subnet:
        return _response(404, {"message": "not found"})

    if "subnet_name" in fields:
        subnet_ec2.update_subnet_name(subnet_id, fields["subnet_name"])

    return _response(200, SubnetResponse.model_validate(subnet.to_dict()).model_dump(mode="json"))


def delete_subnet_handler(event):
    subnet_id = event["pathParameters"]["subnet_id"]

    deleted = subnet_dynamodb.delete_subnet(subnet_id)
    if not deleted:
        return _response(404, {"message": "not found"})

    subnet_ec2.delete_subnet(subnet_id)
    return _response(200, {"subnet_id": subnet_id, "message": "deleted"})