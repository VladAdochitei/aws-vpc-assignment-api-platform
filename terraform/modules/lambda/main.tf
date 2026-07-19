data "archive_file" "source" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.root}/../build/${var.function_name}.zip"
}

resource "aws_iam_role" "exec" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  role             = aws_iam_role.exec.arn
  handler          = var.handler
  runtime          = var.runtime
  filename         = data.archive_file.source.output_path
  source_code_hash = data.archive_file.source.output_base64sha256
  architectures    = [var.architecture]

  environment {
    variables = var.environment_variables
  }
}
