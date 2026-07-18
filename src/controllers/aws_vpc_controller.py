# Should use the models from the models package instead of importing them directly from the files
# Should have available methods such as:
# - list_vpcs()
# - create_vpc(vpc_id, vpc_name, cidr_block, region, created_by)
# - get_vpc_by_id(vpc_id)
# - update_vpc(vpc_id, vpc_name=None, cidr_block=None, region=None, status=None)
# - delete_vpc(vpc_id)
# Should also talk to the database using SQLAlchemy and handle exceptions appropriately, should also perform API calls with boto3.

import json
from pydantic import ValidationError
from botocore.exceptions import ClientError
from schema.vpc import VPCCreateRequest, VPCUpdateRequest, VPCResponse, VPCListResponse
from controllers.services.dynamodb import vpc_dynamodb


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def list_vpcs_handler(event):
    vpcs = vpc_dynamodb.list_vpcs()
    payload = VPCListResponse(items=[v.to_dict() for v in vpcs], count=len(vpcs))
    return _response(200, payload.model_dump(mode="json"))


def create_vpc_handler(event):
    try:
        body = VPCCreateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})
    vpc = vpc_dynamodb.create_vpc(**body.model_dump())
    return _response(201, VPCResponse.model_validate(vpc.to_dict()).model_dump(mode="json"))


def get_vpc_handler(event):
    vpc = vpc_dynamodb.get_vpc(event["pathParameters"]["vpc_id"])
    if not vpc:
        return _response(404, {"message": "not found"})
    return _response(200, VPCResponse.model_validate(vpc.to_dict()).model_dump(mode="json"))


def update_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    try:
        body = VPCUpdateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})
    try:
        vpc = vpc_dynamodb.update_vpc(vpc_id, **body.model_dump(exclude_none=True))
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _response(404, {"message": "not found"})
        raise
    return _response(200, VPCResponse.model_validate(vpc.to_dict()).model_dump(mode="json"))


def delete_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    try:
        vpc_dynamodb.delete_vpc(vpc_id)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _response(404, {"message": "not found"})
        raise
    return _response(204, "")