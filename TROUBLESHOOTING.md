# Troubleshooting & Lessons Learned

Real issues encountered while building and testing these labs — the kind of problems that don't show up in documentation but will save you hours of debugging.

## Model IDs Change Without Warning

**What happened:** Every Bedrock model ID we originally used became deprecated or removed within months. Claude 3.5 Sonnet, Titan Text Express — gone. The labs silently failed with cryptic `ResourceNotFoundException` errors.

**What we learned:**
- Newer Anthropic and Meta models now require **inference profile IDs** (prefixed with `us.` or `global.`) instead of direct model IDs
- Amazon Titan Text models have been retired entirely — only Titan Embeddings remain
- Always check model availability before starting: `aws bedrock list-foundation-models --region us-east-1`

**Current working model IDs (as of April 2026):**

| Model | ID |
|-------|-----|
| Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Titan Embeddings V2 | `amazon.titan-embed-text-v2:0` (still uses direct ID) |
| Llama 3 8B Instruct | `meta.llama3-8b-instruct-v1:0` (still uses direct ID) |
| Mistral 7B Instruct | `mistral.mistral-7b-instruct-v0:2` (still uses direct ID) |

> **Tip:** If you get `ValidationException: Invocation of model ID ... with on-demand throughput isn't supported`, add the `us.` prefix to the model ID.

---

## OpenSearch Serverless Is Not Regular OpenSearch

**What happened:** Standard OpenSearch API calls that work on managed domains fail silently or with `404` on Serverless collections.

**Specific gotchas:**
1. **`client.info()` returns 404** — Serverless does not support the root endpoint. Don't use it for connection verification.
2. **Document IDs are not supported** — you cannot pass `id=` when indexing documents. Serverless auto-generates IDs.
3. **Index creation needs time** — after creating an index, wait ~30 seconds before bulk-indexing documents. The index isn't immediately ready.
4. **Collection creation takes ~4 minutes** — the `setup-resources.py` script handles this with polling, but be patient.
5. **Minimum cost is ~$0.50/hour** — OpenSearch Serverless provisions a minimum of 2 OCUs. Run Labs 04-05 in the same session and clean up after.

```python
# WRONG — fails on Serverless
info = oss_client.info()

# RIGHT — just use it directly
print(f"Connected to OpenSearch Serverless at {COLLECTION_HOST}")
```

---

## IAM Role Descriptions Reject Special Characters

**What happened:** The setup script used an em dash (`—`) in IAM role descriptions. AWS IAM rejects any character outside the basic ASCII + Latin-1 range with a validation error.

**Fix:** Stick to basic ASCII in all IAM resource descriptions, names, and tags.

```python
# WRONG
Description="AWS GenAI Lab Guide — bedrock role"

# RIGHT
Description="AWS GenAI Lab Guide - bedrock role"
```

---

## Bedrock Knowledge Base Requires Pre-Created Index

**What happened:** Creating a Knowledge Base that points to an OpenSearch Serverless collection fails if the vector index doesn't already exist. The error message is not helpful.

**What you need to do:** Before calling `create_knowledge_base()`, create the index in OpenSearch Serverless with the exact field names the KB expects:

```python
index_body = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "embedding": {"type": "knn_vector", "dimension": 1024,
                          "method": {"engine": "faiss", "name": "hnsw"}},
            "text": {"type": "text"},
            "metadata": {"type": "text"}
        }
    }
}
oss_client.indices.create(index="kb-vectors", body=index_body)
```

The field names (`embedding`, `text`, `metadata`) must match the `fieldMapping` in your KB's `storageConfiguration`.

---

## Bedrock Agents Need Readiness Polling

**What happened:** After calling `create_agent()`, immediately calling `create_agent_action_group()` fails because the agent is still in `CREATING` state.

**Fix:** Poll the agent status before adding action groups or preparing:

```python
while True:
    agent_info = bedrock_agent_client.get_agent(agentId=AGENT_ID)
    status = agent_info["agent"]["agentStatus"]
    if status != "CREATING":
        break
    time.sleep(5)
```

