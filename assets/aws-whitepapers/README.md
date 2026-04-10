# AWS Whitepapers — Sample Data

This directory stores AWS whitepapers (PDF format) used as sample data throughout the lab exercises. The PDFs themselves are **not committed to this repository** — they are downloaded on demand by `scripts/setup-resources.py` and listed in `.gitignore`.

## How documents are used

- **RAG labs** — chunked, embedded, and stored in vector databases (OpenSearch Serverless, Knowledge Bases for Amazon Bedrock) for retrieval-augmented generation
- **Embeddings labs** — converted to vector embeddings using Amazon Titan Embeddings or Cohere Embed models via Bedrock
- **Fine-tuning data** — sections are extracted and reformatted as training pairs (see also `labs/data/finetune-qa.jsonl`)

## Document inventory

| Document | Source | License | Why Selected |
|----------|--------|---------|-------------|
| AWS Well-Architected Framework | [docs.aws.amazon.com/wellarchitected](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) | AWS documentation terms | Foundational AWS knowledge referenced across all exam domains; covers design principles and best practices |
| Generative AI on AWS | [aws.amazon.com/ai/generative-ai](https://aws.amazon.com/ai/generative-ai/) | AWS documentation terms | Directly covers DEA-C01 exam topics including foundation models, Bedrock, and GenAI application patterns |
| Amazon Bedrock User Guide | [docs.aws.amazon.com/bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) | AWS documentation terms | Core service for the exam — covers API patterns (InvokeModel, Converse), Knowledge Bases, Agents, Guardrails, and fine-tuning |
| AWS Shared Responsibility Model | [aws.amazon.com/compliance/shared-responsibility-model](https://aws.amazon.com/compliance/shared-responsibility-model/) | AWS documentation terms | Domain 4 (security and compliance) material — critical for understanding security boundaries in GenAI workloads |

## Downloading the documents

Run the setup script from the repository root:

```bash
python scripts/setup-resources.py
```

The script downloads each PDF into this directory. If a file already exists locally, it is skipped.

## Why PDFs are gitignored

- AWS documentation is freely available but redistribution terms vary
- PDF files are large binary blobs that bloat Git history
- Downloading on demand ensures you always have the latest version
