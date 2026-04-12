#!/usr/bin/env python3
"""
setup-resources.py — Provision shared infrastructure for the AWS GenAI lab guide.

Creates:
  - S3 bucket (aws-genai-lab-{account-id})
  - IAM roles for Bedrock and Lambda
  - OpenSearch Serverless collection (genai-lab-vectors)
  - Downloads AWS whitepapers to assets/aws-whitepapers/
  - AWS Budget ($40/month cost protection)
  - Cost allocation tag activation (Project tag)

Optional:
  --sagemaker   Also create a SageMaker Studio domain
"""

import argparse
import json
import os
import sys
import time
import urllib.request

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
WHITEPAPER_DIR = os.path.join(PROJECT_ROOT, "assets", "aws-whitepapers")

# Tags applied to all resources — enables AWS Resource Group view
PROJECT_TAGS = {"Project": "genai-lab-guide", "Environment": "study"}

# ---------------------------------------------------------------------------
# Whitepaper downloads
# ---------------------------------------------------------------------------

WHITEPAPERS = {
    "aws-well-architected-framework.pdf": (
        "https://docs.aws.amazon.com/pdfs/wellarchitected/latest/framework/wellarchitected-framework.pdf"
    ),
    "generative-ai-on-aws.pdf": (
        "https://docs.aws.amazon.com/pdfs/wellarchitected/latest/machine-learning-lens/wellarchitected-machine-learning-lens.pdf"
    ),
    "amazon-bedrock-user-guide.pdf": (
        "https://docs.aws.amazon.com/pdfs/bedrock/latest/userguide/bedrock-ug.pdf"
    ),
    "aws-shared-responsibility-model.pdf": (
        "https://docs.aws.amazon.com/pdfs/whitepapers/latest/aws-risk-and-compliance/aws-risk-and-compliance.pdf"
    ),
}

PLACEHOLDER_TEXT = """\
This is a placeholder for: {name}

The automated download from the URL below did not succeed.
Please download the PDF manually and place it in this directory:

  URL : {url}
  Save: assets/aws-whitepapers/{name}
"""


def download_whitepapers():
    """Download AWS whitepapers (skip files that already exist)."""
    print("\n[1/7] Downloading AWS whitepapers")
    print("-" * 50)

    os.makedirs(WHITEPAPER_DIR, exist_ok=True)

    for filename, url in WHITEPAPERS.items():
        dest = os.path.join(WHITEPAPER_DIR, filename)
        if os.path.exists(dest):
            print(f"  SKIP  {filename}  (already exists)")
            continue

        print(f"  GET   {filename}")
        print(f"        {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  OK    {filename}  ({size_kb:.0f} KB)")
        except Exception as e:
            print(f"  WARN  Download failed: {e}")
            print(f"        Creating placeholder for {filename}")
            placeholder = PLACEHOLDER_TEXT.format(name=filename, url=url)
            txt_path = dest.replace(".pdf", ".txt")
            with open(txt_path, "w") as f:
                f.write(placeholder)
            print(f"  OK    {txt_path}")


# ---------------------------------------------------------------------------
# S3 bucket
# ---------------------------------------------------------------------------

def create_s3_bucket(s3, bucket_name):
    """Create the lab S3 bucket in us-east-1 (no LocationConstraint)."""
    print(f"\n[2/7] Creating S3 bucket: {bucket_name}")
    print("-" * 50)

    try:
        # us-east-1 must NOT include LocationConstraint
        s3.create_bucket(Bucket=bucket_name)
        print(f"  OK    Bucket created: {bucket_name}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"  SKIP  Bucket already exists: {bucket_name}")
        else:
            raise

    # Tag the bucket
    s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in PROJECT_TAGS.items()]},
    )
    print(f"  OK    Bucket tagged")

    # Upload whitepapers
    print(f"\n        Uploading whitepapers to s3://{bucket_name}/whitepapers/")
    for fname in os.listdir(WHITEPAPER_DIR):
        local_path = os.path.join(WHITEPAPER_DIR, fname)
        if not os.path.isfile(local_path):
            continue
        key = f"whitepapers/{fname}"
        print(f"  PUT   {key}")
        s3.upload_file(local_path, bucket_name, key)
    print("  OK    Whitepapers uploaded")


