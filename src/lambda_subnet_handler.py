from controllers.aws_subnet_controller import (
    list_subnets_handler, create_subnet_handler, get_subnet_handler,
    update_subnet_handler, delete_subnet_handler, list_subnets_by_vpc_handler,
)

ROUTES = {
    ("GET", "/subnets"): list_subnets_handler,
    ("GET", "/subnets/{subnet_id}"): get_subnet_handler,
    ("PUT", "/subnets/{subnet_id}"): update_subnet_handler,
    ("DELETE", "/subnets/{subnet_id}"): delete_subnet_handler,
    ("GET", "/vpcs/{vpc_id}/subnets"): list_subnets_by_vpc_handler,
    ("POST", "/vpcs/{vpc_id}/subnets"): create_subnet_handler,
}

def api_handler(event, context):
    fn = ROUTES.get((event["httpMethod"], event["resource"]))
    if not fn:
        return {"statusCode": 404, "headers": {"Content-Type": "application/json"}, "body": '{"message": "not found"}'}
    return fn(event)