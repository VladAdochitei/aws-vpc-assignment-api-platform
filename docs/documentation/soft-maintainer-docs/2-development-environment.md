# Development environment
The development environment mostly consists of the following tools:
1. Pyenv
2. Venv 
3. Tfenv
4. Terraform Workspaces (will see if we will apply that/MAY NOT BE USED)

## Contents: 
- [1. Setup Terraform environment](#1-setup-terraform-environment)
    - [1.1. Check versions](#11-check-versions)
    - [1.2. Install terraform](#12-install-terraform)
    - [1.3. Set terraform version](#13-set-terraform-version)
    - [1.4. Useful env vars](#14-useful-env-vars)
    - [1.5. Common workflow and troubleshooting](#15-common-workflow-and-troubleshooting)
- [2. Setup python development environment](#2-setup-python-development-environment)
    - [2.1. Install pyenv](#21-install-pyenv)
    - [2.2. Install and pin python versions](#22-install-and-pin-python-version)
    - [2.3. Create the virtual environment](#23-create-the-virtual-environment)
    - [2.4. Common workflow](#24-common-workflow)
- [3. AWS Credentials](#3-aws-credentials)
    - [3.1. Local testing](#31-local-testing)
    - [3.2. CI&CD Pipeline](#32-cicd-pipeline)

<br>

## 1. Setup terraform environment
First of all we will need to install tfenv as a terraform environment manager.

```sh
# macOS (Homebrew)
brew install tfenv

# Manual (Linux/macOS)
git clone https://github.com/tfutils/tfenv.git ~/.tfenv

# Add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/.tfenv/bin:$PATH"

source ~/.bashrc  # reload
```

### 1.1. Check versions
```sh
tfenv list                  # List installed versions (active marked with *)
tfenv version-name           # Show current active version
tfenv list-remote            # List all versions available for install
```

### 1.2. Install terraform
```sh
tfenv install 1.7.5          # Install specific version
tfenv install latest         # Install latest stable version
tfenv install latest:^1.6    # Install latest matching a constraint
tfenv uninstall 1.7.5        # Remove a version
```

### 1.3. Set terraform version
```sh
tfenv use 1.7.5
terraform --version  # Uses 1.7.5 everywhere
```

You can also set it to be only project-specific:

```sh
cd your-project
echo "1.7.5" > .terraform-version
terraform --version  # Uses 1.7.5 only in this directory (auto-switches on cd)
```

Priority order: `TFENV_TERRAFORM_VERSION (env var) → .terraform-version (local) → global (highest to lowest priority)`

Matching project requirements

```sh
tfenv install min-required   # Install version from required_version in .tf files
tfenv use min-required       # Switch to it
```

### 1.4. Useful Env vars

```sh
export TFENV_ARCH=arm64                  # Override architecture
export TFENV_TERRAFORM_VERSION=1.7.5     # Force a version, overriding .terraform-version
export TFENV_AUTO_INSTALL=true           # Auto-install missing pinned versions
export TFENV_REMOTE=https://example.com  # Custom mirror URL for downloads
```

### 1.5. Common workflow and troubleshooting
```sh
# Setup project with specific Terraform version
cd your-project
tfenv install 1.7.5
echo "1.7.5" > .terraform-version
terraform init

# Later, switch Terraform versions
tfenv use 1.8.0        # Switch globally
echo "1.8.0" > .terraform-version   # Or switch just this project
```

```sh
# terraform still pointing to system-wide install?
# Make sure ~/.tfenv/bin comes before other Terraform paths in PATH

# Version not switching in a directory?
tfenv version-name     # Confirms which version + source is active

# Need a version matching your config files?
tfenv install min-required
```

<br>

## 2. Setup python development environment
For the python development we will assume that you partly know what you are doing, therefore, the environment management solution chosen for this application is a hybrid system of:
- pyenv (sets up the python version)
- venv (Instantiates a virtual environment)

These two will help pinpoint and isolate the application's dependencies and python version.

### 2.1. Install pyenv
```sh
sudo apt update
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

curl https://pyenv.run | bash

# Add to ~/.bashrc or ~/.zshrc:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

source ~/.bashrc  # reload
```

### 2.2. Install and pin Python version
```sh
pyenv install 3.14.4       # Install specific version
cd your-project
pyenv local 3.14.4         # Project-specific, creates .python-version
```

### 2.3. Create the virtual environment
```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.4. Common workflow
```sh
cd your-project
pyenv install 3.14.4
pyenv local 3.14.4
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> Full pyenv reference (global vs. local vs. shell, `pyenv-virtualenv`, troubleshooting) available separately if needed — this section only covers what's used in this project's setup.

<br>

## 3. AWS credentials
For development purposes, AWS credentials need to be managed properly.

### 3.1. Local testing
For local testing, credentials are **not** stored in any file, `.env`, or committed anywhere in the repo. Just export them into your current shell session:

```sh
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_SESSION_TOKEN="your-session-token"   # if using temporary/STS credentials
export AWS_REGION="eu-central-1"                # adjust to your target region
```

These only persist for the current shell session — once you close the terminal (or open a new one), you'll need to export them again. Verify they're picked up correctly with:

```sh
aws sts get-caller-identity
```

### 3.2. CI/CD pipeline
The pipeline **triggers automatically when a new tag is pushed** to the repository (not on every commit/push to a branch).

In GitHub Actions, AWS credentials are **not stored as static access keys** — they are configured as a **role**, assumed via OIDC at runtime. The role ARN and related config are stored as **GitHub Actions secrets**, but no long-lived AWS keys are ever stored in the repo or in secrets.

```yaml
# example (illustrative only, adjust to your actual pipeline)
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: eu-central-1
```

> Never commit static AWS access keys anywhere — local or CI. Local testing uses temporary exported credentials; CI uses short-lived role assumption via OIDC.