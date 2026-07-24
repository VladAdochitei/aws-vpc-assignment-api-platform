variable "api_name" {
  description = "Name of the REST API"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "routes" {
  description = "Map of routes. path is a list of segments; {param} segments become path params."
  type = map(object({
    path                  = list(string)
    http_method           = string
    lambda_function_arn   = string
    lambda_function_name  = string
  }))
}


variable "authorizer_lambda_invoke_arn" {
  description = "invoke_arn of the authorizer Lambda (used by aws_api_gateway_authorizer)"
  type        = string
}

variable "authorizer_function_name" {
  description = "function_name of the authorizer Lambda (used by aws_lambda_permission)"
  type        = string
}

variable "authorizer_ttl_seconds" {
  description = "How long API Gateway caches an Allow/Deny decision per token"
  type        = number
  default     = 300
}