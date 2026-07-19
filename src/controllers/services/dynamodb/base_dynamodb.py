import os
import boto3

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(os.environ["TABLE_NAME"])


def put_item(item: dict):
    _table.put_item(Item=item)


def get_item(key: dict) -> dict | None:
    return _table.get_item(Key=key).get("Item")


def query_by_type(entity_type: str) -> list[dict]:
    resp = _table.query(
        IndexName="gsi_type",
        KeyConditionExpression="entity_type = :t",
        ExpressionAttributeValues={":t": entity_type},
    )
    return resp.get("Items", [])


def update_item(key: dict, fields: dict) -> dict:
    return _table.update_item(
        Key=key,
        UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in fields),
        ExpressionAttributeNames={f"#{k}": k for k in fields},
        ExpressionAttributeValues={f":{k}": v for k, v in fields.items()},
        ConditionExpression="attribute_exists(PK)",
        ReturnValues="ALL_NEW",
    ).get("Attributes")


def delete_item(key: dict):
    _table.delete_item(Key=key, ConditionExpression="attribute_exists(PK)")

def query_by_pk(pk: str, sk_prefix: str | None = None) -> list[dict]:
    if sk_prefix:
        resp = _table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={":pk": pk, ":sk": sk_prefix},
        )
    else:
        resp = _table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": pk},
        )
    return resp.get("Items", [])


def query_by_sk(sk: str) -> list[dict]:
    resp = _table.query(
        IndexName="gsi_reverse",
        KeyConditionExpression="SK = :sk",
        ExpressionAttributeValues={":sk": sk},
    )
    return resp.get("Items", [])