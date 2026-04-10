# Services Comparison Cheatsheet

![Architecture Overview](../assets/diagrams/architecture-overview.png)

> Side-by-side comparisons and decision guidance for every "which service should I use?" question on the **AWS Generative AI Specialty (DEP-C01)** exam. Each section includes a comparison table and concrete decision criteria.

---

## 1. Bedrock vs SageMaker JumpStart

| Feature | Amazon Bedrock | SageMaker JumpStart |
|---------|---------------|---------------------|
| **Model access** | Managed API (no infrastructure) | Deploy to SageMaker endpoints |
| **Infrastructure management** | None — fully serverless | You manage instance types, scaling, endpoints |
| **Available models** | Claude, Titan, Llama, Cohere, Mistral, Stability AI | Hundreds of open-source models (Hugging Face, Meta, etc.) |
| **Custom models** | Fine-tuning (limited models), Custom Model Import | Full training, fine-tuning, any framework |
| **Pricing model** | Per-token (on-demand) or per-hour (provisioned) | Per-hour for endpoint instances |
| **Scaling** | Automatic (on-demand), manual (provisioned) | Auto Scaling policies on endpoints |
| **RAG support** | Built-in Knowledge Bases | Manual setup (retrieve + prompt) |
| **Agents** | Built-in Bedrock Agents | Custom orchestration code |
| **Guardrails** | Built-in Bedrock Guardrails | Custom implementation |
| **Latency** | Variable (on-demand), guaranteed (provisioned) | Depends on instance type and model |
| **Max customization** | Limited (API-level) | Full (code, model, infrastructure) |
| **MLOps integration** | Basic (model versioning) | Full (Pipelines, Model Registry, Experiments) |

### When to Use Bedrock

- You want a **serverless, fully managed** experience with no infrastructure
- You need **built-in RAG** (Knowledge Bases) or **Agents**
- You want to use **multiple foundation models** via a single API (Converse)
- Your use case is covered by available Bedrock models
- You need **Guardrails** for content safety
- You want the **fastest time-to-production**

### When to Use SageMaker JumpStart

- You need a model **not available on Bedrock**
- You need **full control** over the hosting infrastructure (GPU type, instance count)
- You need **advanced MLOps** (model registry, A/B testing, shadow deployments)
- You need to run **custom training** with proprietary architectures
- You need **dedicated GPU instances** for guaranteed capacity
- You want to **fine-tune** a model that Bedrock does not support for fine-tuning

### When to Use Both Together

- **Bedrock for inference** (production API calls) + **SageMaker for training/fine-tuning** (then import custom model into Bedrock)
- **SageMaker for experimentation** (notebooks, evaluation) + **Bedrock for production deployment** (serverless scaling)

---

## 2. Vector Store Options

| Feature | OpenSearch Serverless | Aurora pgvector | Pinecone | Redis Enterprise Cloud |
|---------|----------------------|-----------------|----------|----------------------|
| **Type** | AWS managed, serverless | AWS managed (Aurora), extension | Third-party SaaS | Third-party SaaS (on AWS) |
| **Bedrock KB integration** | Native (default) | Native | Native | Native |
| **Scaling** | Automatic (OCU-based) | Manual (instance-based) | Automatic (pod-based) | Automatic (shard-based) |
| **Pricing model** | Per OCU-hour (~$0.24/hr min) | Per instance-hour | Per pod-hour + storage | Per shard-hour |
| **Minimum cost** | ~$350/month (2 OCU min) | ~$30/month (db.t4g.medium) | Free tier available | Contact sales |
| **Max dimensions** | 16,000 | 16,000 | 20,000 | 32,768 |
| **Hybrid search** | Yes (vector + keyword BM25) | Limited (pgvector + full-text) | Yes (sparse + dense) | Yes (vector + tag filter) |
| **Metadata filtering** | Yes | Yes (SQL WHERE) | Yes | Yes |
| **HNSW index** | Yes | Yes | Yes | Yes |
| **Serverless** | Yes | No (Aurora Serverless v2 = semi) | Yes | No |
| **AWS native** | Yes | Yes | No | No |
| **Setup complexity** | Medium | Medium | Low | Medium |

### Decision Guide — Vector Stores

