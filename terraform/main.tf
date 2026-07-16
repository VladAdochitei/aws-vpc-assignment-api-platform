

module "hello_world_lambda" {
  source = "./modules/lambda"

  function_name = var.function_name
  handler       = "lambda_handlers.hello_world_handler"
  source_dir    = "${path.module}/../src"

  environment_variables = {
    ENVIRONMENT = var.environment
  }
}
