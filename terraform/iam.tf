data "aws_iam_policy_document" "dynamodb_access" {
  statement {
    sid    = "AllowResourcesTableAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
    ]
    resources = [
      module.resources_table.table_arn,
      "${module.resources_table.table_arn}/index/*",
    ]
  }

  statement {
    sid       = "AllowResourcesTableTransactions"
    effect    = "Allow"
    actions   = ["dynamodb:TransactWriteItems"]
    resources = [module.resources_table.table_arn]
  }
}

resource "aws_iam_role_policy" "vpc_lambda_dynamodb" {
  name   = "${module.vpc_lambda.function_name}-vpc-dynamodb"
  role   = module.vpc_lambda.role_id
  policy = data.aws_iam_policy_document.dynamodb_access.json
}

resource "aws_iam_role_policy" "subnet_lambda_dynamodb" {
  name   = "${module.subnet_lambda.function_name}-subnet-dynamodb"
  role   = module.subnet_lambda.role_id
  policy = data.aws_iam_policy_document.dynamodb_access.json
}