import os
import boto3

_TABLE_NAME = os.environ["TABLE_NAME"]
_dynamodb = boto3.resource("dynamodb")

def get_table():
    return _dynamodb.Table(_TABLE_NAME)