- **Default choice for Bedrock Knowledge Bases** → OpenSearch Serverless (easiest integration, fully managed)
- **Already using Aurora PostgreSQL** → pgvector extension (avoid new service, leverage existing DB)
- **Need lowest cost for small workloads** → Aurora pgvector on small instance or Pinecone free tier
- **Need highest query performance at scale** → OpenSearch Serverless or Pinecone
- **Need hybrid search (vector + keyword)** → OpenSearch Serverless (best BM25 + kNN support)
- **Must stay fully within AWS** → OpenSearch Serverless or Aurora pgvector
- **Exam default answer** → OpenSearch Serverless (AWS-native, serverless, Bedrock default)

---

## 3. Knowledge Bases vs Custom RAG

| Feature | Bedrock Knowledge Bases (Managed) | Custom RAG Pipeline |
|---------|-----------------------------------|---------------------|
| **Ingestion** | Automatic (S3 sync, chunking, embedding) | You build (Lambda, Step Functions, etc.) |
| **Chunking** | Fixed-size, semantic, hierarchical, none | Any strategy you implement |
| **Embedding model** | Titan Embeddings V2, Cohere Embed (select from list) | Any model (Bedrock, SageMaker, external) |
| **Vector store** | OpenSearch, Aurora, Pinecone, Redis, MongoDB Atlas | Any store (including FAISS, Chroma, Weaviate, etc.) |
| **Retrieval** | `Retrieve` or `RetrieveAndGenerate` APIs | Custom query logic |
| **Generation** | Managed prompt with citations | Full prompt control |
| **Metadata filtering** | Supported | Full custom filters |
| **Data sources** | S3, Confluence, SharePoint, Salesforce, web crawler | Anything you can code |
| **Reranking** | Supported (Cohere Rerank) | Any reranker |
| **Prompt customization** | Limited (override prompt template) | Full control |
| **Multi-turn memory** | Managed session context | You implement |
| **Setup time** | Hours | Days to weeks |
| **Maintenance** | AWS managed | You maintain |
| **Cost transparency** | Bundled (harder to optimize individual steps) | Granular (optimize each component) |

### Decision Guide — KB vs Custom RAG

- **"Fastest path to production RAG"** → Knowledge Bases
- **"Need custom chunking logic (e.g., code-aware, table-aware)"** → Custom RAG
- **"Need to use a vector store not supported by KB (e.g., FAISS, Chroma)"** → Custom RAG
- **"Need full control over the generation prompt"** → Custom RAG with `Retrieve` API (get chunks, build your own prompt)
- **"Hybrid approach"** → Use Knowledge Bases for ingestion + storage, use `Retrieve` API for retrieval, build custom generation prompt
- **"Need citations and source attribution"** → Knowledge Bases `RetrieveAndGenerate` provides automatic citations
- **Exam default answer** → Knowledge Bases (unless the question specifies a requirement KB cannot meet)

---

## 4. Throughput Modes

| Feature | On-Demand | Provisioned Throughput | Batch Inference |
|---------|-----------|----------------------|-----------------|
| **Pricing** | Per input/output token | Per model unit per hour | ~50% of on-demand per token |
| **Commitment** | None | 1-month or 6-month | None |
| **Latency** | Variable (best-effort) | Guaranteed, consistent | Hours (async, not real-time) |
| **Throughput** | Shared capacity, may throttle | Dedicated capacity, guaranteed | Bulk processing |
| **Scaling** | Automatic (with limits) | Fixed (you choose units) | N/A |
| **Best for** | Development, variable traffic, low volume | Production with predictable high-volume traffic | Bulk offline processing |
| **API** | `InvokeModel` / `Converse` | Same APIs, specify provisioned model ARN | `CreateModelInvocationJob` |
| **Input format** | Single request | Single request | JSONL file in S3 |
| **Output** | Synchronous response | Synchronous response | JSONL file in S3 |
| **Availability** | All models | Select models | Select models |
| **Minimum cost** | $0 (pay per use) | ~$1,000+/month per unit | Per-job |

### Decision Guide — Throughput Modes

