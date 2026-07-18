# Should use the models from the models package instead of importing them directly from the files
# Should have available methods such as:
# - list_vpcs()
# - create_vpc(vpc_id, vpc_name, cidr_block, region, created_by)
# - get_vpc_by_id(vpc_id)
# - update_vpc(vpc_id, vpc_name=None, cidr_block=None, region=None, status=None)
# - delete_vpc(vpc_id)
# Should also talk to the database using SQLAlchemy and handle exceptions appropriately, should also perform API calls with boto3.

import json
import uuid
from pydantic import ValidationError
from botocore.exceptions import ClientError
from models.vpc_model import VPC
from schema.vpc import VPCCreateRequest, VPCUpdateRequest, VPCResponse, VPCListResponse
from controllers.services import dynamodb


def _response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def list_vpcs_handler(event):
    items = dynamodb.query_by_type("vpc")
    payload = VPCListResponse(items=items, count=len(items))
    return _response(200, payload.model_dump(mode="json"))


def create_vpc_handler(event):
    try:
        body = VPCCreateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})
    vpc = VPC(vpc_id=f"vpc-{uuid.uuid4().hex[:12]}", **body.model_dump())
    dynamodb.put_item(vpc.to_item())
    return _response(201, VPCResponse.model_validate(vpc.__dict__).model_dump(mode="json"))


def get_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    item = dynamodb.get_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"})
    if not item:
        return _response(404, {"message": "not found"})
    return _response(200, VPCResponse.model_validate(item).model_dump(mode="json"))


def update_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    try:
        body = VPCUpdateRequest.model_validate_json(event.get("body") or "{}")
    except ValidationError as e:
        return _response(400, {"message": "invalid request", "errors": e.errors()})
    fields = body.model_dump(exclude_none=True)
    if not fields:
        return _response(400, {"message": "no fields to update"})
    try:
        item = dynamodb.update_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"}, fields)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _response(404, {"message": "not found"})
        raise
    return _response(200, VPCResponse.model_validate(item).model_dump(mode="json"))


def delete_vpc_handler(event):
    vpc_id = event["pathParameters"]["vpc_id"]
    try:
        dynamodb.delete_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"})
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _response(404, {"message": "not found"})
        raise
    return _response(204, "")