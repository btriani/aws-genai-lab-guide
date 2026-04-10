# Prerequisites

Everything you need to set up before starting the labs. Choose **Option A** (SageMaker Studio) or **Option B** (Local Jupyter) depending on your preference — both are fully supported.

---

## 1. AWS Account

You need an AWS account with pay-as-you-go billing enabled. The full lab series costs approximately **$25 - $38** depending on how long resources are left running. See [COST-GUIDE.md](COST-GUIDE.md) for a detailed breakdown by lab.

> **Recommendation:** Create a dedicated **IAM user** with programmatic access instead of using your root account credentials. This follows AWS security best practices and limits the blast radius if credentials are ever exposed.

**Quick steps to create an IAM user:**

1. Sign in to the [AWS Console](https://console.aws.amazon.com/) as root.
2. Navigate to **IAM** > **Users** > **Create user**.
3. Attach the `AdministratorAccess` policy (for lab convenience).
4. Under **Security credentials**, create an **Access key** (CLI use case).
5. Save the Access Key ID and Secret Access Key — you will need them for `aws configure`.

---

## 2. Enable Bedrock Model Access

Several labs rely on foundation models through Amazon Bedrock. You must explicitly request access before you can invoke them.

**Steps:**

1. Open the [AWS Console](https://console.aws.amazon.com/) and switch to the **us-east-1** (N. Virginia) region.
2. Navigate to **Amazon Bedrock** > **Model access** (left sidebar, under Bedrock configurations).
3. Click **Modify model access**.
4. Select the following models and submit your request:

| Provider   | Model                          |
|------------|--------------------------------|
| Anthropic  | Claude 3.5 Sonnet              |
| Anthropic  | Claude 3.5 Haiku               |
| Amazon     | Titan Text Express             |
| Amazon     | Titan Embeddings V2            |
| Meta       | Llama 3 8B Instruct            |
| Mistral    | Mistral 7B Instruct            |

5. Click **Request model access**.

> **Note:** Model access approvals typically complete within a few minutes. You can check the status on the same Model access page — each model will show **Access granted** when ready.

---

## 3. AWS CLI

Install the AWS CLI v2 so you can authenticate from the terminal.

**macOS:**

```bash
brew install awscli
```

**Linux:**

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
  && unzip awscliv2.zip \
  && sudo ./aws/install
```

**Windows:**

Download and run the MSI installer from [https://aws.amazon.com/cli/](https://aws.amazon.com/cli/).

**Configure credentials:**

```bash
aws configure
```

When prompted, enter:

| Prompt              | Value                              |
|---------------------|------------------------------------|
| AWS Access Key ID   | *(your IAM user access key)*       |
| AWS Secret Access Key | *(your IAM user secret key)*     |
| Default region name | `us-east-1`                        |
| Default output format | `json`                           |

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your account ID, user ARN, and user ID in the output.

---

## 4. Python 3.10+

Check your current version:

```bash
python3 --version
```

If you need to install or upgrade:

- **macOS:** `brew install python@3.12`
- **Linux (Ubuntu/Debian):** `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.12`
- **pyenv (any platform):** `pyenv install 3.12 && pyenv global 3.12`

---

## 5. Git

Check if Git is already installed:

```bash
git --version
```

If not:

- **macOS:** `brew install git`
- **Linux (Ubuntu/Debian):** `sudo apt install git`
- **Windows:** Download from [https://git-scm.com/](https://git-scm.com/)

Clone the lab repository:

```bash
git clone https://github.com/btriani/aws-genai-lab-guide.git
cd aws-genai-lab-guide
```

---

## 6. Choose Your Environment

Pick **one** of the two options below. You can always switch later.

### Option A: SageMaker Studio

Best if you want a fully managed cloud notebook experience with no local setup.

**Setup steps:**

1. Open the [AWS Console](https://console.aws.amazon.com/) and navigate to **Amazon SageMaker** > **Domains**.
2. Click **Create domain** and follow the quick setup wizard (the defaults are fine for lab purposes).
3. Once the domain is active, click **Open Studio**.
4. In Studio, open a **System terminal** and clone the repo:
   ```bash
   git clone https://github.com/btriani/aws-genai-lab-guide.git
   ```
5. Open the notebooks from the file browser and start working.

| Pros | Cons |
|------|------|
| No local Python or credential setup | Requires a SageMaker domain (included in free tier for some instance types) |
| IAM roles handle authentication automatically | Studio UI takes a minute to launch |
| Pre-installed data science libraries | |

> **Tip:** You can also create the SageMaker domain automatically by running `python scripts/setup-resources.py --sagemaker`.

---

### Option B: Local Jupyter

Best if you prefer working on your own machine and want to avoid SageMaker domain costs.

**Install the required Python packages:**

```bash
pip install boto3 sagemaker opensearch-py jupyter requests-aws4auth
```

**Make sure your AWS credentials are configured:**

```bash
aws configure
```

**Launch Jupyter Lab:**

```bash
jupyter lab
```

Navigate to the `labs/` directory in the Jupyter file browser and open any notebook to begin.

| Pros | Cons |
|------|------|
| Free compute (runs on your machine) | Requires local Python 3.10+ installation |
| Full control over your environment | Must configure AWS credentials manually |
| Works offline for non-AWS cells | |

---

## 7. Verification

Run the prerequisites check script to confirm everything is set up correctly:

```bash
bash scripts/check-prerequisites.sh
```

You should see output like:

```
AWS GenAI Lab Guide — Prerequisites Check
===========================================

Core tools:
  AWS CLI                   [PASS]
  Python >= 3.10            [PASS] 3.12
  pip                       [PASS]
  Git                       [PASS]

Python packages:
  boto3                     [PASS]
  sagemaker                 [PASS]
  opensearchpy              [PASS]

AWS access:
  AWS credentials           [PASS] account 123456789012
  Bedrock access            [PASS]

===========================================
Results: 9 passed, 0 failed
```

If any check shows `[FAIL]`, follow the instructions in the relevant section above to fix it.

---

You are now ready to start [the labs](labs/).
