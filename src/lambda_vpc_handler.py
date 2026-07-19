from controllers.aws_vpc_controller import (
    list_vpcs_handler, create_vpc_handler, get_vpc_handler, update_vpc_handler, delete_vpc_handler,
)

ROUTES = {
    ("GET", "/vpcs"): list_vpcs_handler,
    ("POST", "/vpcs"): create_vpc_handler,
    ("GET", "/vpcs/{vpc_id}"): get_vpc_handler,
    ("PUT", "/vpcs/{vpc_id}"): update_vpc_handler,
    ("DELETE", "/vpcs/{vpc_id}"): delete_vpc_handler,
}

def api_handler(event, context):
    fn = ROUTES.get((event["httpMethod"], event["resource"]))
    if not fn:
        return {"statusCode": 404, "headers": {"Content-Type": "application/json"}, "body": '{"message": "not found"}'}
    return fn(event)