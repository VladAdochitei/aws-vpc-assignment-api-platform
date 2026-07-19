from controllers.services.boto_ec2 import base_ec2


def create_subnet(vpc_id: str, cidr_block: str, name: str, availability_zone: str | None = None) -> dict:
    kwargs = {
        "VpcId": vpc_id,
        "CidrBlock": cidr_block,
        "TagSpecifications": [{"ResourceType": "subnet", "Tags": base_ec2.build_tags(name)}],
    }
    if availability_zone:
        kwargs["AvailabilityZone"] = availability_zone

    resp = base_ec2.client().create_subnet(**kwargs)
    return resp["Subnet"]  # dict with SubnetId, State, CidrBlock, AvailabilityZone, etc.


def delete_subnet(aws_subnet_id: str):
    base_ec2.client().delete_subnet(SubnetId=aws_subnet_id)


def update_subnet_name(aws_subnet_id: str, name: str):
    base_ec2.client().create_tags(
        Resources=[aws_subnet_id],
        Tags=[{"Key": "Name", "Value": name}],
    )