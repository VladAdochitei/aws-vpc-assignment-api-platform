resource "aws_api_gateway_authorizer" "token" {
  name                             = "${var.api_name}-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.this.id
  authorizer_uri                   = var.authorizer_lambda_invoke_arn
  type                             = "TOKEN"
  identity_source                  = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = var.authorizer_ttl_seconds
}

resource "aws_lambda_permission" "authorizer_invoke" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = var.authorizer_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.this.execution_arn}/authorizers/${aws_api_gateway_authorizer.token.id}"
}

resource "aws_api_gateway_rest_api" "this" {
  name        = var.api_name
  description = "API Gateway for ${var.api_name}"
}

locals {
  # Every unique ancestor path (as joined strings) across all routes, e.g.
  # ["vpcs", "vpcs/{vpc_id}", "vpcs/{vpc_id}/subnets", "subnets", "subnets/{subnet_id}"]
  path_prefixes = distinct(flatten([
    for route in values(var.routes) : [
      for i in range(1, length(route.path) + 1) : join("/", slice(route.path, 0, i))
    ]
  ]))

  # Build a tree node per unique prefix: its own path_part, its parent key, and its depth
  path_tree = {
    for p in local.path_prefixes : p => {
      path_part = element(split("/", p), length(split("/", p)) - 1)
      parent    = length(split("/", p)) > 1 ? join("/", slice(split("/", p), 0, length(split("/", p)) - 1)) : null
      depth     = length(split("/", p))
    }
  }

  # Split by depth so each level's resources only depend on the previous level's
  # (a single for_each resource block can't reference other instances of itself
  # without Terraform reporting a cycle). Max depth here is 3 (vpcs/{vpc_id}/subnets) —
  # add a level4 block below (and to resource_ids) if a deeper route is ever added.
  level1_paths = { for p, v in local.path_tree : p => v if v.depth == 1 }
  level2_paths = { for p, v in local.path_tree : p => v if v.depth == 2 }
  level3_paths = { for p, v in local.path_tree : p => v if v.depth == 3 }

  # Per-route: joined path key + map of path-parameter request_parameters
  route_meta = {
    for key, route in var.routes : key => {
      path_key = join("/", route.path)
      request_parameters = {
        for seg in route.path : "method.request.path.${trim(seg, "{}")}" => true
        if can(regex("^\\{.*\\}$", seg))
      }
    }
  }
}

resource "aws_api_gateway_resource" "level1" {
  for_each = local.level1_paths

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = each.value.path_part
}

resource "aws_api_gateway_resource" "level2" {
  for_each = local.level2_paths

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level1[each.value.parent].id
  path_part   = each.value.path_part
}

resource "aws_api_gateway_resource" "level3" {
  for_each = local.level3_paths

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level2[each.value.parent].id
  path_part   = each.value.path_part
}

locals {
  # Merge all levels into one lookup keyed by full path string, so methods/integrations
  # don't need to care which level a given route's path landed on.
  resource_ids = merge(
    { for k, r in aws_api_gateway_resource.level1 : k => r.id },
    { for k, r in aws_api_gateway_resource.level2 : k => r.id },
    { for k, r in aws_api_gateway_resource.level3 : k => r.id },
  )
}

resource "aws_api_gateway_method" "route" {
  for_each = var.routes

  rest_api_id         = aws_api_gateway_rest_api.this.id
  resource_id         = local.resource_ids[local.route_meta[each.key].path_key]
  http_method         = each.value.http_method
  authorization       = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.token.id
  request_parameters  = local.route_meta[each.key].request_parameters
}

resource "aws_api_gateway_integration" "route" {
  for_each = var.routes

  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = local.resource_ids[local.route_meta[each.key].path_key]
  http_method             = aws_api_gateway_method.route[each.key].http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = each.value.lambda_function_arn
}

resource "aws_api_gateway_method_response" "route" {
  for_each = var.routes

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = local.resource_ids[local.route_meta[each.key].path_key]
  http_method = aws_api_gateway_method.route[each.key].http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "route" {
  for_each = var.routes

  rest_api_id       = aws_api_gateway_rest_api.this.id
  resource_id       = local.resource_ids[local.route_meta[each.key].path_key]
  http_method       = aws_api_gateway_method.route[each.key].http_method
  status_code       = aws_api_gateway_method_response.route[each.key].status_code
  selection_pattern = ""

  depends_on = [
    aws_api_gateway_integration.route,
    aws_lambda_permission.api_gateway,
  ]
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id

  triggers = {
    redeployment = sha1(jsonencode(var.routes))
  }

  depends_on = [aws_api_gateway_integration_response.route]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "this" {
  deployment_id = aws_api_gateway_deployment.this.id
  rest_api_id   = aws_api_gateway_rest_api.this.id
  stage_name    = var.stage_name
}

resource "aws_lambda_permission" "api_gateway" {
  for_each = toset([for route in values(var.routes) : route.lambda_function_name])

  statement_id  = "AllowAPIGatewayInvoke-${each.value}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.this.execution_arn}/*"
}