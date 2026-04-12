#!/usr/bin/env python3
"""
dashboard.py — Streamlit dashboard for the AWS GenAI Lab Guide.

Provides five tabs:
  1. Resource Inventory — all resources tagged Project=genai-lab-guide
  2. Cost Tracker — 7-day spend breakdown via Cost Explorer
  3. Bedrock Usage — recent CloudTrail events for bedrock.amazonaws.com
  4. OpenSearch Status — collection health + index listing
  5. Health Check — prerequisite validation (credentials, bucket, roles, etc.)

Run:  streamlit run dashboard.py
"""

import streamlit as st
import boto3
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AWS GenAI Dashboard", layout="wide")
st.title("AWS GenAI Lab Guide — Resource Dashboard")

REGION = "us-east-1"
session = boto3.Session(region_name=REGION)
sts = session.client("sts")
identity = sts.get_caller_identity()
ACCOUNT_ID = identity["Account"]

BUCKET = f"aws-genai-lab-{ACCOUNT_ID}"
BEDROCK_ROLE = "genai-lab-bedrock-role"
LAMBDA_ROLE = "genai-lab-lambda-role"
COLLECTION_NAME = "genai-lab-vectors"

st.sidebar.write(f"**Account:** {ACCOUNT_ID}")
st.sidebar.write(f"**Region:** {REGION}")
st.sidebar.write(f"**Bucket:** {BUCKET}")
st.sidebar.write(f"**Last refreshed:** {datetime.now().strftime('%H:%M:%S')}")

if st.sidebar.button("Refresh"):
    st.rerun()

# ---------------------------------------------------------------------------
# Helper — build console link from ARN
# ---------------------------------------------------------------------------

def console_link(arn: str) -> str:
    """Return an approximate AWS Console URL for a given ARN."""
    if ":s3:::" in arn:
        name = arn.split(":::")[-1]
        return f"https://s3.console.aws.amazon.com/s3/buckets/{name}"
    if ":iam::" in arn and ":role/" in arn:
        role_name = arn.split("/")[-1]
        return f"https://console.aws.amazon.com/iam/home#/roles/{role_name}"
    if ":aoss:" in arn:
        return f"https://{REGION}.console.aws.amazon.com/aos/home?region={REGION}#opensearch/collections"
    if ":bedrock:" in arn and "knowledge-base" in arn:
        kb_id = arn.split("/")[-1]
        return f"https://{REGION}.console.aws.amazon.com/bedrock/home?region={REGION}#/knowledge-bases/{kb_id}"
    if ":bedrock:" in arn and "guardrail" in arn:
        gr_id = arn.split("/")[-1]
        return f"https://{REGION}.console.aws.amazon.com/bedrock/home?region={REGION}#/guardrails/{gr_id}"
    return f"https://{REGION}.console.aws.amazon.com/"


def resource_type_label(arn: str) -> str:
    """Return a human-readable resource type from an ARN."""
    if ":s3:::" in arn:
        return "S3 Bucket"
    if ":iam::" in arn and ":role/" in arn:
        return "IAM Role"
    if ":aoss:" in arn:
        return "OpenSearch Serverless"
    if ":bedrock:" in arn and "knowledge-base" in arn:
        return "Bedrock Knowledge Base"
    if ":bedrock:" in arn and "guardrail" in arn:
        return "Bedrock Guardrail"
    if ":bedrock:" in arn and "agent" in arn:
        return "Bedrock Agent"
    # Fallback — extract from ARN
    parts = arn.split(":")
    if len(parts) >= 3:
        return parts[2].upper()
    return "Unknown"


def resource_name(arn: str) -> str:
    """Extract a short name from an ARN."""
    if "/" in arn:
        return arn.split("/")[-1]
    if ":::" in arn:
        return arn.split(":::")[-1]
    return arn.split(":")[-1]


def which_lab(arn: str) -> str:
    """Map a resource ARN to the lab/script that created it."""
    name = resource_name(arn).lower()
    rtype = arn.lower()
    if ":s3:::" in rtype:
        return "setup-resources.py"
    if ":iam::" in rtype and ":role/" in rtype:
        return "setup-resources.py"
    if ":aoss:" in rtype:
        return "setup-resources.py (Labs 04, 05)"
    if "knowledge-base" in rtype:
        return "Lab 05"
    if "guardrail" in rtype:
        return "Lab 10"
    if "agent" in rtype:
        return "Lab 06"
    return "—"


