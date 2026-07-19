from controllers.services.boto_ec2 import base_ec2


def create_vpc(cidr_block: str, name: str) -> dict:
    resp = base_ec2.client().create_vpc(
        CidrBlock=cidr_block,
        TagSpecifications=[{"ResourceType": "vpc", "Tags": base_ec2.build_tags(name)}],
    )
    return resp["Vpc"]  # dict with VpcId, State, CidrBlock, etc.


def describe_vpc(aws_vpc_id: str) -> dict | None:
    resp = base_ec2.client().describe_vpcs(VpcIds=[aws_vpc_id])
    vpcs = resp.get("Vpcs", [])
    return vpcs[0] if vpcs else None

def delete_vpc(aws_vpc_id: str):
    base_ec2.client().delete_vpc(VpcId=aws_vpc_id)


def update_vpc_name(aws_vpc_id: str, name: str): # VPCs cannot be modified, they need to be deleted and recreated if different CIDR is needed. 
    base_ec2.client().create_tags(
        Resources=[aws_vpc_id],
        Tags=[{"Key": "Name", "Value": name}],
    )