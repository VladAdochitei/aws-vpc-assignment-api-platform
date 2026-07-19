module "vpc_lambda" {
  source = "./modules/lambda"

  function_name = "${var.function_name}-vpc"
  handler       = "lambda_vpc_handler.api_handler"
  runtime       = var.lambda_runtime
  source_dir = "${path.module}/../build/package"
  architecture = var.lambda_architecture

  environment_variables = merge(
    { 
    ENVIRONMENT = var.environment, 
    LOG_LEVEL = "INFO"
    TABLE_NAME  = module.resources_table.table_name 
    },
    var.lambda_environment_variables
  )
}

module "subnet_lambda" {
  source = "./modules/lambda"

  function_name = "${var.function_name}-subnet"
  handler       = "lambda_subnet_handler.api_handler"
  runtime       = var.lambda_runtime
  source_dir = "${path.module}/../build/package"
  architecture = var.lambda_architecture
  environment_variables = merge(
    { ENVIRONMENT = var.environment, 
    LOG_LEVEL = "INFO" 
    TABLE_NAME  = module.resources_table.table_name
    },
    var.lambda_environment_variables
  )
}

module "api_gateway" {
  source = "./modules/api-gateway"

  api_name               = "${var.function_name}-api"
  stage_name              = var.environment

  routes = {
    vpcs_list = {
      path                 = ["vpcs"]
      http_method          = "GET"
      lambda_function_arn  = module.vpc_lambda.invoke_arn
      lambda_function_name = module.vpc_lambda.function_name
    }
    vpcs_create = {
      path                 = ["vpcs"]
      http_method          = "POST"
      lambda_function_arn  = module.vpc_lambda.invoke_arn
      lambda_function_name = module.vpc_lambda.function_name
    }
    vpcs_get = {
      path                 = ["vpcs", "{vpc_id}"]
      http_method          = "GET"
      lambda_function_arn  = module.vpc_lambda.invoke_arn
      lambda_function_name = module.vpc_lambda.function_name
    }
    vpcs_update = {
      path                 = ["vpcs", "{vpc_id}"]
      http_method          = "PUT"
      lambda_function_arn  = module.vpc_lambda.invoke_arn
      lambda_function_name = module.vpc_lambda.function_name
    }
    vpcs_delete = {
      path                 = ["vpcs", "{vpc_id}"]
      http_method          = "DELETE"
      lambda_function_arn  = module.vpc_lambda.invoke_arn
      lambda_function_name = module.vpc_lambda.function_name
    }

    subnets_list = {
      path                 = ["subnets"]
      http_method          = "GET"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }
    subnets_get = {
      path                 = ["subnets", "{subnet_id}"]
      http_method          = "GET"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }
    subnets_update = {
      path                 = ["subnets", "{subnet_id}"]
      http_method          = "PUT"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }
    subnets_delete = {
      path                 = ["subnets", "{subnet_id}"]
      http_method          = "DELETE"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }

    subnets_by_vpc_list = {
      path                 = ["vpcs", "{vpc_id}", "subnets"]
      http_method          = "GET"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }
    subnets_by_vpc_create = {
      path                 = ["vpcs", "{vpc_id}", "subnets"]
      http_method          = "POST"
      lambda_function_arn  = module.subnet_lambda.invoke_arn
      lambda_function_name = module.subnet_lambda.function_name
    }
  }
}


module "resources_table" {
  source     = "./modules/dynamodb"
  table_name = "${var.function_name}-DATABASE-resources"
  hash_key   = "PK"
  range_key  = "SK"

  attributes = [
    { name = "PK", type = "S" },
    { name = "SK", type = "S" },
    { name = "entity_type", type = "S" },
  ]

  global_secondary_indexes = [
    {
      name            = "gsi_reverse"
      hash_key        = "SK"
      projection_type = "ALL"
    },
    {
      name            = "gsi_type"
      hash_key        = "entity_type"
      range_key       = "PK"
      projection_type = "ALL"
    },
  ]
}