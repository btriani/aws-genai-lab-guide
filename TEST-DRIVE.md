# Test Drive Guide

Try everything you built in 15 minutes. Open each link, type the test prompt, and see what happens.

> **Region:** Make sure you're in **us-east-1 (N. Virginia)** — top-right corner of the console.

---

## 1. Chat with a Model (2 min)

**What it is:** Direct conversation with a foundation model — no RAG, no tools, just the model.

**Go to:** Bedrock → Playgrounds → [Playground](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/playgrounds/chat) → Select model → **Amazon Nova Lite**

**Try these:**

| Prompt | What You'll See |
|--------|----------------|
| `What is Amazon Bedrock?` | Factual answer from the model's training data |
| `Write a haiku about cloud computing` | Creative output — try changing temperature to 1.0 |
| `Explain RAG in one sentence` | Tests the model's knowledge of GenAI concepts |

**What to notice:**
- Change **temperature** (right panel): 0 = same answer every time, 1 = creative/varied
- Change **model**: switch to Claude Sonnet 4.5 — notice how answers are more detailed but slower
- Check **token count** at the bottom — this is what you pay for

---

## 2. Ask Your Knowledge Base (3 min)

**What it is:** RAG — the model answers using your AWS whitepapers as source material, not just its training data. It retrieves relevant chunks from your documents and generates a grounded answer with citations.

**Go to:** Bedrock → [Knowledge bases](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/knowledge-bases) → **genai-lab-kb** → **Test** (top right)

**Select a model** (e.g., Claude Sonnet 4.5), then try:

| Prompt | What You'll See |
|--------|----------------|
| `What are the six pillars of the Well-Architected Framework?` | Answer pulled from the actual whitepaper PDF, with source citations |
| `How does the shared responsibility model apply to AI?` | Answer grounded in the security whitepaper |
| `What embedding models does Bedrock support?` | Answer from the Bedrock User Guide |
| `What is the capital of France?` | Poor/generic answer — the whitepapers don't contain this, showing RAG's scope limitation |

**What to notice:**
- Expand **Source citations** — you'll see the exact PDF chunks the model used
- The last prompt shows RAG's limitation: if the answer isn't in your documents, the model either hallucinates or gives a generic answer
- This is the same `RetrieveAndGenerate` API that Lab 05 calls programmatically

---

## 3. Test Your Guardrails (3 min)

**What it is:** Content filtering that blocks harmful, sensitive, or off-topic responses. Guardrails sit between the user and the model, filtering both input and output.

**Go to:** Bedrock → [Guardrails](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/guardrails) → **genai-lab-guardrail** → **Test** (top right)

**Select a model**, then try:

| Prompt | Expected Result | Why |
|--------|----------------|-----|
| `What is Amazon S3?` | Normal answer | Safe prompt, no filters triggered |
| `Should I invest in Amazon stock?` | **BLOCKED** | Denied topic: investment advice |
| `What medication should I take for headaches?` | **BLOCKED** | Denied topic: medical advice |
| `My email is john@example.com and my phone is 555-1234` | Answer with **email/phone redacted** | PII anonymization (EMAIL, PHONE) |
| `My SSN is 123-45-6789` | **BLOCKED entirely** | PII blocking (US_SOCIAL_SECURITY_NUMBER) |

**What to notice:**
- **BLOCKED** shows the blocked message you configured, not the model's response
- **PII anonymization** replaces the sensitive data with `{EMAIL}` or `{PHONE}` — the model never sees the real values
- **PII blocking** (SSN) stops the entire request — stricter than anonymization
- Check the **Trace** to see which filter triggered and why

---

## 4. Talk to Your Agent (3 min)

**What it is:** An AI agent that can use tools (Lambda functions) to look up information and reason about it. Uses the ReAct pattern: Think → Act → Observe → Think → Answer.

**Go to:** Bedrock → [Agents](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents) → **genai-lab-agent** → **Test** (top right)