# ---------------------------------------------------------------------------
# IAM roles
# ---------------------------------------------------------------------------

def _trust_policy(service):
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": service},
                "Action": "sts:AssumeRole",
            }
        ],
    })


BEDROCK_ROLE_NAME = "genai-lab-bedrock-role"
LAMBDA_ROLE_NAME = "genai-lab-lambda-role"

BEDROCK_ROLE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockInvoke",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel",
            ],
            "Resource": "*",
        },
        {
            "Sid": "S3ReadWrite",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject",
            ],
            "Resource": [
                "arn:aws:s3:::aws-genai-lab-*",
                "arn:aws:s3:::aws-genai-lab-*/*",
            ],
        },
        {
            "Sid": "OpenSearchAccess",
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll",
            ],
            "Resource": "*",
        },
    ],
}

LAMBDA_ROLE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockInvoke",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            "Resource": "*",
        },
        {
            "Sid": "S3Read",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
            ],
            "Resource": [
                "arn:aws:s3:::aws-genai-lab-*",
                "arn:aws:s3:::aws-genai-lab-*/*",
            ],
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            "Resource": "arn:aws:logs:*:*:*",
        },
    ],
}


def _create_role(iam, role_name, trust_service, inline_policy):
    """Create an IAM role with an inline policy (skip if it already exists)."""
    try:
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=_trust_policy(trust_service),
            Description=f"AWS GenAI Lab Guide - {role_name}",
            MaxSessionDuration=3600,
        )
        print(f"  OK    Created role: {role_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"  SKIP  Role already exists: {role_name}")
        else:
            raise

    # Tag the role
    iam.tag_role(
        RoleName=role_name,
        Tags=[{"Key": k, "Value": v} for k, v in PROJECT_TAGS.items()],
    )

    # Attach / update inline policy
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=f"{role_name}-policy",
        PolicyDocument=json.dumps(inline_policy),
    )
    print(f"  OK    Inline policy attached to {role_name}")


def create_iam_roles(iam):
    """Create the Bedrock and Lambda IAM roles."""
    print("\n[3/7] Creating IAM roles")
    print("-" * 50)

    _create_role(iam, BEDROCK_ROLE_NAME, "bedrock.amazonaws.com", BEDROCK_ROLE_POLICY)
    _create_role(iam, LAMBDA_ROLE_NAME, "lambda.amazonaws.com", LAMBDA_ROLE_POLICY)


# ---------------------------------------------------------------------------
# OpenSearch Serverless
# ---------------------------------------------------------------------------

COLLECTION_NAME = "genai-lab-vectors"


