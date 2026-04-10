# Exam Domains Cheatsheet — AWS Generative AI Specialty (DEP-C01)

> Comprehensive domain-by-domain breakdown with key concepts, decision points, and study priorities for the AWS Certified AI Practitioner (AIF-C01) and the **AWS Generative AI Specialty (DEP-C01)** exam.

---

## 1. Domain Overview

| Domain | Name | Weight | Labs | Key Services |
|--------|------|--------|------|-------------|
| **D1** | Selecting and Customizing Foundation Models | 26% | Lab 01, Lab 02, Lab 03 | Bedrock (InvokeModel, Converse), SageMaker JumpStart, Bedrock Model Evaluation, Fine-Tuning, Prompt Management |
| **D2** | Building Generative AI Applications | 30% | Lab 04, Lab 05, Lab 06, Lab 07 | Bedrock Knowledge Bases, Bedrock Agents, OpenSearch Serverless, Step Functions, Lambda, S3, EventBridge |
| **D3** | Optimizing Generative AI Performance | 24% | Lab 08, Lab 09 | Bedrock Evaluation, Provisioned Throughput, Batch Inference, Model Invocation Logging, CloudWatch, Prompt Caching |
| **D4** | Security, Compliance, and Governance | 20% | Lab 10, Lab 11 | Bedrock Guardrails, IAM, KMS, VPC Endpoints, CloudTrail, AWS Config, Macie, Service Control Policies |

> **Exam format:** 85 questions, 170 minutes, pass score ~750/1000. Mix of multiple choice and multiple response.

---

## 2. Domain 1 — Selecting and Customizing Foundation Models (26%)

### Key Concepts

**Model Selection Criteria**
- **Task type** — text generation, summarization, classification, code generation, multimodal (image+text)
- **Accuracy requirements** — larger models (Claude Sonnet 4.5, Llama 3.1 70B) for complex reasoning; smaller models (Llama 3 8B, Haiku) for simple tasks
- **Latency requirements** — smaller models respond faster; streaming reduces perceived latency
- **Cost** — input/output token pricing varies significantly across models and sizes
- **Language and region** — not all models available in all regions; some models better for specific languages
- **Context window** — Claude supports up to 200K tokens; critical for long-document processing

**InvokeModel vs Converse**
- `InvokeModel` — model-specific request/response JSON; use for legacy code or provider-specific features
- `Converse` — unified API across all models; preferred for new development
- `ConverseStream` — streaming variant; required for real-time response display
- Converse supports built-in tool use, system prompts, and guardrails integration

**Customization Spectrum (least to most effort)**

| Approach | When to Use | Data Required | Cost | Time |
|----------|-------------|---------------|------|------|
| **Prompt engineering** | Adjust behavior without training | None (examples in prompt) | Lowest | Minutes |
| **RAG** | Ground answers in proprietary data | Documents (unstructured) | Low-Medium | Hours |
| **Continued pre-training** | Teach new domain vocabulary | Large unlabeled corpus | High | Days |
| **Fine-tuning** | Change model style or behavior | Labeled examples (JSONL) | High | Hours-Days |
| **Full training** | Completely custom model | Massive dataset | Highest | Weeks |

**Fine-Tuning on Bedrock**
- Supported models: Titan Text, Cohere, Meta Llama (check current availability)
- Training data format: JSONL with `prompt` and `completion` fields
- Data stored in S3; IAM role with S3 and Bedrock permissions required
- Hyperparameters: epochs, batch size, learning rate, warmup steps
- Output: custom model version accessible via custom model ARN
- **Custom model import** — bring SageMaker or externally trained models into Bedrock

**Prompt Engineering Techniques**

| Technique | Description | When to Use |
|-----------|-------------|-------------|
| Zero-shot | No examples | Simple, well-defined tasks |
| Few-shot | Include examples in prompt | Format compliance, style matching |
| Chain-of-thought | "Think step by step" | Complex reasoning, math |
| ReAct | Reason + Act pattern | Agent-like tool use |
| Self-consistency | Multiple reasoning paths | High-accuracy requirements |

### Decision Points

- **"Need to use proprietary data without training"** → RAG (Knowledge Bases)
- **"Need to change model personality or output style"** → Fine-tuning
- **"Need domain-specific vocabulary (legal, medical)"** → Continued pre-training, then fine-tuning
- **"Need unified API across multiple providers"** → Converse API
- **"Need to evaluate which model is best for a task"** → Bedrock Model Evaluation (automatic or human)
- **"Need real-time response streaming"** → ConverseStream
- **"Need to run a model not available in Bedrock"** → SageMaker JumpStart or Custom Model Import

