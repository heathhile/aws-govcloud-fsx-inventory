# AWS GovCloud FSX Inventory Tool

This script connects to your AWS commercial account via SSO, lists all associated GovCloud accounts in your organization, and inventories all FSX file systems. It performs **read-only operations** and makes no changes to any AWS account.

## Quick Start (with uv)

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd aws_stuff
uv sync

# Test with dry-run (no AWS connection needed)
uv run list_govcloud_fsx.py --dry-run

# Configure AWS SSO and login
aws configure sso
aws sso login --profile my-profile

# Run for real
uv run list_govcloud_fsx.py --profile my-profile
```

## Prerequisites

1. **Python 3.7+** installed
2. **AWS CLI v2** installed and configured
3. **uv** (recommended) or **pip** for dependency management

## Installation

### 1. Install AWS CLI v2

If not already installed:

**macOS:**
```bash
brew install awscli
```

**Linux/Windows:** Follow [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### 2. Install Python Dependencies

**Option A: Using uv (Recommended - Fast & Modern)**

[uv](https://docs.astral.sh/uv/) is a modern, extremely fast Python package manager. Benefits:
- ⚡ 10-100x faster than pip
- 🔒 Automatic virtual environment management
- 🎯 No need to activate/deactivate venvs
- 📦 Better dependency resolution
- 🚀 Simple workflow: `uv run` handles everything

Install uv if you haven't already:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with brew on macOS
brew install uv

# Or with pip
pip install uv
```

Then install dependencies (uv handles everything automatically):
```bash
cd aws_stuff
uv sync
```

That's it! No venv creation or activation needed.

**Option B: Using pip (Traditional Method)**

```bash
pip install boto3
```

Or using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure AWS SSO

Configure your AWS SSO profile:

```bash
aws configure sso
```

Follow the prompts to enter:
- SSO start URL
- SSO region
- Account ID
- Role name
- CLI default region
- Profile name (e.g., "my-commercial-account")

## Usage

### 1. Test with Dry-Run Mode (Recommended First Step)

Before making any AWS API calls, test the script with dry-run mode to see what it would do:

**Using uv (Recommended):**
```bash
cd aws_stuff
uv run list_govcloud_fsx.py --dry-run
```

**Using python directly:**
```bash
python list_govcloud_fsx.py --dry-run
# or python3 list_govcloud_fsx.py --dry-run
```

This will simulate the entire process without connecting to AWS, showing you:
- Mock accounts that would be scanned
- Mock FSX systems that would be found
- CSV output that would be generated

**Note:** Dependencies must be installed even for dry-run mode, but AWS credentials are not required.

### 2. Login to AWS SSO

Before running the script for real, authenticate:

```bash
aws sso login --profile <your-profile-name>
```

### 3. Run the Script

**Using uv (Recommended - No venv activation needed):**

```bash
# Basic usage with a specific profile
uv run list_govcloud_fsx.py --profile my-commercial-account

# With default credentials
uv run list_govcloud_fsx.py

# With custom role name
uv run list_govcloud_fsx.py --profile my-profile --role-name CustomRoleName

# Dry-run with your profile
uv run list_govcloud_fsx.py --profile my-profile --dry-run

# Using short flags
uv run list_govcloud_fsx.py -p my-profile -r CustomRoleName

# View help
uv run list_govcloud_fsx.py --help
```

**Using python directly:**

```bash
# Basic usage with a specific profile
python list_govcloud_fsx.py --profile my-commercial-account

# With default credentials
python list_govcloud_fsx.py

# With custom role name
python list_govcloud_fsx.py --profile my-profile --role-name CustomRoleName

# Using short flags
python list_govcloud_fsx.py -p my-profile -r CustomRoleName
```

**Or make it executable:**
```bash
chmod +x list_govcloud_fsx.py
./list_govcloud_fsx.py --profile my-profile
```

### 4. Output

The script generates a CSV file named: `govcloud_fsx_inventory_YYYYMMDD_HHMMSS.csv`

**CSV Format:**
```
Organization Name,GovCloud Account ID,FSX ID,FSX Type,Region,Lifecycle
MyOrg-GovCloud,123456789012,fs-0123456789abcdef0,LUSTRE,us-gov-west-1,AVAILABLE
```

## Required AWS Permissions

The IAM role/user needs the following permissions:

### In the Commercial Account:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "organizations:ListAccounts",
        "organizations:DescribeAccount"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws-us-gov:iam::*:role/OrganizationAccountAccessRole"
    }
  ]
}
```

### In Each GovCloud Account:
The script assumes a role (default: `OrganizationAccountAccessRole`) that needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "fsx:DescribeFileSystems",
        "fsx:ListTagsForResource"
      ],
      "Resource": "*"
    }
  ]
}
```

