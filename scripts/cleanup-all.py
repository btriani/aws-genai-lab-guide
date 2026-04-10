#!/usr/bin/env python3
"""
cleanup-all.py — Tear down all shared infrastructure created by setup-resources.py.

Deletes (in reverse order of creation):
  - SageMaker Studio domain + role (if exists)
  - OpenSearch Serverless collection + policies
  - IAM roles (genai-lab-bedrock-role, genai-lab-lambda-role)
  - S3 bucket (aws-genai-lab-{account-id})
  - Downloaded whitepapers from assets/aws-whitepapers/
"""

import glob
import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
WHITEPAPER_DIR = os.path.join(PROJECT_ROOT, "assets", "aws-whitepapers")

# Resource names (must match setup-resources.py)
BEDROCK_ROLE_NAME = "genai-lab-bedrock-role"
LAMBDA_ROLE_NAME = "genai-lab-lambda-role"
SAGEMAKER_ROLE_NAME = "genai-lab-sagemaker-role"
COLLECTION_NAME = "genai-lab-vectors"
SAGEMAKER_DOMAIN_NAME = "genai-lab-studio"

# OpenSearch Serverless policy names
ENC_POLICY_NAME = "genai-lab-enc"
NET_POLICY_NAME = "genai-lab-net"
DATA_POLICY_NAME = "genai-lab-data"


# ---------------------------------------------------------------------------
# SageMaker cleanup
# ---------------------------------------------------------------------------

def delete_sagemaker_domain(sm, iam):
    """Delete SageMaker Studio domain and its execution role if they exist."""
    print("\n[1/5] SageMaker Studio domain")
    print("-" * 50)

    # Find domain by name
    domain_id = None
    try:
        domains = sm.list_domains()
        for d in domains.get("Domains", []):
            if d["DomainName"] == SAGEMAKER_DOMAIN_NAME:
                domain_id = d["DomainId"]
                break
    except ClientError as e:
        print(f"  ERROR Could not list SageMaker domains: {e}")
        return

    if domain_id is None:
        print(f"  SKIP  Domain not found: {SAGEMAKER_DOMAIN_NAME}")
    else:
        # Delete user profiles first
        try:
            profiles = sm.list_user_profiles(DomainIdEquals=domain_id)
            for profile in profiles.get("UserProfiles", []):
                name = profile["UserProfileName"]
                print(f"  DEL   User profile: {name}")
                sm.delete_user_profile(
                    DomainId=domain_id,
                    UserProfileName=name,
                )
                print(f"  OK    Deleted user profile: {name}")
        except ClientError as e:
            print(f"  ERROR Could not delete user profiles: {e}")

        # Delete domain
        print(f"  DEL   Domain: {SAGEMAKER_DOMAIN_NAME} (id: {domain_id})")
        try:
            sm.delete_domain(
                DomainId=domain_id,
                RetentionPolicy={"HomeEfsFileSystem": "Delete"},
            )
            print(f"  OK    Domain deletion initiated: {SAGEMAKER_DOMAIN_NAME}")
            print("        (Full deletion may take several minutes)")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ResourceNotFound":
                print(f"  SKIP  Domain already deleted: {SAGEMAKER_DOMAIN_NAME}")
            else:
                print(f"  ERROR Could not delete domain: {e}")

    # Delete SageMaker execution role
    _delete_iam_role(iam, SAGEMAKER_ROLE_NAME, managed_policies=True)


# ---------------------------------------------------------------------------
# OpenSearch Serverless cleanup
# ---------------------------------------------------------------------------