---

## 3. Domain 2 — Building Generative AI Applications (30%)

### Key Concepts

**RAG Pipeline Architecture**

1. **Ingestion** — documents (PDF, HTML, TXT, DOCX, CSV) loaded from S3
2. **Chunking** — split documents into smaller pieces (fixed-size, semantic, hierarchical)
3. **Embedding** — convert chunks to vectors (Titan Embeddings V2, Cohere Embed)
4. **Storage** — store vectors in a vector store (OpenSearch Serverless, Aurora pgvector, Pinecone, Redis)
5. **Retrieval** — query vector store with embedded user question (semantic, hybrid, or metadata filtering)
6. **Generation** — pass retrieved chunks + user question to foundation model

**Bedrock Knowledge Bases**
- Managed RAG service: handles ingestion, chunking, embedding, and storage
- Supported sources: S3 (primary), Confluence, SharePoint, Salesforce, web crawlers
- Chunking strategies: fixed-size (default 300 tokens), semantic, hierarchical, no chunking
- Vector stores: OpenSearch Serverless (default), Aurora pgvector, Pinecone, Redis Enterprise Cloud, MongoDB Atlas
- Retrieval types: SEMANTIC (vector similarity), HYBRID (vector + keyword)
- APIs: `Retrieve` (chunks only) and `RetrieveAndGenerate` (chunks + LLM response)
- Metadata filtering: filter retrieval results by document attributes

**Bedrock Agents**
- Autonomous AI assistants that can reason, plan, and take action
- Components: foundation model, instructions, action groups, knowledge bases
- **Action groups** — Lambda functions with OpenAPI schema defining available actions
- **Knowledge base integration** — agent can query KBs during reasoning
- **Code interpreter** — agent can write and execute Python code
- **Session management** — multi-turn conversations with `sessionId`
- **Agent versioning** — create aliases for production deployment
- Reasoning: ReAct pattern (Reason → Act → Observe → Repeat)

**Orchestration Patterns**

| Pattern | Service | Use Case |
|---------|---------|----------|
| Single model call | Bedrock Converse | Simple Q&A, summarization |
| RAG | Knowledge Bases | Grounded Q&A over documents |
| Agent (autonomous) | Bedrock Agents | Multi-step tasks with tool use |
| Sequential workflow | Step Functions + Lambda + Bedrock | Deterministic multi-step pipelines |
| Event-driven | EventBridge + Lambda + Bedrock | Async processing triggers |
| Map-reduce | Step Functions Distributed Map | Parallel document processing |
| Human-in-the-loop | Step Functions + callback | Approval workflows |

**Step Functions Integration**
- Native Bedrock integration via `bedrock:InvokeModel` task type
- Orchestrate multi-step GenAI workflows with branching logic
- Error handling with `Retry` and `Catch` blocks
- Wait states for human approval
- Map state for parallel processing of multiple documents

**Prompt Engineering for Applications**
- System prompts define persona, constraints, and output format
- Few-shot examples improve format compliance
- Prompt templates with variable substitution for dynamic content
- Bedrock Prompt Management for versioning and A/B testing prompts

### Decision Points

- **"Need Q&A over company documents with minimal code"** → Bedrock Knowledge Bases with RetrieveAndGenerate
- **"Need full control over RAG pipeline"** → Custom RAG with Retrieve API + custom prompting
- **"Need an AI assistant that can take actions (API calls, DB queries)"** → Bedrock Agents with action groups
- **"Need deterministic multi-step workflow"** → Step Functions orchestrating Bedrock calls
- **"Need to process thousands of documents in parallel"** → Step Functions Distributed Map + Bedrock
- **"Need to combine retrieval + actions in one assistant"** → Bedrock Agent with attached knowledge base
- **"Need event-driven GenAI processing"** → EventBridge → Lambda → Bedrock
- **"Which chunking strategy?"** → Fixed-size for uniform docs; semantic for mixed-format; hierarchical for documents with natural structure (chapters, sections)

---

## 4. Domain 3 — Optimizing Generative AI Performance (24%)

### Key Concepts

**Evaluation Methods**