def create_opensearch_collection(aoss, caller_arn):
    """Create an OpenSearch Serverless vector-search collection with policies."""
    print("\n[4/7] Creating OpenSearch Serverless collection")
    print("-" * 50)

    # --- Encryption policy ---------------------------------------------------
    enc_policy_name = "genai-lab-enc"
    enc_policy_doc = json.dumps({
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": [f"collection/{COLLECTION_NAME}"],
            }
        ],
        "AWSOwnedKey": True,
    })

    try:
        aoss.create_security_policy(
            name=enc_policy_name,
            type="encryption",
            policy=enc_policy_doc,
            description="Encryption policy for genai-lab-vectors",
        )
        print(f"  OK    Encryption policy created: {enc_policy_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            print(f"  SKIP  Encryption policy already exists: {enc_policy_name}")
        else:
            raise

    # --- Network policy -------------------------------------------------------
    net_policy_name = "genai-lab-net"
    net_policy_doc = json.dumps([
        {
            "Description": "Public access for lab simplicity",
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{COLLECTION_NAME}"],
                },
                {
                    "ResourceType": "dashboard",
                    "Resource": [f"collection/{COLLECTION_NAME}"],
                },
            ],
            "AllowFromPublic": True,
        }
    ])

    try:
        aoss.create_security_policy(
            name=net_policy_name,
            type="network",
            policy=net_policy_doc,
            description="Network policy for genai-lab-vectors",
        )
        print(f"  OK    Network policy created: {net_policy_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            print(f"  SKIP  Network policy already exists: {net_policy_name}")
        else:
            raise

    # --- Data access policy ---------------------------------------------------
    data_policy_name = "genai-lab-data"
    data_policy_doc = json.dumps([
        {
            "Description": "Data access for lab user and Bedrock role",
            "Rules": [
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{COLLECTION_NAME}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument",
                    ],
                },
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{COLLECTION_NAME}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems",
                    ],
                },
            ],
            "Principal": [
                caller_arn,
                f"arn:aws:iam::{caller_arn.split(':')[4]}:role/{BEDROCK_ROLE_NAME}",
            ],
        }
    ])

    try:
        aoss.create_access_policy(
            name=data_policy_name,
            type="data",
            policy=data_policy_doc,
            description="Data access policy for genai-lab-vectors",
        )
        print(f"  OK    Data access policy created: {data_policy_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            print(f"  SKIP  Data access policy already exists: {data_policy_name}")
        else:
            raise

    # --- Create collection ----------------------------------------------------
    try:
        resp = aoss.create_collection(
            name=COLLECTION_NAME,
            type="VECTORSEARCH",
            description="Vector store for AWS GenAI lab guide",
        )
        collection_id = resp["createCollectionDetail"]["id"]
        print(f"  OK    Collection created: {COLLECTION_NAME} (id: {collection_id})")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            print(f"  SKIP  Collection already exists: {COLLECTION_NAME}")
            # Retrieve existing collection id
            existing = aoss.batch_get_collection(
                names=[COLLECTION_NAME]
            )
            if existing["collectionDetails"]:
                collection_id = existing["collectionDetails"][0]["id"]
            else:
                print("  WARN  Could not retrieve collection details")
                return
        else:
            raise

    # --- Wait for ACTIVE status -----------------------------------------------
    print(f"\n        Waiting for collection to become ACTIVE ...")
    max_wait = 300  # 5 minutes
    elapsed = 0
    poll_interval = 10

    while elapsed < max_wait:
        result = aoss.batch_get_collection(ids=[collection_id])
        details = result.get("collectionDetails", [])
        if details:
            status = details[0].get("status", "UNKNOWN")
            endpoint = details[0].get("collectionEndpoint", "")
            print(f"        Status: {status}  ({elapsed}s elapsed)")
            if status == "ACTIVE":
                print(f"  OK    Collection is ACTIVE")
                print(f"        Endpoint: {endpoint}")
                # Tag the collection
                coll_arn = details[0].get("arn", "")
                if coll_arn:
                    aoss.tag_resource(
                        resourceArn=coll_arn,
                        tags=[{"key": k, "value": v} for k, v in PROJECT_TAGS.items()],
                    )
                    print(f"  OK    Collection tagged")
                return
            if status in ("FAILED", "DELETED"):
                print(f"  FAIL  Collection entered {status} state")
                sys.exit(1)
        time.sleep(poll_interval)
        elapsed += poll_interval

    print("  WARN  Timed out waiting for collection (it may still be creating)")
    print("        Check the OpenSearch Serverless console for status.")


# ---------------------------------------------------------------------------
# SageMaker (optional)
# ---------------------------------------------------------------------------

def create_sagemaker_domain(account_id):
    """Create a SageMaker Studio domain (optional, behind --sagemaker flag)."""
    print("\n[opt] Creating SageMaker Studio domain")
    print("-" * 50)

    sm = boto3.client("sagemaker", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)
    ec2 = boto3.client("ec2", region_name=REGION)

    # Get default VPC
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    if not vpcs["Vpcs"]:
        print("  FAIL  No default VPC found. Create one or pass a VPC manually.")
        return
    vpc_id = vpcs["Vpcs"][0]["VpcId"]

    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    subnet_ids = [s["SubnetId"] for s in subnets["Subnets"]][:2]

    # SageMaker execution role
    sm_role_name = "genai-lab-sagemaker-role"
    try:
        iam.create_role(
            RoleName=sm_role_name,
            AssumeRolePolicyDocument=_trust_policy("sagemaker.amazonaws.com"),
            Description="AWS GenAI Lab Guide - SageMaker execution role",
            Tags=[{"Key": k, "Value": v} for k, v in PROJECT_TAGS.items()],
        )
        iam.attach_role_policy(
            RoleName=sm_role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
        )
        print(f"  OK    Created SageMaker role: {sm_role_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"  SKIP  SageMaker role already exists: {sm_role_name}")
        else:
            raise

    sm_role_arn = f"arn:aws:iam::{account_id}:role/{sm_role_name}"

    domain_name = "genai-lab-studio"
    try:
        sm.create_domain(
            DomainName=domain_name,
            AuthMode="IAM",
            DefaultUserSettings={
                "ExecutionRole": sm_role_arn,
            },
            SubnetIds=subnet_ids,
            VpcId=vpc_id,
        )
        print(f"  OK    SageMaker domain creation started: {domain_name}")
        print("        This may take several minutes to complete.")
        print("        Check the SageMaker console for status.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceInUse":
            print(f"  SKIP  SageMaker domain already exists: {domain_name}")
        else:
            raise


# ---------------------------------------------------------------------------
# AWS Budget
# ---------------------------------------------------------------------------

def create_budget(account_id):
    """Create a $40 monthly budget for cost protection."""
    print("\n[6/7] Creating AWS Budget")
    print("-" * 50)

    budgets = boto3.client("budgets", region_name=REGION)
    try:
        budgets.create_budget(
            AccountId=account_id,
            Budget={
                "BudgetName": "genai-lab-guide",
                "BudgetLimit": {"Amount": "40", "Unit": "USD"},
                "TimeUnit": "MONTHLY",
                "BudgetType": "COST",
                "CostFilters": {},
                "CostTypes": {
                    "IncludeTax": True,
                    "IncludeSubscription": True,
                    "UseBlended": False,
                    "IncludeRefund": False,
                    "IncludeCredit": False,
                    "IncludeUpfront": True,
                    "IncludeRecurring": True,
                    "IncludeOtherSubscription": True,
                    "IncludeSupport": True,
                    "IncludeDiscount": True,
                    "UseAmortized": False,
                },
            },
            NotificationsWithSubscribers=[]  # No email — check in console
        )
        print("  OK    Budget created: genai-lab-guide ($40/month)")
    except ClientError as e:
        if "DuplicateRecordException" in str(e) or "already exists" in str(e).lower():
            print("  SKIP  Budget already exists: genai-lab-guide")
        else:
            print(f"  WARN  Could not create budget: {e}")
    print("        Check at: AWS Console > Billing > Budgets")


# ---------------------------------------------------------------------------
# Cost allocation tag
# ---------------------------------------------------------------------------

def activate_cost_tag():
    """Activate the Project tag for Cost Explorer filtering."""
    print("\n[7/7] Activating cost allocation tag")
    print("-" * 50)
    try:
        ce = boto3.client("ce", region_name=REGION)
        ce.update_cost_allocation_tags_status(
            CostAllocationTagsStatus=[
                {"TagKey": "Project", "Status": "Active"}
            ]
        )
        print("  OK    Cost allocation tag 'Project' activated")
        print("        Note: takes ~24 hours to appear in Cost Explorer")
    except ClientError as e:
        print(f"  WARN  Could not activate cost tag: {e}")
        print("        Manually activate at: Billing > Cost allocation tags")


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------

def confirm_plan(account_id, include_sagemaker):
    """Print what will be created and ask the user to confirm."""
    print("\n" + "=" * 60)
    print("AWS GenAI Lab Guide — Resource Setup Plan")
    print("=" * 60)
    print(f"\n  Account   : {account_id}")
    print(f"  Region    : {REGION}")
    print()
    print("  The following resources will be created:")
    print()
    print("  [1] Download 4 AWS whitepapers to assets/aws-whitepapers/")
    print(f"  [2] S3 bucket: aws-genai-lab-{account_id}")
    print(f"      └── Upload whitepapers to s3://aws-genai-lab-{account_id}/whitepapers/")
    print(f"  [3] IAM role: {BEDROCK_ROLE_NAME}  (trust: bedrock.amazonaws.com)")
    print(f"      IAM role: {LAMBDA_ROLE_NAME}   (trust: lambda.amazonaws.com)")
    print(f"  [4] OpenSearch Serverless collection: {COLLECTION_NAME}")
    print("      └── encryption, network, and data-access policies")
    print(f"  [5] Resource Group: genai-lab-guide")
    print(f"      └── All resources tagged with Project=genai-lab-guide")
    print(f"  [6] AWS Budget: genai-lab-guide ($40/month)")
    print(f"  [7] Activate cost allocation tag: Project")

    if include_sagemaker:
        print("  [opt] SageMaker Studio domain: genai-lab-studio")
        print("        └── SageMaker execution role: genai-lab-sagemaker-role")

    print()
    print("=" * 60)
    answer = input("\n  Type 'yes' to proceed: ").strip().lower()
    if answer != "yes":
        print("\n  Aborted. No resources were created.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Provision shared infrastructure for the AWS GenAI lab guide."
    )
    parser.add_argument(
        "--sagemaker",
        action="store_true",
        help="Also create a SageMaker Studio domain",
    )
    args = parser.parse_args()

    # Get caller identity
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    account_id = identity["Account"]
    caller_arn = identity["Arn"]

    bucket_name = f"aws-genai-lab-{account_id}"

    # Confirmation
    confirm_plan(account_id, args.sagemaker)

    print("\n" + "=" * 60)
    print("Starting resource provisioning ...")
    print("=" * 60)

    # Step 1 — Whitepapers
    download_whitepapers()

    # Step 2 — S3
    s3 = boto3.client("s3", region_name=REGION)
    create_s3_bucket(s3, bucket_name)

    # Step 3 — IAM
    iam = boto3.client("iam", region_name=REGION)
    create_iam_roles(iam)

    # Step 4 — OpenSearch Serverless
    aoss = boto3.client("opensearchserverless", region_name=REGION)
    create_opensearch_collection(aoss, caller_arn)

    # Step 5 (optional) — SageMaker
    if args.sagemaker:
        create_sagemaker_domain(account_id)

    # Step 5 — Resource Group (for easy console navigation)
    print("\n[5/7] Creating Resource Group")
    print("-" * 50)
    rg = boto3.client("resource-groups", region_name=REGION)
    try:
        rg.create_group(
            Name="genai-lab-guide",
            Description="All resources for the AWS GenAI Developer Lab Guide",
            ResourceQuery={
                "Type": "TAG_FILTERS_1_0",
                "Query": json.dumps({
                    "ResourceTypeFilters": ["AWS::AllSupported"],
                    "TagFilters": [{"Key": "Project", "Values": ["genai-lab-guide"]}],
                }),
            },
            Tags=PROJECT_TAGS,
        )
        print("  OK    Resource Group created: genai-lab-guide")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BadRequestException",) and "already exists" in str(e):
            print("  SKIP  Resource Group already exists: genai-lab-guide")
        else:
            # Non-critical — don't fail setup over this
            print(f"  WARN  Could not create Resource Group: {e}")
    print("        View all resources: AWS Console > Resource Groups > genai-lab-guide")

    # Step 6 — Budget
    create_budget(account_id)

    # Step 7 — Cost allocation tag
    activate_cost_tag()

    # Done
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"\n  S3 bucket        : s3://{bucket_name}")
    print(f"  Bedrock role     : arn:aws:iam::{account_id}:role/{BEDROCK_ROLE_NAME}")
    print(f"  Lambda role      : arn:aws:iam::{account_id}:role/{LAMBDA_ROLE_NAME}")
    print(f"  OpenSearch coll. : {COLLECTION_NAME}")
    print(f"  Resource Group   : genai-lab-guide")
    print(f"  Budget           : genai-lab-guide ($40/month)")
    if args.sagemaker:
        print(f"  SageMaker domain : genai-lab-studio")
    print(f"\n  All resources tagged: Project=genai-lab-guide")
    print(f"  View in console: Resource Groups > genai-lab-guide")
    print()


if __name__ == "__main__":
    main()
