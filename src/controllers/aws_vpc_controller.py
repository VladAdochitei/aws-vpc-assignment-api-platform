# Should use the models from the models package instead of importing them directly from the files
# Should have available methods such as:
# - list_vpcs()
# - create_vpc(vpc_id, vpc_name, cidr_block, region, created_by)
# - get_vpc_by_id(vpc_id)
# - update_vpc(vpc_id, vpc_name=None, cidr_block=None, region=None, status=None)
# - delete_vpc(vpc_id)
# Should also talk to the database using SQLAlchemy and handle exceptions appropriately, should also perform API calls with boto3.