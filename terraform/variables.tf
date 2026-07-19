variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "vpc-assignment-api-dev"
}

variable "lambda_handler" {
  description = "Lambda handler entrypoint (e.g., lambda_handlers.api_handler)"
  type        = string
  default     = "lambda_handlers.api_handler"
}

variable "lambda_runtime" {
  description = "Lambda runtime identifier"
  type        = string
  default     = "python3.12"
}

variable "lambda_environment_variables" {
  description = "Environment variables to pass to Lambda (key-value map)"
  type        = map(string)
  default     = {}
}

variable "lambda_architecture" {
  description = "Lambda instruction set architecture (x86_64 or arm64); must match Makefile ARCH"
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.lambda_architecture)
    error_message = "lambda_architecture must be x86_64 or arm64."
  }
}