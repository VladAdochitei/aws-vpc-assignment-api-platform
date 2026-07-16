# Terraform State Backend Setup Options

## Current Status
- Placeholder S3 backend configuration exists in `terraform/providers.tf`
- Bucket name and key need to be configured
- No state locking (DynamoDB) currently set up

! Will most likely go with Option 2 !

## Option 1: Manual S3 Bucket Creation + Terraform Configuration

### Step 1: Create and Configure S3 Bucket (AWS CLI)

```bash
# Create bucket (using account ID for uniqueness)
aws s3api create-bucket \
  --bucket "vpc-assignment-tfstate-$(aws sts get-caller-identity --query Account --output text)" \
  --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1

# Enable versioning (rollback capability)
aws s3api put-bucket-versioning \
  --bucket "vpc-assignment-tfstate-ACCOUNT_ID" \
  --versioning-configuration Status=Enabled

# Enable encryption (AES-256)
aws s3api put-bucket-encryption \
  --bucket "vpc-assignment-tfstate-ACCOUNT_ID" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block all public access
aws s3api put-public-access-block \
  --bucket "vpc-assignment-tfstate-ACCOUNT_ID" \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Step 2: Update `terraform/providers.tf`

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "vpc-assignment-tfstate-ACCOUNT_ID"
    key            = "vpc-api/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "vpc-api-tflock"  # optional, for state locking
  }
}
```

**Pros:** Simple, one-time setup, no chicken-and-egg problem  
**Cons:** Manual bucket creation, less auditable

---

## Option 2: Terraform-Managed S3 Setup (Recommended)

### Step 1: Create `terraform/backend-setup.tf`

```hcl
# Bootstrap Terraform state bucket
# Run once with local state, then comment out after bucket is created

resource "aws_s3_bucket" "tfstate" {
  bucket = "vpc-assignment-tfstate-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_caller_identity" "current" {}
```

### Step 2: Initial Setup (Local State)

```bash
cd terraform
terraform init  # initializes with local state
terraform apply  # creates S3 bucket and configuration
```

### Step 3: Configure Backend in `terraform/providers.tf`

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "vpc-assignment-tfstate-ACCOUNT_ID"
    key            = "vpc-api/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
  }
}
```

### Step 4: Migrate State to S3

```bash
cd terraform
terraform init -reconfigure  # prompts to migrate state from local to S3
# Answer 'yes' to copy existing state
```

### Step 5: Comment Out Backend Setup (Optional)

After bucket exists, you can comment out or delete `backend-setup.tf` since the bucket is now managed externally and only needs to exist:

```hcl
# terraform/backend-setup.tf
# Commented out after initial bucket creation
# The bucket is now managed separately and only needs to exist
# If you need to recreate it, uncomment and re-apply
```

**Pros:** Fully auditable infrastructure-as-code, version controlled, explicit configuration  
**Cons:** Requires two-step init process, initial bootstrap with local state

---

## Optional: State Locking with DynamoDB

For team environments, add state locking to prevent concurrent modifications:

```bash
aws dynamodb create-table \
  --table-name vpc-api-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

Then update backend configuration to include:
```hcl
backend "s3" {
  bucket         = "vpc-assignment-tfstate-ACCOUNT_ID"
  key            = "vpc-api/terraform.tfstate"
  region         = "eu-west-1"
  encrypt        = true
  dynamodb_table = "vpc-api-tflock"
}
```

---

## Recommendation

**Use Option 2 (Terraform-Managed)** for:
- Better audit trail (all infra in version control)
- Team consistency
- Reproducibility

**Use Option 1 (Manual)** for:
- Quick one-off setup
- Simpler first-time experience

## Next Steps

1. Choose region (currently using `eu-west-1` in examples)
2. Decide on Option 1 or 2
3. Execute the setup steps
4. Run `terraform init` and `terraform plan` to verify
5. Add `.terraform/` to `.gitignore` if not already present