- **"Development or testing"** → On-demand (no commitment, pay only for what you use)
- **"Production chatbot with 1,000+ daily users"** → Provisioned throughput (guaranteed latency and capacity)
- **"Need to summarize 50,000 documents overnight"** → Batch inference (50% savings, async OK)
- **"Unpredictable traffic, sometimes zero"** → On-demand (no minimum cost)
- **"Compliance requires consistent response times"** → Provisioned throughput
- **"Budget is the top priority, latency can wait"** → Batch inference

### Cost Comparison Example (Claude Sonnet 4.5)

| Scenario | On-Demand | Provisioned | Batch |
|----------|-----------|-------------|-------|
| 1M input tokens | ~$3.00 | Included in hourly rate | ~$1.50 |
| 1M output tokens | ~$15.00 | Included in hourly rate | ~$7.50 |
| Monthly base cost | $0 | ~$1,000+/unit/month | $0 |

> **Exam tip:** If the question mentions "variable workloads" or "unpredictable traffic" → on-demand. If it mentions "guaranteed latency" or "predictable high volume" → provisioned. If it mentions "bulk processing" or "offline" → batch.

---

## 5. Agent Approaches

| Feature | Bedrock Agents | Custom Orchestration (Lambda/Step Functions) | LangChain / LangGraph |
|---------|---------------|----------------------------------------------|----------------------|
| **Reasoning** | Built-in ReAct | You implement logic | Built-in chains and agents |
| **Tool use** | Action groups (Lambda + OpenAPI) | Direct Lambda/API calls | Tool abstractions |
| **Knowledge base** | Native integration | Manual Retrieve API calls | Retriever abstractions |
| **Multi-turn memory** | Managed sessions | You implement (DynamoDB, etc.) | Memory abstractions |
| **Code interpreter** | Built-in | You build (Lambda, containers) | Code execution tools |
| **Observability** | Agent trace (CloudWatch) | Step Functions visual, X-Ray | LangSmith, callbacks |
| **Vendor lock-in** | AWS-specific | AWS services | Framework-specific, multi-cloud |
| **Deployment** | Bedrock managed | Lambda + Step Functions | EC2, ECS, Lambda (you host) |
| **Customization** | Limited (instruction, action groups) | Full control over every step | Full control, many prebuilt patterns |
| **Production readiness** | High (managed, versioned) | High (AWS native) | Medium (you manage infrastructure) |
| **Setup effort** | Low-Medium | Medium-High | Medium |

### Decision Guide — Agent Approaches

- **"Need an agent with minimal code, managed by AWS"** → Bedrock Agents
- **"Need deterministic workflow with branches and error handling"** → Step Functions orchestrating Bedrock
- **"Need complex multi-agent system with custom routing"** → LangGraph or custom orchestration
- **"Need agents that work across multiple LLM providers"** → LangChain/LangGraph
- **"Need full audit trail of every step"** → Step Functions (visual workflow + execution history)
- **"Agent needs to call external APIs and query knowledge base"** → Bedrock Agents with action groups + attached KB
- **Exam default answer** → Bedrock Agents (unless specific requirements point elsewhere)

---

## 6. Evaluation Options

| Feature | Bedrock Model Evaluation | Custom Metrics (CloudWatch + Lambda) | Human Evaluation |
|---------|-------------------------|--------------------------------------|-----------------|
| **Setup** | Console or API | You build pipeline | You recruit evaluators |
| **Metrics** | ROUGE, BERTScore, accuracy, toxicity | Any custom metric | Subjective quality, preference |
| **Scale** | Batch evaluation of datasets | Real-time per-request | Limited by evaluator count |
| **Cost** | Per-evaluation token cost | Lambda + CloudWatch cost | Per-evaluation labor cost |
| **Speed** | Minutes to hours | Real-time | Days to weeks |
| **Best for** | Model comparison, baseline quality | Production monitoring, SLA tracking | Nuanced quality, user preference |
| **Objectivity** | High (automated) | High (metric-based) | Low (subjective, but valuable) |

### Evaluation Metrics by Use Case