| Method | Service/Approach | Metrics | Best For |
|--------|-----------------|---------|----------|
| **Automatic (Bedrock)** | Bedrock Model Evaluation | ROUGE, BERTScore, accuracy, toxicity | Batch comparison of models |
| **Human evaluation (Bedrock)** | Bedrock Model Evaluation + human workforce | Thumbs up/down, ranking, Likert scale | Subjective quality, preference |
| **LLM-as-judge** | Claude evaluating another model's outputs | Custom rubrics, scoring | Scalable quality assessment |
| **Custom metrics** | CloudWatch + Lambda | Latency, token usage, cost, custom scores | Production monitoring |
| **RAG evaluation** | Custom pipeline | Context relevance, faithfulness, answer relevance | RAG pipeline quality |

**Key Evaluation Metrics**

| Metric | Measures | Range | Higher Is Better |
|--------|----------|-------|-----------------|
| ROUGE-L | Longest common subsequence overlap | 0-1 | Yes |
| BERTScore | Semantic similarity via embeddings | 0-1 | Yes |
| Perplexity | How well model predicts text | > 0 | No (lower is better) |
| F1 Score | Precision/recall balance | 0-1 | Yes |
| Toxicity | Harmful content detection | 0-1 | No (lower is better) |
| Faithfulness | RAG answer grounded in context | 0-1 | Yes |
| Latency (P50/P99) | Response time | ms | No (lower is better) |

**Throughput Modes**

| Mode | Pricing | Latency | Use Case | Commitment |
|------|---------|---------|----------|------------|
| **On-demand** | Per-token (input + output) | Variable, best-effort | Development, variable workloads | None |
| **Provisioned throughput** | Hourly rate per model unit | Guaranteed, consistent | Production with predictable traffic | 1-month or 6-month |
| **Batch inference** | 50% discount vs on-demand | Hours (async) | Bulk processing, offline jobs | None |

**Batch Inference**
- Submit JSONL file to S3 with multiple requests
- Bedrock processes asynchronously, writes results to S3
- 50% cost savings compared to on-demand
- Use for: bulk classification, document summarization, dataset augmentation
- API: `CreateModelInvocationJob`

**Prompt Caching**
- Cache frequently used prompt prefixes (system prompts, few-shot examples)
- Reduces input token costs for repeated prefixes
- Supported on select models (check current availability)
- Cache TTL configurable; cache hit reduces latency and cost

**Token Optimization Strategies**

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| Shorter prompts | Remove unnecessary context, use concise instructions | Reduce input cost |
| Prompt caching | Cache static prompt prefixes | Reduce repeat input cost |
| Smaller models | Use Haiku/Titan Lite for simple tasks | Lower per-token cost |
| Output length limits | Set appropriate `maxTokens` | Reduce output cost |
| Batch inference | Process bulk requests offline | 50% cost reduction |
| Response caching | Cache common query responses (ElastiCache) | Eliminate redundant calls |
| Model routing | Route simple queries to cheaper models | Lower average cost |

**Monitoring and Observability**
- **Model invocation logging** — log all Bedrock API calls to S3 and/or CloudWatch Logs
- **CloudWatch metrics** — InvocationCount, Latency, ThrottlingCount, InputTokenCount, OutputTokenCount
- **CloudWatch alarms** — alert on latency spikes, throttling, error rates
- **X-Ray tracing** — end-to-end trace for multi-service GenAI workflows

### Decision Points

- **"Need to compare three models on the same task"** → Bedrock Model Evaluation (automatic)
- **"Need guaranteed low latency in production"** → Provisioned throughput
- **"Need to process 10,000 documents cheaply"** → Batch inference
- **"Need to reduce cost of repeated system prompts"** → Prompt caching
- **"Need to monitor model performance in production"** → Model invocation logging + CloudWatch metrics + alarms
- **"Need to evaluate RAG quality"** → Custom evaluation pipeline measuring faithfulness, relevance, and recall
- **"Need subjective quality assessment"** → Human evaluation via Bedrock Model Evaluation
- **"Need end-to-end latency visibility"** → X-Ray tracing across Lambda, Step Functions, Bedrock

---

## 5. Domain 4 — Security, Compliance, and Governance (20%)

### Key Concepts

**Bedrock Guardrails**
- Content filtering: SEXUAL, VIOLENCE, HATE, INSULTS, MISCONDUCT, PROMPT_ATTACK
- Topic denial: block specific subjects (e.g., competitor products, financial advice)
- Word filters: custom blocked words + managed profanity list
- PII detection: BLOCK or ANONYMIZE sensitive data (email, phone, SSN, etc.)
- Contextual grounding: detect hallucinations with grounding and relevance thresholds
- Applied via `guardrailConfig` in Converse API or standalone `ApplyGuardrail` API

**IAM for Bedrock**