**Try these:**

| Prompt | What You'll See |
|--------|----------------|
| `What is Amazon Bedrock?` | Agent calls the lookup tool, returns structured info |
| `Compare S3 and Lambda` | Agent calls the compare tool, explains differences |
| `What category does SageMaker belong to?` | Agent reasons: "I need to look up SageMaker" → calls tool → "AI/ML" |
| `Which is better for storing files, S3 or DynamoDB?` | Agent may call lookup on both, then reason about the answer |

**What to notice:**
- Enable **Show trace** — this reveals the ReAct reasoning steps:
  1. **Thought:** "I need to look up this service"
  2. **Action:** Calls the Lambda function via the action group
  3. **Observation:** Receives the tool response
  4. **Thought:** "Now I can answer the question"
  5. **Final answer**
- The agent isn't just retrieving data — it's *deciding which tool to use* and *reasoning about the results*
- Try a question that needs both tools: `"Compare Bedrock and SageMaker for hosting models"`

---

## 5. See Your Resources (2 min)

**Go to:** [Resource Groups → genai-lab-guide](https://us-east-1.console.aws.amazon.com/resource-groups/group/genai-lab-guide?region=us-east-1)

You'll see all lab resources in one list:

| Resource | What It Does |
|----------|-------------|
| **S3 Bucket** | Stores whitepapers (PDFs) and training data |
| **OpenSearch Vectors** | Vector database holding document embeddings for RAG |
| **Knowledge Base** | Manages the RAG pipeline: ingestion, retrieval, generation |
| **Bedrock Agent** | AI agent with Lambda tools for looking up services |
| **Guardrail** | Content filter protecting against PII, harmful content, off-topic requests |
| **Lambda Function** | The tool the agent calls to look up AWS service info |

---

## 6. Check Your Costs (2 min)

**Go to:** [Billing → Budgets](https://us-east-1.console.aws.amazon.com/billing/home#/budgets)

You should see **genai-lab-guide** budget ($40/month). Click it to see current spend.

**Go to:** [CloudTrail → Event history](https://us-east-1.console.aws.amazon.com/cloudtrailv2/home?region=us-east-1#/events?EventSource=bedrock.amazonaws.com)

You'll see every Bedrock API call you (and the labs) made — InvokeModel, Converse, CreateAgent, etc. This is the audit trail the exam tests you on.

---

## What Could Go Wrong (Abuse Scenarios)

These are the scenarios the exam tests — and now you can see them in action:

| Scenario | What Happens | Which Lab Covers It |
|----------|-------------|-------------------|
| User sends PII to the model | Guardrails anonymize or block it before the model sees it | Lab 10 |
| User asks for investment advice | Guardrails block the request with a policy message | Lab 10 |
| Model hallucinates an answer | RAG grounds the response in source documents with citations | Lab 05 |
| Someone calls Bedrock without permission | IAM policy denies the request; CloudTrail logs the attempt | Lab 11 |
| Costs spiral out of control | Budget alert triggers at $40; Cost Explorer shows per-service breakdown | Lab 11 |
| Model gives inconsistent answers | Set temperature=0 for deterministic output; evaluate with ROUGE/BERTScore | Labs 03, 08 |
| Agent calls the wrong tool | ReAct trace shows the reasoning — improve the tool descriptions in OpenAPI schema | Lab 06 |
| OpenSearch left running overnight | ~$12/day; cleanup script deletes it; Cost Explorer shows the spike | TROUBLESHOOTING.md |

---

## When You're Done

Your OpenSearch collection charges **~$0.50/hr** while active. To stop all billing:

```bash
python scripts/cleanup-all.py
```

This deletes: OpenSearch collection, Knowledge Base, Agent, Lambda, IAM roles, S3 bucket.

Or keep resources running if you want to keep exploring — just watch your budget in the [Billing console](https://us-east-1.console.aws.amazon.com/billing/home).
