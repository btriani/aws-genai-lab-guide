# Cost Guide

**Estimated total cost: ~$26-39**

This guide breaks down the estimated AWS costs for each lab so you can budget accordingly and avoid surprises.

---

## Per-Lab Cost Breakdown

| # | Lab | Compute | Model/API Calls | Other | Est. Total |
|---|-----|---------|----------------|-------|------------|
| 01 | Bedrock Foundation Models | — | ~$0.35 (multi-model) | — | ~$0.35 |
| 02 | Model Selection & Customization | SageMaker (~$1.50/hr if deployed) | ~$0.10 | Fine-tuning: ~$5-10 | ~$8-12 |
| 03 | Prompt Engineering | — | ~$0.30 (Claude) | — | ~$0.30 |
| 04 | Embeddings & Vector Search | — | ~$0.05 (Titan Embed) | OpenSearch: ~$2-3/hr | ~$2-3 |
| 05 | RAG with Knowledge Bases | — | ~$0.50 (embed + Claude) | OpenSearch: shared | ~$2-3 |
| 06 | Bedrock Agents | — | ~$0.50 (Claude + Lambda) | Lambda: free tier | ~$2-3 |
| 07 | Multi-Step Workflows | — | ~$0.20 (Llama 3 + Claude) | Step Functions: ~$0.01 | ~$0.20 |
| 08 | Model Evaluation | — | ~$0.60 (3 models) | Eval job: ~$1-2 | ~$2-3 |
| 09 | Inference Optimization | — | ~$1.00 (benchmarking) | Batch job: ~$1-2 | ~$3-5 |
| 10 | Guardrails & Responsible AI | — | ~$0.30 (Claude) | Guardrails: ~$0.75/1K assessments | ~$1-2 |
| 11 | Security & Governance | — | ~$0.10 | KMS: ~$1/month | ~$1 |
| 12 | Interactive GenAI Playground | — | ~$0.50 (multi-model chat) | — | ~$0.50 |
| 13 | Resource Dashboard & Cost Monitor | — | — | Cost Explorer: ~$0.01/query | ~$0.50 |

---

## Per-Service Pricing Reference

### Bedrock Model Invocation

Prices are per 1,000 tokens (on-demand pricing as of early 2026).

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|-----------------------|------------------------|
| Claude Sonnet 4.5 | $0.003 | $0.015 |
| Claude Haiku 4.5 | $0.0008 | $0.004 |
| Titan Embeddings V2 | $0.00002 | — |
| Llama 3 8B | $0.0003 | $0.0006 |
| Mistral 7B | $0.00015 | $0.0002 |

### OpenSearch Serverless

| Resource | Price |
|----------|-------|
| Indexing OCU | ~$0.24/hr per OCU |
| Search OCU | ~$0.24/hr per OCU |
| Minimum per collection | 2 OCUs (1 indexing + 1 search) |
| **Minimum hourly cost** | **~$0.48/hr** |

### SageMaker

| Instance Type | Price |
|---------------|-------|
| ml.g5.2xlarge | ~$1.50/hr |

### Lambda

| Resource | Price |
|----------|-------|
| First 1M requests/month | Free |
| Additional requests | $0.20 per 1M requests |
| Compute | $0.0000166667 per GB-second |

### S3

Negligible for lab data volumes. Standard storage costs $0.023/GB/month; lab datasets are typically under 100 MB.

---

## Understanding Cost Drivers

> **Warning: OpenSearch Serverless is the #1 cost risk in these labs.** Each collection requires a minimum of 2 OCUs (one indexing, one search) at ~$0.24/hr each. That is ~$0.48/hr just to keep a collection running — even if you are not querying it. Leaving a collection running overnight (8 hours) costs ~$3.84.

**Recommendation:** Only create your OpenSearch Serverless collection when you are actively working on Labs 04 and 05. Delete the collection immediately after completing those labs.

> **Warning: SageMaker endpoints also bill by the hour.** If Lab 02 deploys a model endpoint, delete it as soon as you finish experimenting. A single ml.g5.2xlarge endpoint left running overnight costs ~$12.

The model invocation costs (Bedrock API calls) are generally small — most labs cost well under $1 in API calls alone. The infrastructure costs (OpenSearch, SageMaker) are what drive the bill.

---

## Stop the Billing Clock

### After Each Session

**Delete SageMaker endpoints:**

```bash
# List active endpoints
aws sagemaker list-endpoints --status-equals InService

# Delete a specific endpoint
aws sagemaker delete-endpoint --endpoint-name <endpoint-name>

# Delete the endpoint configuration too
aws sagemaker delete-endpoint-config --endpoint-config-name <config-name>
```

**Check for running OpenSearch Serverless collections:**

```bash
# List collections
aws opensearchserverless list-collections

# Delete a collection (if done with Labs 04-05)
aws opensearchserverless delete-collection --id <collection-id>
```

> Note: OpenSearch Serverless OCUs continue to bill even when idle. If you are done with Labs 04-05, delete the collection.

### When Completely Done

Run the full cleanup script to tear down all lab resources:

```bash
python scripts/cleanup-all.py
```

If you prefer manual cleanup, delete resources in this order:

```bash
# 1. Delete SageMaker endpoints and configs
aws sagemaker list-endpoints --status-equals InService
aws sagemaker delete-endpoint --endpoint-name <name>

# 2. Delete OpenSearch Serverless collections
aws opensearchserverless list-collections
aws opensearchserverless delete-collection --id <id>

# 3. Delete Bedrock Knowledge Bases
aws bedrock-agent list-knowledge-bases
aws bedrock-agent delete-knowledge-base --knowledge-base-id <id>

# 4. Delete Bedrock Agents
aws bedrock-agent list-agents
aws bedrock-agent delete-agent --agent-id <id>

# 5. Delete Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'genai-lab')]"
aws lambda delete-function --function-name <name>

# 6. Delete S3 lab buckets
aws s3 ls | grep genai-lab
aws s3 rb s3://<bucket-name> --force

# 7. Delete IAM roles (created by labs)
aws iam list-roles --query "Roles[?starts_with(RoleName, 'genai-lab')]"
```

---

## Tips to Minimize Cost

1. **Run Labs 04-05 in one session.** Both labs use OpenSearch Serverless. By completing them back-to-back, you share the OCU uptime and avoid paying for a second spin-up.

2. **Skip Lab 02 fine-tuning if short on budget.** Fine-tuning is the single most expensive exercise (~$5-10). You can still learn the concepts by reading through the lab and studying the configuration without running the job.

3. **Use Haiku instead of Sonnet for experimentation.** When iterating on prompts or testing agent logic, Claude Haiku 4.5 costs roughly 5x less than Sonnet and responds faster. Switch to Sonnet only for final comparisons.

4. **Run `cleanup-all.py` when done studying.** Do not leave resources running between study sessions. A single forgotten OpenSearch collection or SageMaker endpoint can quietly add $10+ to your bill overnight.

5. **Monitor spend in the AWS Billing dashboard.** Go to **Billing and Cost Management > Bills** to see charges by service. Set up a **Budget** with an alert at $30 so you get notified before costs exceed your target.