| Permission | Purpose | Example |
|------------|---------|---------|
| `bedrock:InvokeModel` | Call foundation models | Allow specific models only |
| `bedrock:InvokeModelWithResponseStream` | Streaming model calls | Same as above, streaming variant |
| `bedrock:Converse` | Use Converse API | Preferred over InvokeModel permissions |
| `bedrock:Retrieve` | Query knowledge bases | Restrict to specific KB IDs |
| `bedrock:InvokeAgent` | Call agents | Restrict to specific agent IDs |
| `bedrock:ApplyGuardrail` | Apply guardrails standalone | Restrict to specific guardrail IDs |

**Least Privilege Best Practices**
- Use resource-level permissions: restrict by model ID, knowledge base ID, agent ID
- Condition keys: `bedrock:ModelId`, `aws:RequestedRegion`
- Deny access to unused models to prevent cost surprises
- Separate roles for development (broader access) and production (tightly scoped)
- Use IAM Identity Center for federated access; no long-lived access keys

**Networking and Data Protection**

| Control | Service | Purpose |
|---------|---------|---------|
| **VPC Endpoints** | PrivateLink | Keep Bedrock traffic off the public internet |
| **KMS encryption** | KMS CMK | Encrypt model artifacts, training data, knowledge base data at rest |
| **TLS 1.2+** | Default | Encrypt data in transit |
| **S3 bucket policies** | S3 | Restrict access to training/RAG data |
| **Macie** | Macie | Discover and protect sensitive data in S3 |
| **PrivateLink** | VPC | Private connectivity to Bedrock endpoints |

**VPC Endpoints for Bedrock**
- `bedrock-runtime` endpoint — for InvokeModel, Converse, ConverseStream
- `bedrock` endpoint — for control plane APIs (CreateGuardrail, etc.)
- `bedrock-agent-runtime` endpoint — for InvokeAgent, Retrieve, RetrieveAndGenerate
- Use endpoint policies to restrict which APIs and models are accessible

**Logging and Auditing**

| Service | What It Logs | Use Case |
|---------|-------------|----------|
| **CloudTrail** | All Bedrock API calls (control + data plane) | Audit trail, compliance |
| **Model invocation logging** | Full input/output of model calls | Content auditing, debugging |
| **CloudWatch Logs** | Invocation logs destination | Centralized log analysis |
| **S3** | Invocation logs destination | Long-term archival, analytics |
| **AWS Config** | Resource configuration changes | Configuration compliance |
| **GuardDuty** | Threat detection | Anomalous API usage detection |

**Model Invocation Logging**
- Enable via Bedrock console or `PutModelInvocationLoggingConfiguration` API
- Logs: full prompt, full response, model ID, token counts, latency
- Destinations: S3 bucket and/or CloudWatch Logs
- Important for: compliance auditing, content review, debugging, cost analysis
- **Caution:** Logs may contain sensitive data — encrypt with KMS and restrict access

**Compliance and Governance**
- AWS Config rules to enforce Bedrock configuration standards
- Service Control Policies (SCPs) to restrict Bedrock access at the organization level
- Tag-based access control for cost allocation and permission boundaries
- Data residency: choose regions carefully; Bedrock processes data in the selected region
- Model providers: understand data usage policies for each provider on Bedrock

### Decision Points

- **"Need to prevent PII in model responses"** → Guardrails with sensitive information policy (BLOCK or ANONYMIZE)
- **"Need to keep Bedrock traffic private"** → VPC endpoints (PrivateLink)
- **"Need to audit all model inputs/outputs"** → Model invocation logging to S3 + CloudWatch
- **"Need to restrict which models teams can use"** → IAM policies with `bedrock:ModelId` condition
- **"Need to prevent prompt injection attacks"** → Guardrails with PROMPT_ATTACK content filter
- **"Need organization-wide Bedrock restrictions"** → Service Control Policies (SCPs)
- **"Need to encrypt knowledge base data at rest"** → KMS customer managed key (CMK)
- **"Need to detect sensitive data in training documents"** → Amazon Macie on S3 buckets

---

## 6. Study Priority Guide

Ranked by **exam weight x typical difficulty**. Spend more time on higher-priority items.

