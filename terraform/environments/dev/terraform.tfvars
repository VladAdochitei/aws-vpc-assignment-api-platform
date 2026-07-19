aws_region    = "eu-central-1"
environment   = "dev"
function_name = "vpc-assignment-api-dev"
lambda_runtime = "python3.14"
lambda_architecture = "x86_64"

lambda_environment_variables = {
  # Add your environment variables here as needed
  # Example:
  # DATABASE_URL       = "postgresql://user:pass@host:5432/db"
  # API_KEYS_ALLOWLIST = "key1,key2"
}