| Use Case | Key Metrics | Tool |
|----------|-------------|------|
| **Summarization** | ROUGE-L, BERTScore, faithfulness | Bedrock Evaluation |
| **Q&A** | Accuracy, F1 score, exact match | Bedrock Evaluation |
| **Classification** | Accuracy, precision, recall, F1 | Custom metrics |
| **RAG quality** | Context relevance, faithfulness, answer relevance | Custom pipeline (RAGAS-style) |
| **Content safety** | Toxicity, bias, PII leakage | Bedrock Evaluation + Guardrails |
| **Chatbot quality** | User satisfaction, task completion, coherence | Human evaluation |
| **Latency/cost** | P50/P99 latency, tokens per request, cost per query | CloudWatch metrics |

### Decision Guide — Evaluation

- **"Which model is better for my task?"** → Bedrock Model Evaluation (automatic)
- **"Is the chatbot response good enough?"** → Human evaluation (subjective quality)
- **"Are production latency SLAs being met?"** → CloudWatch metrics + alarms
- **"Is the RAG pipeline returning relevant context?"** → Custom evaluation (faithfulness, relevance)
- **"Is the model generating toxic content?"** → Bedrock Evaluation (toxicity metric) + Guardrails
- **"Need continuous production monitoring"** → CloudWatch custom metrics via Lambda

---

## 7. Decision Trees

### "I need to add AI to my application..."

```
START: Do you need to train a custom model from scratch?
├── YES → SageMaker (full training control)
└── NO → Do you need a foundation model API?
    ├── YES → Is your model available on Bedrock?
    │   ├── YES → Amazon Bedrock
    │   │   ├── Simple Q&A → Converse API
    │   │   ├── Q&A over documents → Knowledge Bases
    │   │   ├── Multi-step actions → Bedrock Agents
    │   │   └── Workflow orchestration → Step Functions + Bedrock
    │   └── NO → SageMaker JumpStart (deploy open-source model)
    └── NO → What do you need?
        ├── Embeddings only → Bedrock (Titan Embeddings V2)
        └── Image generation → Bedrock (Stability AI / Titan Image)
```

### "I need to ground my AI in company data..."

```
START: How much control do you need over the RAG pipeline?
├── MINIMAL (fastest setup) → Knowledge Bases + RetrieveAndGenerate
├── MODERATE (custom prompts) → Knowledge Bases + Retrieve API + custom generation
└── FULL (custom everything) → Custom RAG pipeline
    ├── Vector store → OpenSearch Serverless (default) or Aurora pgvector
    ├── Embedding → Titan Embeddings V2 or Cohere Embed
    ├── Chunking → Custom Lambda logic
    └── Generation → Converse API with custom prompt
```

### "I need to secure my GenAI application..."

```
START: What security requirement?
├── Block harmful content → Guardrails (content filters)
├── Block specific topics → Guardrails (topic policies)
├── Protect PII → Guardrails (sensitive info policy — BLOCK or ANONYMIZE)
├── Prevent prompt injection → Guardrails (PROMPT_ATTACK filter)
├── Private network connectivity → VPC endpoints (PrivateLink)
├── Restrict model access → IAM policies with bedrock:ModelId condition
├── Encrypt data at rest → KMS customer managed keys
├── Audit model usage → CloudTrail + model invocation logging
├── Org-wide restrictions → Service Control Policies (SCPs)
└── Detect sensitive data in S3 → Amazon Macie
```

### "I need to optimize cost..."

```
START: What is your usage pattern?
├── Variable/unpredictable traffic → On-demand pricing
├── Steady, high-volume production → Provisioned throughput
├── Bulk offline processing → Batch inference (50% savings)
├── Repeated prompts/prefixes → Prompt caching
├── Simple tasks using expensive models → Route to smaller/cheaper models
├── Caching common responses → ElastiCache or application-level cache
└── All of the above → Implement a tiered strategy
    ├── Tier 1: Cache hit → return cached response ($0)
    ├── Tier 2: Simple query → small model on-demand (low cost)
    ├── Tier 3: Complex query → large model on-demand (higher cost)
    └── Tier 4: Bulk jobs → batch inference (50% savings)
```

### "I need to evaluate my GenAI system..."

```
START: What are you evaluating?
├── Model quality (which model is best?) → Bedrock Model Evaluation
│   ├── Objective metrics (ROUGE, accuracy) → Automatic evaluation
│   └── Subjective quality (is it good?) → Human evaluation
├── RAG quality (are answers grounded?) → Custom pipeline
│   ├── Context relevance → Are retrieved chunks relevant?
│   ├── Faithfulness → Does the answer match the context?
│   └── Answer relevance → Does the answer address the question?
├── Production performance → CloudWatch metrics
│   ├── Latency (P50, P99) → CloudWatch + alarms
│   ├── Throughput → InvocationCount metric
│   └── Errors → ThrottlingCount, error rates
└── Content safety → Guardrails + Bedrock Evaluation (toxicity)
```