| Priority | Topic | Domain | Weight | Why It Matters |
|----------|-------|--------|--------|---------------|
| 1 | RAG architecture and Knowledge Bases | D2 | 30% | Most-tested topic; understand full pipeline |
| 2 | Bedrock Agents and action groups | D2 | 30% | Complex; multi-step reasoning questions |
| 3 | Model selection criteria | D1 | 26% | Many scenario-based questions |
| 4 | Guardrails configuration | D4 | 20% | Applied security; policy types and actions |
| 5 | Evaluation methods and metrics | D3 | 24% | Know when to use automatic vs human eval |
| 6 | Converse API vs InvokeModel | D1 | 26% | Fundamental API distinction |
| 7 | Throughput modes (on-demand, provisioned, batch) | D3 | 24% | Cost optimization scenarios |
| 8 | IAM least privilege for Bedrock | D4 | 20% | Always tested on AWS exams |
| 9 | Prompt engineering techniques | D1 | 26% | Zero-shot, few-shot, chain-of-thought |
| 10 | Step Functions orchestration | D2 | 30% | Multi-step workflow questions |
| 11 | VPC endpoints and networking | D4 | 20% | Private connectivity questions |
| 12 | Fine-tuning vs RAG vs prompt engineering | D1 | 26% | "When to use which" scenarios |
| 13 | Embeddings and vector search | D2 | 30% | Foundation for RAG understanding |
| 14 | Model invocation logging | D4 | 20% | Auditing and compliance |
| 15 | Batch inference and cost optimization | D3 | 24% | Cost-focused scenarios |

### Study Time Allocation

| Domain | Suggested Study Time | Reasoning |
|--------|---------------------|-----------|
| D2 (Building GenAI Apps) | 30-35% | Highest weight + most complex topics |
| D1 (Foundation Models) | 25-30% | Second highest weight; broad knowledge needed |
| D3 (Optimizing Performance) | 20-25% | Moderate weight; some overlap with D1/D2 |
| D4 (Security & Governance) | 15-20% | Lowest weight; many concepts transfer from other AWS certs |

---

## 7. Common Exam Patterns

**1. Q: A company has thousands of PDF documents and wants employees to ask natural language questions. The solution should require minimal custom code. What AWS approach is best?**

A: **Amazon Bedrock Knowledge Bases** with S3 as the data source and **RetrieveAndGenerate** API. This is the fully managed RAG solution — Bedrock handles document ingestion, chunking, embedding, vector storage, retrieval, and generation.

---

**2. Q: A startup wants to minimize costs for a GenAI chatbot with unpredictable traffic. They need low latency during business hours but can tolerate delays at night for batch processing. What throughput strategy should they use?**

A: **On-demand throughput** for the real-time chatbot (no commitment, pay-per-token) and **batch inference** for nighttime processing (50% cost savings). Provisioned throughput is not recommended because traffic is unpredictable.

---

**3. Q: A financial services company needs an AI assistant that can check account balances, transfer funds, and answer policy questions from a compliance manual. Which Bedrock feature combines these capabilities?**

A: **Bedrock Agents** with (1) **action groups** backed by Lambda functions for account balance and transfer operations (defined via OpenAPI schema), and (2) an attached **knowledge base** containing the compliance manual for policy questions.

---

**4. Q: A healthcare organization must ensure their GenAI application never reveals patient names, never discusses treatment pricing, and maintains response quality. Which combination of Bedrock features addresses all three requirements?**

A: **Bedrock Guardrails** with three policies: (1) **Sensitive information policy** to ANONYMIZE or BLOCK patient name PII entities, (2) **Topic policy** with DENY for treatment pricing discussions, and (3) **Contextual grounding check** to ensure response quality and prevent hallucinations. Optionally, use **model invocation logging** for compliance auditing.

---

**5. Q: A team wants to evaluate whether Claude or Llama produces better summaries for their legal documents. They need both automated metrics and human judgment. What is the most efficient approach?**

A: Use **Bedrock Model Evaluation** with both automatic evaluation (measuring ROUGE, BERTScore for text quality) and human evaluation (using a human workforce to rate summary quality, relevance, and accuracy). This provides both objective metrics and subjective quality assessment in a single managed service.

---

## Quick Reference: Service-to-Domain Mapping

| Service | D1 | D2 | D3 | D4 |
|---------|----|----|----|----|
| Bedrock (InvokeModel/Converse) | X | X | | |
| Bedrock Knowledge Bases | | X | | |
| Bedrock Agents | | X | | |
| Bedrock Guardrails | | | | X |
| Bedrock Model Evaluation | X | | X | |
| Bedrock Fine-Tuning | X | | | |
| SageMaker JumpStart | X | | | |
| Step Functions | | X | | |
| OpenSearch Serverless | | X | | |
| CloudWatch / CloudTrail | | | X | X |
| IAM / KMS / VPC | | | | X |
| Provisioned Throughput | | | X | |
| Batch Inference | | | X | |