## How It Works

1. **Authenticates** using AWS SSO credentials
2. **Lists accounts** in the AWS Organization (commercial account)
3. **Identifies GovCloud accounts** (accounts with "govcloud" in name/email)
4. **Assumes role** in each GovCloud account
5. **Queries FSX** in both GovCloud regions (us-gov-west-1, us-gov-east-1)
6. **Exports data** to CSV file

## Dry-Run Mode

The `--dry-run` flag allows you to test the script without making any actual AWS API calls. This is useful for:

**Testing the script behavior:**
- See what accounts would be scanned
- Preview the CSV output format
- Verify the script logic before running it

**When to use dry-run:**
- First time running the script
- Testing after making modifications
- Demonstrating the script to others
- Validating command-line arguments

**What dry-run does:**
- ✓ Uses mock data (3 sample GovCloud accounts, 2 sample FSX systems per account)
- ✓ Shows all console output as it would appear
- ✓ Displays sample CSV data without creating a file
- ✗ Does NOT connect to AWS
- ✗ Does NOT require AWS credentials (but boto3 must still be installed)
- ✗ Does NOT make any API calls
- ✗ Does NOT create any CSV files

**Example output:**
```bash
$ python list_govcloud_fsx.py --dry-run
============================================================
AWS GovCloud FSX Inventory Script
[DRY-RUN MODE - No actual AWS API calls will be made]
============================================================

→ Using default AWS credentials

→ Authenticating with AWS SSO...
✓ [DRY-RUN] Would connect as: arn:aws:iam::123456789012:user/mock-user
✓ [DRY-RUN] Would use account: 123456789012

→ [DRY-RUN] Would list accounts in organization...
  [DRY-RUN] API Call: organizations.list_accounts()
✓ [DRY-RUN] Would find 3 account(s)
  - Production-GovCloud (987654321098)
  - Development-GovCloud (876543210987)
  - Test-GovCloud (765432109876)

→ Scanning accounts for FSX file systems...

  Processing: Production-GovCloud (987654321098)
  [DRY-RUN] Would assume role: arn:aws-us-gov:iam::987654321098:role/OrganizationAccountAccessRole
  [DRY-RUN] Would query FSX in regions: us-gov-west-1, us-gov-east-1
  ✓ [DRY-RUN] Would find 2 FSX system(s)
...

→ [DRY-RUN] Would write 6 result(s) to govcloud_fsx_inventory_20241111_143022.csv
```

## Command-Line Options

```
--profile, -p      AWS CLI profile name to use
--dry-run          Simulate operations without making actual AWS API calls
--role-name, -r    IAM role name to assume in target accounts
                   (default: OrganizationAccountAccessRole)
--help, -h         Show help message and exit
```

## Customization

### Change the Assumed Role Name (via command-line)

Use the `--role-name` flag:
```bash
python list_govcloud_fsx.py --profile my-profile --role-name MyCustomRole
```

### Modify GovCloud Account Detection

Edit the `list_accounts()` method in the `GovCloudFSXInventory` class (around line 120) to adjust how accounts are identified as GovCloud accounts.

### Add Additional FSX Details

Modify the `list_fsx_systems()` method in the `GovCloudFSXInventory` class (around line 218) to capture additional FSX properties from the API response.

### Add More Regions

Edit the `__init__` method of the `GovCloudFSXInventory` class (line 33) to add more regions:
```python
self.govcloud_regions = ['us-gov-west-1', 'us-gov-east-1', 'us-gov-central-1']
```

## Troubleshooting

### "No AWS credentials found"
- Run: `aws sso login --profile <your-profile>`
- Verify: `aws sts get-caller-identity --profile <your-profile>`

### "AccessDenied" errors
- Ensure you have `organizations:ListAccounts` permission
- Verify the role exists in target accounts
- Check trust relationships on the assumed role

### "Cannot assume role in account"
- Verify the role name (default: `OrganizationAccountAccessRole`)
- Check the role's trust policy allows your commercial account
- Ensure the role has FSX read permissions

### No FSX systems found
- Verify FSX systems exist in the GovCloud accounts
- Check the script is scanning the correct regions
- Confirm the assumed role has `fsx:DescribeFileSystems` permission

## Security Notes

- This script performs **read-only operations only**
- No modifications are made to any AWS resources
- Credentials are handled by AWS SDK (boto3)
- Temporary credentials are used when assuming roles
- CSV output may contain sensitive account information - handle appropriately

## Support

For issues or questions:
1. Check AWS CloudTrail logs for API errors
2. Verify IAM permissions
3. Test manually with AWS CLI: `aws fsx describe-file-systems --region us-gov-west-1`
