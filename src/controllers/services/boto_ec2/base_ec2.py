import os
import boto3

_ec2 = boto3.client("ec2", region_name=os.environ.get("AWS_REGION"))

MANAGED_TAG_KEY = "vpc-assignment-platform:managed"


def client():
    return _ec2


def build_tags(name: str, extra: dict | None = None) -> list[dict]:
    tags = {"Name": name, MANAGED_TAG_KEY: "true"}
    if extra:
        tags.update(extra)
    return [{"Key": k, "Value": v} for k, v in tags.items()]