import uuid
from models.vpc_model import VPC
from controllers.services.dynamodb import base_dynamodb


def create_vpc(vpc_name: str, cidr_block: str, region: str, created_by: str | None = None) -> VPC:
    vpc = VPC(
        vpc_id=f"vpc-{uuid.uuid4().hex[:12]}",
        vpc_name=vpc_name,
        cidr_block=cidr_block,
        region=region,
        created_by=created_by,
    )
    base_dynamodb.put_item(vpc.to_dynamodb())
    return vpc


def get_vpc(vpc_id: str) -> VPC | None:
    item = base_dynamodb.get_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"})
    return VPC.from_dynamodb(item) if item else None


def list_vpcs() -> list[VPC]:
    return [VPC.from_dynamodb(i) for i in base_dynamodb.query_by_type("vpc")]


def update_vpc(vpc_id: str, **fields) -> VPC | None:
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        return get_vpc(vpc_id)
    item = base_dynamodb.update_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"}, fields)
    return VPC.from_dynamodb(item)


def delete_vpc(vpc_id: str):
    base_dynamodb.delete_item({"PK": f"VPC#{vpc_id}", "SK": f"VPC#{vpc_id}"})