#!/usr/bin/env python3
"""
Script to list all FSX file systems from GovCloud accounts in an AWS Organization.
This script connects via AWS SSO and performs read-only operations.
"""

import argparse
import boto3
import csv
import sys
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


class GovCloudFSXInventory:
    """
    Class to manage FSX inventory collection from GovCloud accounts.
    """

    def __init__(self, profile_name=None, dry_run=False, role_name='OrganizationAccountAccessRole'):
        """
        Initialize the inventory manager.

        Args:
            profile_name: AWS CLI profile name to use (optional)
            dry_run: If True, simulates operations without making actual AWS API calls
            role_name: IAM role name to assume in target accounts
        """
        self.profile_name = profile_name
        self.dry_run = dry_run
        self.role_name = role_name
        self.session = None
        self.govcloud_regions = ['us-gov-west-1', 'us-gov-east-1']

    def connect(self):
        """
        Establish AWS SSO session.

        Returns:
            bool: True if connection successful (or dry-run), False otherwise
        """
        if self.dry_run:
            print(f"✓ [DRY-RUN] Would connect as: arn:aws:iam::123456789012:user/mock-user")
            print(f"✓ [DRY-RUN] Would use account: 123456789012")
            return True

        try:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name)
            else:
                self.session = boto3.Session()

            # Test credentials by making a simple API call
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✓ Connected as: {identity['Arn']}")
            print(f"✓ Account: {identity['Account']}")
            return True

        except NoCredentialsError:
            print("ERROR: No AWS credentials found. Please configure AWS SSO:")
            print("  1. Run: aws configure sso")
            print("  2. Run: aws sso login --profile <your-profile>")
            return False

        except ClientError as e:
            print(f"ERROR: Failed to authenticate: {e}")
            return False

    def list_accounts(self):
        """
        List all accounts in the AWS Organization.

        Returns:
            list: List of dictionaries containing account info
        """
        if self.dry_run:
            print("\n→ [DRY-RUN] Would list accounts in organization...")
            print("  [DRY-RUN] API Call: organizations.list_accounts()")
            mock_accounts = [
                {
                    'id': '987654321098',
                    'name': 'Production-GovCloud',
                    'email': 'govcloud-prod@example.com',
                    'status': 'ACTIVE'
                },
                {
                    'id': '876543210987',
                    'name': 'Development-GovCloud',
                    'email': 'govcloud-dev@example.com',
                    'status': 'ACTIVE'
                },
                {
                    'id': '765432109876',
                    'name': 'Test-GovCloud',
                    'email': 'govcloud-test@example.com',
                    'status': 'ACTIVE'
                }
            ]
            print(f"✓ [DRY-RUN] Would find {len(mock_accounts)} account(s)")
            for acc in mock_accounts:
                print(f"  - {acc['name']} ({acc['id']})")
            return mock_accounts

        org_client = self.session.client('organizations')
        accounts = []

        try:
            print("\n→ Listing accounts in organization...")
            paginator = org_client.get_paginator('list_accounts')

            for page in paginator.paginate():
                for account in page['Accounts']:
                    account_name = account.get('Name', '')
                    account_email = account.get('Email', '')
                    account_id = account['Id']

                    # Filter for GovCloud accounts or all active accounts
                    # Adjust this logic based on your organization's naming conventions
                    if ('govcloud' in account_name.lower() or
                        'govcloud' in account_email.lower() or
                        account.get('Status') == 'ACTIVE'):

                        accounts.append({
                            'id': account_id,
                            'name': account_name,
                            'email': account_email,
                            'status': account.get('Status', 'UNKNOWN')
                        })

            print(f"✓ Found {len(accounts)} account(s)")
            return accounts

        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print("ERROR: No permission to access AWS Organizations.")
                print("This script requires organizations:ListAccounts permission.")
            else:
                print(f"ERROR: Failed to list accounts: {e}")
            return []

    def assume_role(self, account_id):
        """
        Assume a role in the target account.

        Args:
            account_id: Target AWS account ID

        Returns:
            boto3.Session or None: Session for the assumed role, or None if failed
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would assume role: arn:aws-us-gov:iam::{account_id}:role/{self.role_name}")
            return 'mock_session'  # Return a mock session indicator

        try:
            sts_client = self.session.client('sts')
            role_arn = f"arn:aws-us-gov:iam::{account_id}:role/{self.role_name}"

            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f'fsx-inventory-{account_id}'
            )

            credentials = response['Credentials']
            assumed_session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            return assumed_session

        except ClientError as e:
            print(f"  ⚠ Cannot assume role in account {account_id}: {e.response['Error']['Code']}")
            return None

    def list_fsx_systems(self, session, account_info):
        """
        List all FSX file systems in a GovCloud account.

        Args:
            session: boto3.Session object (or mock indicator for dry-run)
            account_info: Dictionary with account details

        Returns:
            list: List of FSX file system details
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would query FSX in regions: {', '.join(self.govcloud_regions)}")
            mock_fsx = [
                {
                    'filesystem_id': 'fs-0123456789abcdef0',
                    'filesystem_type': 'LUSTRE',
                    'region': 'us-gov-west-1',
                    'creation_time': '2024-01-15',
                    'lifecycle': 'AVAILABLE'
                },
                {
                    'filesystem_id': 'fs-abcdef0123456789',
                    'filesystem_type': 'WINDOWS',
                    'region': 'us-gov-west-1',
                    'creation_time': '2024-02-20',
                    'lifecycle': 'AVAILABLE'
                }
            ]
            print(f"  ✓ [DRY-RUN] Would find {len(mock_fsx)} FSX system(s)")
            return mock_fsx

        fsx_systems = []

        for region in self.govcloud_regions:
            try:
                fsx_client = session.client('fsx', region_name=region)

                paginator = fsx_client.get_paginator('describe_file_systems')
                for page in paginator.paginate():
                    for fs in page.get('FileSystems', []):
                        fsx_systems.append({
                            'filesystem_id': fs['FileSystemId'],
                            'filesystem_type': fs['FileSystemType'],
                            'region': region,
                            'creation_time': fs.get('CreationTime', ''),
                            'lifecycle': fs.get('Lifecycle', '')
                        })

                if fsx_systems:
                    print(f"  ✓ Found {len(fsx_systems)} FSX system(s) in {region}")

            except ClientError as e:
                if e.response['Error']['Code'] not in ['AccessDenied', 'UnauthorizedOperation']:
                    print(f"  ⚠ Error querying FSX in {region}: {e.response['Error']['Code']}")
                continue

        return fsx_systems

    def scan_accounts(self, accounts):
        """
        Scan all accounts for FSX file systems.

        Args:
            accounts: List of account dictionaries

        Returns:
            list: List of FSX inventory results
        """
        print(f"\n→ Scanning accounts for FSX file systems...")
        results = []

        for account in accounts:
            account_id = account['id']
            account_name = account['name']

            print(f"\n  Processing: {account_name} ({account_id})")

            # Try to assume role in the account
            assumed_session = self.assume_role(account_id)

            if not assumed_session:
                # If we can't assume role, try with current credentials
                # (in case it's the current account)
                if not self.dry_run:
                    try:
                        assumed_session = self.session
                    except:
                        print(f"  ⚠ Skipping account {account_id}")
                        continue
                else:
                    print(f"  ⚠ [DRY-RUN] Would skip account {account_id}")
                    continue

            # List FSX file systems
            fsx_systems = self.list_fsx_systems(assumed_session, account)

            if fsx_systems:
                for fsx in fsx_systems:
                    results.append({
                        'Organization Name': account_name,
                        'GovCloud Account ID': account_id,
                        'FSX ID': fsx['filesystem_id'],
                        'FSX Type': fsx['filesystem_type'],
                        'Region': fsx['region'],
                        'Lifecycle': fsx['lifecycle']
                    })
            else:
                print(f"  ℹ No FSX file systems found")

        return results

    def export_to_csv(self, results):
        """
        Export results to CSV file.

        Args:
            results: List of FSX inventory results

        Returns:
            str: Output filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'govcloud_fsx_inventory_{timestamp}.csv'

        if self.dry_run:
            print(f"\n→ [DRY-RUN] Would write {len(results)} result(s) to {output_file}")
            print(f"  [DRY-RUN] CSV columns: Organization Name, GovCloud Account ID, FSX ID, FSX Type, Region, Lifecycle")
            if results:
                print(f"\n  [DRY-RUN] Sample data (first 3 rows):")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result['Organization Name']} | {result['GovCloud Account ID']} | {result['FSX ID']}")
            return output_file

        if results:
            print(f"\n→ Writing results to {output_file}...")
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ['Organization Name', 'GovCloud Account ID', 'FSX ID',
                             'FSX Type', 'Region', 'Lifecycle']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(results)

            print(f"✓ Successfully wrote {len(results)} FSX system(s) to {output_file}")
        else:
            print("\n⚠ No FSX file systems found in any account")

        return output_file

    def run(self):
        """
        Execute the full inventory process.
        """
        print("=" * 60)
        print("AWS GovCloud FSX Inventory Script")
        if self.dry_run:
            print("[DRY-RUN MODE - No actual AWS API calls will be made]")
        print("=" * 60)

        if self.profile_name:
            print(f"\n→ Using AWS profile: {self.profile_name}")
        else:
            print("\n→ Using default AWS credentials")

        # Connect to AWS
        print("\n→ Authenticating with AWS SSO...")
        if not self.connect():
            sys.exit(1)

        # List accounts
        accounts = self.list_accounts()
        if not accounts:
            print("ERROR: No accounts found or accessible")
            sys.exit(1)

        # Scan accounts for FSX systems
        results = self.scan_accounts(accounts)

        # Export to CSV
        self.export_to_csv(results)

        print("\n" + "=" * 60)
        print("Scan complete!")
        print("=" * 60)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='List FSX file systems from GovCloud accounts in an AWS Organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --profile my-commercial-account
  %(prog)s --profile my-commercial-account --dry-run
  %(prog)s --dry-run --role-name CustomRoleName
        """
    )

    parser.add_argument(
        '--profile',
        '-p',
        help='AWS CLI profile name to use',
        default=None
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate the operations without making actual AWS API calls'
    )

    parser.add_argument(
        '--role-name',
        '-r',
        help='IAM role name to assume in target accounts (default: OrganizationAccountAccessRole)',
        default='OrganizationAccountAccessRole'
    )

    args = parser.parse_args()

    # Create and run inventory
    inventory = GovCloudFSXInventory(
        profile_name=args.profile,
        dry_run=args.dry_run,
        role_name=args.role_name
    )

    inventory.run()


if __name__ == '__main__':
    main()
