# IAM policies for the Lambda functions to access DynamoDB resources (Resources table)

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

# IAM policies for the Lambda functions to access EC2 resources (VPCs and Subnets)

data "aws_iam_policy_document" "vpc_ec2_access" {
  statement {
    sid    = "AllowVpcCreate"
    effect = "Allow"
    actions = [
      "ec2:CreateVpc",
      "ec2:CreateTags",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowVpcDeleteManagedOnly"
    effect = "Allow"
    actions = [
      "ec2:DeleteVpc",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/vpc-assignment-platform:managed"
      values   = ["true"]
    }
  }

  statement {
    sid    = "AllowVpcDescribeReadOnly"
    effect = "Allow"
    actions = [
      "ec2:DescribeVpcs",
    ]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "subnet_ec2_access" {
  statement {
    sid    = "AllowSubnetCreate"
    effect = "Allow"
    actions = [
      "ec2:CreateSubnet",
      "ec2:CreateTags",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowSubnetDeleteManagedOnly"
    effect = "Allow"
    actions = [
      "ec2:DeleteSubnet",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/vpc-assignment-platform:managed"
      values   = ["true"]
    }
  }

  statement {
    sid    = "AllowSubnetDescribeReadOnly"
    effect = "Allow"
    actions = [
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcs",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "vpc_lambda_ec2" {
  name   = "${module.vpc_lambda.function_name}-vpc-ec2"
  role   = module.vpc_lambda.role_id
  policy = data.aws_iam_policy_document.vpc_ec2_access.json
}

resource "aws_iam_role_policy" "subnet_lambda_ec2" {
  name   = "${module.subnet_lambda.function_name}-subnet-ec2"
  role   = module.subnet_lambda.role_id
  policy = data.aws_iam_policy_document.subnet_ec2_access.json
}