def delete_opensearch_collection(aoss):
    """Delete the OpenSearch Serverless collection and its policies."""
    print("\n[2/5] OpenSearch Serverless collection")
    print("-" * 50)

    # Find and delete the collection
    collection_id = None
    try:
        result = aoss.batch_get_collection(names=[COLLECTION_NAME])
        details = result.get("collectionDetails", [])
        if details:
            collection_id = details[0]["id"]
    except ClientError as e:
        print(f"  WARN  Could not look up collection: {e}")

    if collection_id:
        print(f"  DEL   Collection: {COLLECTION_NAME} (id: {collection_id})")
        try:
            aoss.delete_collection(id=collection_id)
            print(f"  OK    Collection deletion initiated: {COLLECTION_NAME}")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ResourceNotFoundException":
                print(f"  SKIP  Collection already deleted: {COLLECTION_NAME}")
            else:
                print(f"  ERROR Could not delete collection: {e}")
    else:
        print(f"  SKIP  Collection not found: {COLLECTION_NAME}")

    # Delete data access policy
    print(f"  DEL   Data access policy: {DATA_POLICY_NAME}")
    try:
        aoss.delete_access_policy(name=DATA_POLICY_NAME, type="data")
        print(f"  OK    Deleted: {DATA_POLICY_NAME}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("ResourceNotFoundException", "ConflictException"):
            print(f"  SKIP  Policy not found: {DATA_POLICY_NAME}")
        else:
            print(f"  ERROR Could not delete policy: {e}")

    # Delete network policy
    print(f"  DEL   Network policy: {NET_POLICY_NAME}")
    try:
        aoss.delete_security_policy(name=NET_POLICY_NAME, type="network")
        print(f"  OK    Deleted: {NET_POLICY_NAME}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("ResourceNotFoundException", "ConflictException"):
            print(f"  SKIP  Policy not found: {NET_POLICY_NAME}")
        else:
            print(f"  ERROR Could not delete policy: {e}")

    # Delete encryption policy
    print(f"  DEL   Encryption policy: {ENC_POLICY_NAME}")
    try:
        aoss.delete_security_policy(name=ENC_POLICY_NAME, type="encryption")
        print(f"  OK    Deleted: {ENC_POLICY_NAME}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("ResourceNotFoundException", "ConflictException"):
            print(f"  SKIP  Policy not found: {ENC_POLICY_NAME}")
        else:
            print(f"  ERROR Could not delete policy: {e}")


# ---------------------------------------------------------------------------
# IAM cleanup
# ---------------------------------------------------------------------------

def _delete_iam_role(iam, role_name, managed_policies=False):
    """Delete an IAM role after removing all inline (and optionally managed) policies."""
    print(f"  DEL   Role: {role_name}")

    try:
        # Remove inline policies
        inline = iam.list_role_policies(RoleName=role_name)
        for policy_name in inline.get("PolicyNames", []):
            print(f"        Removing inline policy: {policy_name}")
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        # Remove managed policies (for SageMaker role)
        if managed_policies:
            attached = iam.list_attached_role_policies(RoleName=role_name)
            for policy in attached.get("AttachedPolicies", []):
                print(f"        Detaching managed policy: {policy['PolicyName']}")
                iam.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy["PolicyArn"],
                )

        iam.delete_role(RoleName=role_name)
        print(f"  OK    Deleted role: {role_name}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NoSuchEntity":
            print(f"  SKIP  Role not found: {role_name}")
        else:
            print(f"  ERROR Could not delete role: {e}")


def delete_iam_roles(iam):
    """Delete the Bedrock and Lambda IAM roles."""
    print("\n[3/5] IAM roles")
    print("-" * 50)

    _delete_iam_role(iam, BEDROCK_ROLE_NAME)
    _delete_iam_role(iam, LAMBDA_ROLE_NAME)


# ---------------------------------------------------------------------------
# S3 cleanup
# ---------------------------------------------------------------------------

def delete_s3_bucket(s3, bucket_name):
    """Empty and delete the S3 bucket."""
    print(f"\n[4/5] S3 bucket: {bucket_name}")
    print("-" * 50)

    # Check if bucket exists
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            print(f"  SKIP  Bucket not found: {bucket_name}")
            return
        else:
            print(f"  ERROR Could not access bucket: {e}")
            return

    # Empty the bucket
    print(f"  DEL   Emptying bucket: {bucket_name}")
    deleted_count = 0
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get("Contents", [])
            if not objects:
                continue
            delete_keys = [{"Key": obj["Key"]} for obj in objects]
            s3.delete_objects(
                Bucket=bucket_name,
                Delete={"Objects": delete_keys},
            )
            deleted_count += len(delete_keys)
    except ClientError as e:
        print(f"  ERROR Could not empty bucket: {e}")
        return

    print(f"  OK    Removed {deleted_count} object(s)")

    # Delete the bucket
    print(f"  DEL   Deleting bucket: {bucket_name}")
    try:
        s3.delete_bucket(Bucket=bucket_name)
        print(f"  OK    Deleted bucket: {bucket_name}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NoSuchBucket":
            print(f"  SKIP  Bucket already deleted: {bucket_name}")
        else:
            print(f"  ERROR Could not delete bucket: {e}")


# ---------------------------------------------------------------------------
# Whitepaper cleanup
# ---------------------------------------------------------------------------

def delete_whitepapers():
    """Remove downloaded PDF (and placeholder .txt) files from assets/aws-whitepapers/."""
    print(f"\n[5/5] Downloaded whitepapers")
    print("-" * 50)

    if not os.path.isdir(WHITEPAPER_DIR):
        print(f"  SKIP  Directory not found: {WHITEPAPER_DIR}")
        return

    pdf_files = glob.glob(os.path.join(WHITEPAPER_DIR, "*.pdf"))
    txt_files = glob.glob(os.path.join(WHITEPAPER_DIR, "*.txt"))
    files = pdf_files + txt_files

    if not files:
        print(f"  SKIP  No PDF/TXT files found in {WHITEPAPER_DIR}")
        return

    for f in files:
        fname = os.path.basename(f)
        try:
            os.remove(f)
            print(f"  OK    Removed: {fname}")
        except OSError as e:
            print(f"  ERROR Could not remove {fname}: {e}")


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------

def confirm_destroy(account_id, bucket_name):
    """Print what will be deleted and require interactive confirmation."""
    print("\n" + "=" * 60)
    print("AWS GenAI Lab Guide — Resource Cleanup Plan")
    print("=" * 60)
    print(f"\n  Account   : {account_id}")
    print(f"  Region    : {REGION}")
    print()
    print("  The following resources will be DELETED (if they exist):")
    print()
    print(f"  [1] SageMaker Studio domain : {SAGEMAKER_DOMAIN_NAME}")
    print(f"      SageMaker role           : {SAGEMAKER_ROLE_NAME}")
    print(f"  [2] OpenSearch collection    : {COLLECTION_NAME}")
    print(f"      Policies                 : {ENC_POLICY_NAME}, {NET_POLICY_NAME}, {DATA_POLICY_NAME}")
    print(f"  [3] IAM roles                : {BEDROCK_ROLE_NAME}, {LAMBDA_ROLE_NAME}")
    print(f"  [4] S3 bucket                : {bucket_name}  (all objects will be deleted)")
    print(f"  [5] Local whitepapers        : assets/aws-whitepapers/*.pdf")
    print()
    print("  THIS ACTION IS IRREVERSIBLE.")
    print()
    print("=" * 60)
    answer = input("\n  Type 'yes' to proceed: ").strip().lower()
    if answer != "yes":
        print("\n  Aborted. No resources were deleted.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Get caller identity
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    account_id = identity["Account"]

    bucket_name = f"aws-genai-lab-{account_id}"

    # Confirmation
    confirm_destroy(account_id, bucket_name)

    print("\n" + "=" * 60)
    print("Starting resource cleanup ...")
    print("=" * 60)

    # Clients
    sm = boto3.client("sagemaker", region_name=REGION)
    aoss = boto3.client("opensearchserverless", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)

    # Step 1 — SageMaker (reverse order: last created, first deleted)
    delete_sagemaker_domain(sm, iam)

    # Step 2 — OpenSearch Serverless
    delete_opensearch_collection(aoss)

    # Step 3 — IAM roles
    delete_iam_roles(iam)

    # Step 4 — S3 bucket
    delete_s3_bucket(s3, bucket_name)

    # Step 5 — Local whitepapers
    delete_whitepapers()

    # Done
    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