---

## 8. Common Exam Patterns

**1. Q: A company wants to build a customer service chatbot that answers questions from their product documentation. They want the simplest AWS-native solution with automatic citations. What should they use?**

A: **Amazon Bedrock Knowledge Bases** with S3 as the data source (storing product docs), **OpenSearch Serverless** as the vector store (default), and the **RetrieveAndGenerate** API for automatic retrieval, generation, and citation. This is the fully managed RAG solution with minimal code.

---

**2. Q: A data science team needs to fine-tune an open-source model not available on Bedrock, then serve it with auto-scaling. After fine-tuning, they also want to make it available through a unified API alongside Bedrock models. What approach should they take?**

A: Fine-tune the model using **SageMaker JumpStart** (or SageMaker training jobs), then use **Bedrock Custom Model Import** to make the fine-tuned model available through Bedrock's Converse API. This gives them SageMaker's training flexibility plus Bedrock's managed inference and unified API.

---

**3. Q: An organization processes 100,000 insurance claims per night and needs to generate summaries for each. Cost is the primary concern, and latency is not critical. What Bedrock feature should they use?**

A: **Batch inference** via `CreateModelInvocationJob`. Submit all claims as a JSONL file in S3. Bedrock processes them asynchronously and writes results to S3. Batch inference offers approximately 50% cost savings compared to on-demand pricing, and the async nature is acceptable since latency is not critical.

---

**4. Q: A company is choosing between OpenSearch Serverless and Aurora pgvector for their Bedrock Knowledge Base. They need hybrid search (keyword + semantic), fully serverless operations, and are willing to pay a premium for minimal management. Which should they choose?**

A: **OpenSearch Serverless**. It is fully serverless (no instance management), has native hybrid search combining BM25 keyword scoring with kNN vector search, and is the default vector store for Bedrock Knowledge Bases. Aurora pgvector requires instance management and has limited hybrid search capability. The higher cost of OpenSearch Serverless is acceptable given the requirement for minimal management.

---

**5. Q: A fintech startup needs their GenAI application to: (a) never discuss competitor products, (b) mask customer account numbers in responses, (c) block prompt injection attempts, and (d) maintain an audit trail of all interactions. Which AWS services and features address each requirement?**

A: (a) **Guardrails topic policy** with DENY for competitor product topics. (b) **Guardrails sensitive information policy** with regex pattern matching for account numbers, action set to ANONYMIZE. (c) **Guardrails content filter** with PROMPT_ATTACK type set to HIGH input strength. (d) **Model invocation logging** enabled to write full input/output to S3 and CloudWatch Logs, plus **CloudTrail** for API-level auditing. All four Guardrail policies can be combined in a single guardrail and applied via `guardrailConfig` in the Converse API.

---

## Quick Reference: Service Selection Matrix

| Requirement | Primary Service | Alternative |
|-------------|----------------|-------------|
| Foundation model API | Bedrock (Converse) | SageMaker JumpStart |
| Managed RAG | Bedrock Knowledge Bases | Custom pipeline |
| AI agent with tool use | Bedrock Agents | Step Functions + Lambda |
| Vector search | OpenSearch Serverless | Aurora pgvector |
| Text embeddings | Titan Embeddings V2 | Cohere Embed |
| Content safety | Bedrock Guardrails | Custom filters |
| Model evaluation | Bedrock Model Evaluation | Custom metrics |
| Fine-tuning | Bedrock / SageMaker | External + Custom Import |
| Workflow orchestration | Step Functions | Bedrock Agents |
| Cost optimization | Batch inference / Provisioned | Prompt caching / Model routing |
| Audit and compliance | CloudTrail + Invocation logging | AWS Config |
| Network security | VPC endpoints (PrivateLink) | — |
| Data encryption | KMS CMK | — |
| Access control | IAM (resource-level policies) | SCPs (org-wide) |
