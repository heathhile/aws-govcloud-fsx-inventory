# AWS GovCloud FSX Inventory Tool - Context

## Project Overview

This project is a Python script that connects to an AWS commercial account via SSO, lists all associated GovCloud accounts in an organization, and inventories all FSX file systems. It performs **read-only operations only** and makes no changes to any AWS resources.

## Development Process

### Initial Requirements

The user requested a script that could:
1. Connect to an AWS commercial account using SSO
2. List all associated GovCloud accounts in the organization
3. Get all FSX ID numbers from those accounts
4. Export the data to a CSV file with: organization name, GovCloud ID, and FSX ID
5. Make no changes to any AWS accounts (read-only)

### Architecture Evolution

#### Phase 1: Initial Functional Design
Initially created a functional programming approach with separate functions for:
- SSO authentication
- Account listing
- Role assumption
- FSX system discovery
- CSV export

#### Phase 2: Class-Based Refactoring
At the user's suggestion, refactored to a class-based architecture for better:
- State management (eliminated global variables)
- Testability and maintainability
- Organization and extensibility

**Key Class: `GovCloudFSXInventory`**
- `__init__()` - Initialize with profile, dry-run flag, and role name
- `connect()` - Establish AWS SSO session
- `list_accounts()` - Query AWS Organizations for accounts
- `assume_role()` - Assume role in target GovCloud accounts
- `list_fsx_systems()` - Query FSX in both GovCloud regions
- `scan_accounts()` - Orchestrate scanning across all accounts
- `export_to_csv()` - Generate timestamped CSV output
- `run()` - Main execution flow

### Features Implemented

#### 1. Dry-Run Mode
Added `--dry-run` flag that:
- Simulates the entire workflow without AWS API calls
- Uses mock data (3 sample accounts, 2 FSX systems each)
- Shows console output as it would appear in real execution
- Displays sample CSV data without creating files
- Allows testing without AWS credentials

#### 2. Command-Line Interface
Using `argparse` for proper argument handling:
- `--profile` / `-p` - AWS SSO profile name
- `--dry-run` - Simulation mode
- `--role-name` / `-r` - Custom IAM role name (default: OrganizationAccountAccessRole)
- `--help` / `-h` - Usage information

#### 3. Multi-Region Support
Scans both GovCloud regions:
- us-gov-west-1
- us-gov-east-1

#### 4. Error Handling
- Graceful handling of authentication failures
- Permission denied errors
- Role assumption failures
- Missing FSX systems

#### 5. CSV Output
Generates timestamped CSV files with format:
```
Organization Name, GovCloud Account ID, FSX ID, FSX Type, Region, Lifecycle
```

### Package Management

#### Traditional Method (pip)
- Created `requirements.txt` with boto3 dependency
- Supports standard virtual environment workflow

#### Modern Method (uv)
At user's request, added full `uv` support:
- Created `pyproject.toml` with project metadata and dependencies
- Added `.python-version` file (Python 3.11)
- Auto-generated `uv.lock` for reproducible builds
- Enables fast, simple workflow: `uv run list_govcloud_fsx.py --dry-run`

**Benefits of uv:**
- 10-100x faster than pip
- Automatic virtual environment management
- No manual venv activation needed
- Better dependency resolution

### Files Created

1. **list_govcloud_fsx.py** (412 lines)
   - Main script with GovCloudFSXInventory class
   - Executable with shebang: `#!/usr/bin/env python3`

2. **README.md** (Comprehensive documentation)
   - Quick start guide with uv
   - Installation instructions (both uv and pip)
   - Usage examples
   - Dry-run mode documentation
   - AWS permissions required
   - Troubleshooting guide
   - Security notes

3. **pyproject.toml**
   - Modern Python project configuration
   - Project metadata
   - Dependencies specification
   - Compatible with uv and other modern tools

4. **requirements.txt**
   - Traditional pip requirements
   - boto3>=1.26.0
   - botocore>=1.29.0

5. **.python-version**
   - Specifies Python 3.11
   - Used by uv for automatic Python version management

6. **.gitignore**
   - Python artifacts (__pycache__, *.pyc, etc.)
   - Virtual environments (.venv, venv, env)
   - IDE files (.vscode, .idea)
   - OS files (.DS_Store)
   - Output CSV files
   - AWS credentials

7. **uv.lock**
   - Auto-generated lock file
   - Ensures reproducible dependency installs

## AWS Permissions Required

### Commercial Account
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

### GovCloud Accounts
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

## Usage Examples

### Testing (No AWS Connection)
```bash
# Using uv (recommended)
uv run list_govcloud_fsx.py --dry-run

# Using python
python3 list_govcloud_fsx.py --dry-run
```

### Production Use
```bash
# Configure and login
aws configure sso
aws sso login --profile my-commercial-account

# Run inventory
uv run list_govcloud_fsx.py --profile my-commercial-account

# With custom role
uv run list_govcloud_fsx.py -p my-profile -r CustomRoleName
```

## Design Decisions

1. **Class-based architecture** - Better organization, testability, and state management
2. **Dry-run first approach** - Allows safe testing before AWS operations
3. **Both uv and pip support** - Modern tooling while maintaining compatibility
4. **Read-only operations** - No modifications to AWS resources for safety
5. **Explicit error messages** - Clear guidance when issues occur
6. **Timestamped CSV output** - Prevents accidental overwrites
7. **Two GovCloud regions** - Comprehensive FSX discovery
8. **Configurable role name** - Flexibility for different AWS org structures

## Security Considerations

- Script performs read-only operations only
- No AWS resource modifications
- Credentials handled by AWS SDK (boto3)
- Temporary credentials used for role assumption
- CSV output may contain sensitive data - handle appropriately
- .gitignore prevents accidental credential commits

## Future Enhancement Ideas

- Add support for additional AWS regions
- Support for other file system types (EFS, etc.)
- JSON output format option
- Parallel account scanning for faster execution
- AWS CloudFormation template for IAM setup
- Progress bar for large organizations
- Email notification when scan completes
- Integration with AWS Config for compliance tracking

## Technologies Used

- **Python 3.7+** - Core language
- **boto3** - AWS SDK for Python
- **argparse** - Command-line argument parsing
- **csv module** - CSV file generation
- **uv** - Modern Python package manager
- **GitHub CLI** - For repository management
