variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "handler" {
  description = "Lambda handler entrypoint, in the form file.function"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime identifier"
  type        = string
  default     = "python3.12"
}

variable "source_dir" {
  description = "Path to the directory containing the Lambda source code"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables to pass to the Lambda function"
  type        = map(string)
  default     = {}
}

variable "architecture" {
  description = "Lambda instruction set architecture (x86_64 or arm64)"
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.architecture)
    error_message = "architecture must be x86_64 or arm64."
  }
}