---

## LLMs Wrap JSON in Markdown Code Fences

**What happened:** When asking Claude to return "ONLY valid JSON", it sometimes wraps the response in ` ```json ... ``` ` markdown formatting. This breaks `json.loads()` with a cryptic `JSONDecodeError: Expecting value` error.

**Fix:** Always strip markdown fences before parsing:

```python
result = invoke(prompt, temperature=0.0)

# Strip markdown code fences if present
cleaned = result.strip()
if cleaned.startswith("```"):
    cleaned = cleaned.split("\n", 1)[1]     # remove ```json line
    cleaned = cleaned.rsplit("```", 1)[0]   # remove closing ```

parsed = json.loads(cleaned.strip())
```

> **Tip:** Adding `"no markdown formatting"` to the prompt reduces this, but doesn't eliminate it. Always include the stripping logic as a safety net.

---

## Bedrock API Throttling Under Load

**What happened:** Labs 08 and 09 make many rapid API calls (model comparison, benchmarking). After ~10 calls in quick succession, Bedrock returns `ThrottlingException`.

**Fix:** Add exponential backoff retry logic:

```python
import time
import random

def invoke_with_retry(model_id, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return bedrock_runtime.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 256}
            )
        except bedrock_runtime.exceptions.ThrottlingException:
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"  Throttled, retrying in {wait:.1f}s...")
            time.sleep(wait)
    raise Exception(f"Failed after {max_retries} retries")
```

---

## Step Functions + Bedrock InvokeModel Formatting

**What happened:** The Step Functions Bedrock integration (`arn:aws:states:::bedrock:invokeModel`) uses Amazon States Language (ASL) which has strict rules about string interpolation. You cannot use `States.Format()` inside nested JSON structures the way you'd expect.

**What works:** Use Pass states to build the request body, then pipe it into the InvokeModel state. Or use simpler prompt structures that don't require interpolation.

---

## Bash Script Arithmetic + `set -e` = Silent Failure

**What happened:** The prerequisites check script used `((PASS++))` to count results. In bash, when `PASS` starts at 0, `((0++))` evaluates to 0 (falsy), which triggers `set -e` to abort the script after the first successful check.

**Fix:** Remove `set -e` from scripts that use arithmetic, or use `PASS=$((PASS + 1))` instead:

```bash
# WRONG with set -e
set -euo pipefail
PASS=0
((PASS++))  # exits the script because 0++ evaluates to 0 (false)

# RIGHT — remove set -e
set -uo pipefail

# OR use assignment form (always succeeds)
PASS=$((PASS + 1))
```

---

## Finding Your Resources in the AWS Console

If you can't find the lab resources after running `setup-resources.py`:

1. **Check the region** — all resources are in **us-east-1 (N. Virginia)**. Look at the top-right corner of the AWS Console.
2. **S3** — search for `aws-genai-lab-` in the [S3 Console](https://s3.console.aws.amazon.com/s3/buckets)
3. **IAM Roles** — search `genai-lab` in [IAM Console](https://console.aws.amazon.com/iam/) → Roles
4. **OpenSearch Serverless** — go to [OpenSearch Console](https://us-east-1.console.aws.amazon.com/aos/home?region=us-east-1#opensearch/collections) → **Serverless** section (not Domains) → Collections
5. **Knowledge Bases** — [Bedrock Console](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/knowledge-bases) → Knowledge bases (created by Lab 05)
6. **Guardrails** — [Bedrock Console](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/guardrails) → Guardrails (created/cleaned by Lab 10)

---

## Cost Surprises

**OpenSearch Serverless** is the #1 cost risk. It charges a minimum of ~$0.50/hour (2 OCUs) as soon as the collection is created, even if you're not using it. Run `python scripts/cleanup-all.py` when you're done studying.

**Fine-tuning (Lab 02)** costs $8-12 per run. If you're budget-conscious, read through the lab to understand the concepts but skip the actual training job.

See [COST-GUIDE.md](COST-GUIDE.md) for complete pricing details.
