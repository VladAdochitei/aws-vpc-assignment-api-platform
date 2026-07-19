from models.subnet_model import Subnet
from controllers.services.dynamodb import base_dynamodb


def create_subnet(subnet_id: str, vpc_id: str, subnet_name: str, cidr_block: str,
                   availability_zone: str | None = None, created_by: str | None = None) -> Subnet:
    subnet = Subnet(
        subnet_id=subnet_id,
        vpc_id=vpc_id,
        subnet_name=subnet_name,
        cidr_block=cidr_block,
        availability_zone=availability_zone,
        created_by=created_by,
    )
    base_dynamodb.put_item(subnet.to_dynamodb())
    return subnet


def _find_by_subnet_id(subnet_id: str) -> Subnet | None:
    items = base_dynamodb.query_by_sk(f"SUBNET#{subnet_id}")
    return Subnet.from_dynamodb(items[0]) if items else None


def get_subnet(subnet_id: str) -> Subnet | None:
    return _find_by_subnet_id(subnet_id)


def list_subnets() -> list[Subnet]:
    return [Subnet.from_dynamodb(i) for i in base_dynamodb.query_by_type("subnet")]


def list_subnets_by_vpc(vpc_id: str) -> list[Subnet]:
    items = base_dynamodb.query_by_pk(f"VPC#{vpc_id}", sk_prefix="SUBNET#")
    return [Subnet.from_dynamodb(i) for i in items]


def update_subnet(subnet_id: str, **fields) -> Subnet | None:
    fields = {k: v for k, v in fields.items() if v is not None}
    existing = _find_by_subnet_id(subnet_id)
    if not existing:
        return None
    if not fields:
        return existing
    item = base_dynamodb.update_item(existing.key(), fields)
    return Subnet.from_dynamodb(item)


def delete_subnet(subnet_id: str) -> bool:
    existing = _find_by_subnet_id(subnet_id)
    if not existing:
        return False
    base_dynamodb.delete_item(existing.key())
    return True