# ═══════════════════════════════════════════════════════════════════════════
# Tabs
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resource Inventory",
    "Cost Tracker",
    "Bedrock Usage",
    "OpenSearch Status",
    "Health Check",
])


# ═══════════════════════════════════════════════════════════════════════════
# Tab 1 — Resource Inventory
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("Resource Inventory")
    st.write("All resources tagged `Project = genai-lab-guide`, plus direct checks.")

    rows = []

    # --- Tagged resources via Resource Groups Tagging API ---------------
    tagging = session.client("resourcegroupstaggingapi")
    try:
        paginator = tagging.get_paginator("get_resources")
        for page in paginator.paginate(
            TagFilters=[{"Key": "Project", "Values": ["genai-lab-guide"]}]
        ):
            for r in page.get("ResourceTagMappingList", []):
                arn = r["ResourceARN"]
                rows.append({
                    "Resource Name": resource_name(arn),
                    "Type": resource_type_label(arn),
                    "Status": "Tagged",
                    "Created By": which_lab(arn),
                    "Console Link": console_link(arn),
                })
    except ClientError as e:
        st.warning(f"Could not query tagged resources: {e}")

    # --- Direct checks — S3 bucket ------------------------------------
    s3 = session.client("s3")
    try:
        s3.head_bucket(Bucket=BUCKET)
        arn = f"arn:aws:s3:::{BUCKET}"
        if not any(r["Resource Name"] == BUCKET for r in rows):
            rows.append({
                "Resource Name": BUCKET,
                "Type": "S3 Bucket",
                "Status": "Exists",
                "Created By": "setup-resources.py",
                "Console Link": console_link(arn),
            })
    except ClientError:
        pass

    # --- Direct checks — IAM roles ------------------------------------
    iam = session.client("iam")
    for role_name in [BEDROCK_ROLE, LAMBDA_ROLE]:
        try:
            iam.get_role(RoleName=role_name)
            arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
            if not any(r["Resource Name"] == role_name for r in rows):
                rows.append({
                    "Resource Name": role_name,
                    "Type": "IAM Role",
                    "Status": "Exists",
                    "Created By": "setup-resources.py",
                    "Console Link": console_link(arn),
                })
        except ClientError:
            pass

    # --- Direct checks — OpenSearch collection ------------------------
    aoss = session.client("opensearchserverless")
    try:
        resp = aoss.batch_get_collection(names=[COLLECTION_NAME])
        for coll in resp.get("collectionDetails", []):
            arn = coll["arn"]
            if not any(r["Resource Name"] == COLLECTION_NAME for r in rows):
                rows.append({
                    "Resource Name": coll["name"],
                    "Type": "OpenSearch Serverless",
                    "Status": coll.get("status", "—"),
                    "Created By": "setup-resources.py (Labs 04, 05)",
                    "Console Link": console_link(arn),
                })
    except ClientError:
        pass

    if rows:
        st.dataframe(rows, use_container_width=True)
        st.info(f"Total resources found: **{len(rows)}**")
    else:
        st.warning("No lab resources found. Run `scripts/setup-resources.py` first.")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 2 — Cost Tracker
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("Cost Tracker — Last 7 Days")

    ce = session.client("ce")
    today = datetime.utcnow().date()
    start = today - timedelta(days=7)

    try:
        result = ce.get_cost_and_usage(
            TimePeriod={
                "Start": start.strftime("%Y-%m-%d"),
                "End": today.strftime("%Y-%m-%d"),
            },
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        # Build daily totals and per-service totals
        daily_totals = {}
        service_totals = {}

        for period in result.get("ResultsByTime", []):
            day = period["TimePeriod"]["Start"]
            day_total = 0.0
            for group in period.get("Groups", []):
                service = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                service_totals[service] = service_totals.get(service, 0.0) + amount
                day_total += amount
            daily_totals[day] = day_total

        # Daily spend bar chart
        if daily_totals:
            st.subheader("Daily Spend")
            st.bar_chart(daily_totals)

        # Service breakdown table
        if service_totals:
            total_spend = sum(service_totals.values())
            projected_monthly = (total_spend / 7) * 30

            st.subheader("Spend by Service")
            svc_rows = [
                {"Service": svc, "Cost (USD)": f"${cost:.4f}"}
                for svc, cost in sorted(
                    service_totals.items(), key=lambda x: x[1], reverse=True
                )
                if cost > 0.0001
            ]
            st.dataframe(svc_rows, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("Total (7 days)", f"${total_spend:.2f}")
            col2.metric("Projected Monthly", f"${projected_monthly:.2f}")

            st.warning(
                "**OpenSearch Serverless is your #1 cost** — it runs 24/7 "
                "even with zero queries. Run `scripts/cleanup-all.py` when you "
                "are done with the labs to avoid ongoing charges."
            )
        else:
            st.info("No cost data available for the last 7 days.")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            st.error(
                "**Cost Explorer access denied.** Cost Explorer must be enabled in "
                "the AWS Billing console (it can take up to 24 hours to activate). "
                "Go to: https://console.aws.amazon.com/billing/home#/costexplorer"
            )
        else:
            st.error(f"Cost Explorer error: {e}")
    except Exception as e:
        st.error(f"Unexpected error querying Cost Explorer: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 3 — Bedrock Usage
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("Bedrock Usage — Recent CloudTrail Events")

    cloudtrail = session.client("cloudtrail")

    try:
        events_resp = cloudtrail.lookup_events(
            LookupAttributes=[{
                "AttributeKey": "EventSource",
                "AttributeValue": "bedrock.amazonaws.com",
            }],
            MaxResults=20,
        )

        events = events_resp.get("Events", [])

        if events:
            # Event table
            event_rows = []
            action_counts = {}
            today_count = 0
            today_str = datetime.utcnow().strftime("%Y-%m-%d")

            for ev in events:
                ts = ev.get("EventTime", "")
                name = ev.get("EventName", "")
                user = ev.get("Username", "—")
                event_rows.append({
                    "Timestamp": str(ts),
                    "Event": name,
                    "User": user,
                })
                action_counts[name] = action_counts.get(name, 0) + 1
                if today_str in str(ts):
                    today_count += 1

            st.dataframe(event_rows, use_container_width=True)

            # Summary metrics
            st.subheader("Summary")
            col1, col2 = st.columns(2)
            col1.metric("Events shown", len(events))
            col2.metric("Calls today", today_count)

            st.subheader("Calls by API Action")
            action_rows = [
                {"Action": action, "Count": count}
                for action, count in sorted(
                    action_counts.items(), key=lambda x: x[1], reverse=True
                )
            ]
            st.dataframe(action_rows, use_container_width=True)
        else:
            st.info(
                "No recent Bedrock CloudTrail events found. "
                "Run one of the earlier labs first to generate API activity."
            )

    except ClientError as e:
        st.error(f"CloudTrail error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 4 — OpenSearch Status
# ═══════════════════════════════════════════════════════════════════════════

with tab4:
    st.header("OpenSearch Serverless — Collection Status")

    aoss = session.client("opensearchserverless")

    try:
        resp = aoss.batch_get_collection(names=[COLLECTION_NAME])
        collections = resp.get("collectionDetails", [])

        if collections:
            coll = collections[0]
            st.subheader(f"Collection: {coll['name']}")

            col1, col2 = st.columns(2)
            col1.write(f"**Status:** {coll.get('status', '—')}")
            col1.write(f"**ARN:** `{coll.get('arn', '—')}`")
            col2.write(f"**Created:** {coll.get('createdDate', '—')}")
            col2.write(f"**Last modified:** {coll.get('lastModifiedDate', '—')}")

            endpoint = coll.get("collectionEndpoint", "")
            if endpoint:
                st.write(f"**Endpoint:** `{endpoint}`")

                # Try to connect and list indices
                st.subheader("Indices")
                try:
                    from opensearchpy import OpenSearch, RequestsHttpConnection
                    from requests_aws4auth import AWS4Auth

                    credentials = session.get_credentials().get_frozen_credentials()
                    auth = AWS4Auth(
                        credentials.access_key,
                        credentials.secret_key,
                        REGION,
                        "aoss",
                        session_token=credentials.token,
                    )

                    host = endpoint.replace("https://", "")
                    client = OpenSearch(
                        hosts=[{"host": host, "port": 443}],
                        http_auth=auth,
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection,
                        timeout=10,
                    )

                    indices = client.cat.indices(format="json")
                    if indices:
                        idx_rows = []
                        for idx in indices:
                            idx_rows.append({
                                "Index": idx.get("index", "—"),
                                "Health": idx.get("health", "—"),
                                "Docs": idx.get("docs.count", "—"),
                                "Size": idx.get("store.size", "—"),
                            })
                        st.dataframe(idx_rows, use_container_width=True)
                    else:
                        st.info("No indices found in the collection.")

                except ImportError:
                    st.warning(
                        "Install `opensearch-py` and `requests-aws4auth` to "
                        "list indices: `pip install opensearch-py requests-aws4auth`"
                    )
                except Exception as e:
                    st.warning(f"Could not connect to OpenSearch: {e}")
            else:
                st.warning("Collection endpoint not yet available (still creating?).")
        else:
            errors = resp.get("collectionErrorDetails", [])
            if errors:
                st.warning(f"Collection not found: {errors[0].get('errorMessage', '—')}")
            else:
                st.info(
                    f"Collection `{COLLECTION_NAME}` does not exist. "
                    "Run `scripts/setup-resources.py` to create it."
                )

    except ClientError as e:
        st.error(f"OpenSearch Serverless error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 5 — Health Check
# ═══════════════════════════════════════════════════════════════════════════

with tab5:
    st.header("Health Check — Prerequisites")
    st.write("Validates that all lab prerequisites are in place.")

    # 1. AWS credentials
    try:
        sts.get_caller_identity()
        st.success("AWS credentials are valid")
    except Exception as e:
        st.error(f"AWS credentials invalid — fix: run `aws configure` or check your credentials file. Error: {e}")

    # 2. S3 bucket
    try:
        s3 = session.client("s3")
        s3.head_bucket(Bucket=BUCKET)
        st.success(f"S3 bucket `{BUCKET}` exists")
    except ClientError:
        st.error(
            f"S3 bucket `{BUCKET}` not found — "
            "fix: run `python scripts/setup-resources.py`"
        )

    # 3. IAM roles
    iam = session.client("iam")
    for role_name in [BEDROCK_ROLE, LAMBDA_ROLE]:
        try:
            iam.get_role(RoleName=role_name)
            st.success(f"IAM role `{role_name}` exists")
        except ClientError:
            st.error(
                f"IAM role `{role_name}` not found — "
                "fix: run `python scripts/setup-resources.py`"
            )

    # 4. OpenSearch collection
    try:
        resp = aoss.batch_get_collection(names=[COLLECTION_NAME])
        collections = resp.get("collectionDetails", [])
        if collections and collections[0].get("status") == "ACTIVE":
            st.success(f"OpenSearch collection `{COLLECTION_NAME}` is ACTIVE")
        elif collections:
            status = collections[0].get("status", "UNKNOWN")
            st.warning(
                f"OpenSearch collection `{COLLECTION_NAME}` status: {status} — "
                "wait for it to become ACTIVE"
            )
        else:
            st.error(
                f"OpenSearch collection `{COLLECTION_NAME}` not found — "
                "fix: run `python scripts/setup-resources.py`"
            )
    except ClientError as e:
        st.error(f"Could not check OpenSearch collection: {e}")

    # 5. Bedrock model access
    try:
        bedrock = session.client("bedrock")
        models = bedrock.list_foundation_models()
        model_count = len(models.get("modelSummaries", []))
        if model_count > 0:
            st.success(f"Bedrock model access confirmed ({model_count} models available)")
        else:
            st.error(
                "No Bedrock foundation models found — "
                "fix: enable model access in the Bedrock console"
            )
    except ClientError as e:
        st.error(
            f"Cannot access Bedrock — fix: check IAM permissions "
            f"and enable model access in the Bedrock console. Error: {e}"
        )

    st.divider()
    st.info(
        "If any checks fail, see `prerequisites.md` at the project root "
        "or run `scripts/check-prerequisites.sh` for detailed diagnostics."
    )
