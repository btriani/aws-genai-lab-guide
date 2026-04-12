import streamlit as st
import boto3
import json
import time

st.set_page_config(page_title="AWS GenAI Playground", layout="wide")
st.title("AWS GenAI Playground")

REGION = "us-east-1"
session = boto3.Session(region_name=REGION)
bedrock_runtime = session.client("bedrock-runtime")

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
MODELS = {
    "Claude Sonnet 4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Llama 3 8B": "meta.llama3-8b-instruct-v1:0",
    "Mistral 7B": "mistral.mistral-7b-instruct-v0:2",
}

# ---------------------------------------------------------------------------
# Helper: invoke converse (non-streaming, returns full response)
# ---------------------------------------------------------------------------
def call_converse(model_id, messages, system=None, max_tokens=512, temperature=0.7, guardrail_config=None):
    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        kwargs["system"] = [{"text": system}]
    if guardrail_config:
        kwargs["guardrailConfig"] = guardrail_config
    return bedrock_runtime.converse(**kwargs)


# ---------------------------------------------------------------------------
# Helper: streaming generator for st.write_stream
# ---------------------------------------------------------------------------
def stream_converse(model_id, messages, system=None, max_tokens=512, temperature=0.7):
    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        kwargs["system"] = [{"text": system}]
    response = bedrock_runtime.converse_stream(**kwargs)
    usage = {}
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                yield delta["text"]
        if "metadata" in event:
            usage = event["metadata"].get("usage", {})
    # Stash usage in session state so caller can read it after the generator
    st.session_state["_last_usage"] = usage


# ===================================================================
# TABS
# ===================================================================
tab_chat, tab_rag, tab_compare, tab_guard, tab_prompt = st.tabs(
    ["Chat", "RAG", "Model Compare", "Guardrails", "Prompt Lab"]
)

# ===================================================================
# TAB 1 — Chat
# ===================================================================
with tab_chat:
    # --- Sidebar controls ---
    with st.sidebar:
        st.header("Chat Settings")
        selected_model_name = st.selectbox("Model", list(MODELS.keys()), key="chat_model")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, key="chat_temp")
        max_tokens = st.slider("Max Tokens", 100, 2000, 512, key="chat_max")
        system_prompt = st.text_area("System Prompt (optional)", key="chat_system")

    model_id = MODELS[selected_model_name]

    # Initialise chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display existing messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Show user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build Converse messages list
        converse_messages = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in st.session_state.chat_messages
        ]

        sys = system_prompt.strip() if system_prompt else None

        # Stream assistant response
        with st.chat_message("assistant"):
            st.session_state["_last_usage"] = {}
            response_text = st.write_stream(
                stream_converse(model_id, converse_messages, system=sys,
                                max_tokens=max_tokens, temperature=temperature)
            )

        st.session_state.chat_messages.append({"role": "assistant", "content": response_text})

        # Token usage
        usage = st.session_state.get("_last_usage", {})
        if usage:
            st.caption(
                f"Tokens — input: {usage.get('inputTokens', 'N/A')}, "
                f"output: {usage.get('outputTokens', 'N/A')}, "
                f"total: {usage.get('totalTokens', 'N/A')}"
            )

# ===================================================================
# TAB 2 — RAG
# ===================================================================
with tab_rag:
    st.header("RAG — Knowledge Base Q&A")

    # Discover existing Knowledge Bases
    bedrock_agent_client = session.client("bedrock-agent")
    bedrock_agent_runtime = session.client("bedrock-agent-runtime")

    try:
        kb_response = bedrock_agent_client.list_knowledge_bases(maxResults=10)
        kb_list = kb_response.get("knowledgeBaseSummaries", [])
    except Exception as e:
        kb_list = []
        st.error(f"Could not list Knowledge Bases: {e}")

    if not kb_list:
        st.warning(
            "No Knowledge Bases found. Run **Lab 05 — RAG with Knowledge Bases** first, "
            "or create a Knowledge Base in the Bedrock console."
        )
    else:
        kb_options = {kb["name"]: kb["knowledgeBaseId"] for kb in kb_list}
        selected_kb_name = st.selectbox("Knowledge Base", list(kb_options.keys()), key="rag_kb")
        kb_id = kb_options[selected_kb_name]

        rag_model = st.selectbox("Model for generation", list(MODELS.keys()), key="rag_model")
        rag_model_id = MODELS[rag_model]

        question = st.text_input("Ask a question", key="rag_question")

        if st.button("Ask", key="rag_ask") and question:
            with st.spinner("Retrieving and generating..."):
                try:
                    rag_response = bedrock_agent_runtime.retrieve_and_generate(
                        input={"text": question},
                        retrieveAndGenerateConfiguration={
                            "type": "KNOWLEDGE_BASE",
                            "knowledgeBaseConfiguration": {
                                "knowledgeBaseId": kb_id,
                                "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{rag_model_id}",
                            },
                        },
                    )

                    answer = rag_response["output"]["text"]
                    st.subheader("Answer")
                    st.write(answer)

                    # Retrieved chunks / citations
                    citations = rag_response.get("citations", [])
                    if citations:
                        with st.expander("Retrieved Chunks & Citations", expanded=False):
                            for i, citation in enumerate(citations):
                                refs = citation.get("retrievedReferences", [])
                                for j, ref in enumerate(refs):
                                    st.markdown(f"**Chunk {i+1}.{j+1}**")
                                    content = ref.get("content", {}).get("text", "N/A")
                                    st.text(content[:500])
                                    location = ref.get("location", {})
                                    if location:
                                        st.caption(f"Source: {json.dumps(location, default=str)}")
                                    st.divider()

                except Exception as e:
                    st.error(f"RAG error: {e}")

# ===================================================================
# TAB 3 — Model Compare
# ===================================================================
with tab_compare:
    st.header("Model Comparison")

    compare_prompt = st.text_area("Prompt", key="compare_prompt",
                                  placeholder="Enter a prompt to send to multiple models...")
    compare_models = st.multiselect(
        "Select models to compare",
        list(MODELS.keys()),
        default=["Claude Sonnet 4.5", "Llama 3 8B"],
        key="compare_models",
    )

    if st.button("Compare", key="compare_run") and compare_prompt and compare_models:
        cols = st.columns(len(compare_models))
        messages = [{"role": "user", "content": [{"text": compare_prompt}]}]

        for idx, model_name in enumerate(compare_models):
            mid = MODELS[model_name]
            with cols[idx]:
                st.subheader(model_name)
                with st.spinner("Generating..."):
                    start = time.time()
                    try:
                        resp = call_converse(mid, messages, max_tokens=512, temperature=0.7)
                        elapsed = time.time() - start
                        output_text = resp["output"]["message"]["content"][0]["text"]
                        usage = resp.get("usage", {})

                        st.write(output_text)
                        st.caption(
                            f"Time: {elapsed:.2f}s | "
                            f"Input tokens: {usage.get('inputTokens', 'N/A')} | "
                            f"Output tokens: {usage.get('outputTokens', 'N/A')}"
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")

# ===================================================================
# TAB 4 — Guardrails
# ===================================================================
with tab_guard:
    st.header("Guardrails Testing")

    bedrock_control = session.client("bedrock")

    # --- Find or create guardrail ---
    @st.cache_resource
    def get_or_create_guardrail():
        """Return (guardrailId, guardrailVersion)."""
        try:
            existing = bedrock_control.list_guardrails(maxResults=10)
            for g in existing.get("guardrails", []):
                if g["name"] == "PlaygroundGuardrail":
                    return g["id"], "DRAFT"
        except Exception:
            pass

        # Create a default guardrail
        resp = bedrock_control.create_guardrail(
            name="PlaygroundGuardrail",
            description="Default guardrail for the GenAI Playground",
            topicPolicyConfig={
                "topicsConfig": [
                    {
                        "name": "InvestmentAdvice",
                        "definition": "Providing specific investment, stock trading, or financial planning recommendations",
                        "examples": [
                            "Should I buy AMZN stock?",
                            "What stocks should I invest in?",
                            "Is now a good time to invest in tech?",
                        ],
                        "type": "DENY",
                    }
                ]
            },
            sensitiveInformationPolicyConfig={
                "piiEntitiesConfig": [
                    {"type": "EMAIL", "action": "ANONYMIZE"},
                    {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
                ]
            },
            contentPolicyConfig={
                "filtersConfig": [
                    {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                    {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                    {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                    {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                    {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                    {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
                ]
            },
            blockedInputMessaging="Your request was blocked by the guardrail.",
            blockedOutputsMessaging="The model response was blocked by the guardrail.",
        )
        return resp["guardrailId"], "DRAFT"

    guardrail_id, guardrail_version = get_or_create_guardrail()
    st.info(f"Using guardrail: **{guardrail_id}** (version: {guardrail_version})")

    # Pre-loaded test prompts
    test_prompts = {
        "What is Amazon Bedrock? (safe)": "What is Amazon Bedrock?",
        "Should I invest in AMZN stock? (denied topic)": "Should I invest in AMZN stock?",
        "My email is john@example.com, my SSN is 123-45-6789 (PII)": "My email is john@example.com, my SSN is 123-45-6789. Can you help me?",
    }
    selected_test = st.selectbox("Test Prompts", list(test_prompts.keys()), key="guard_select")
    custom_input = st.text_area("Or enter custom input", key="guard_custom")

    prompt_text = custom_input.strip() if custom_input.strip() else test_prompts[selected_test]

    if st.button("Test Guardrail", key="guard_run"):
        messages = [{"role": "user", "content": [{"text": prompt_text}]}]
        guardrail_config = {
            "guardrailIdentifier": guardrail_id,
            "guardrailVersion": guardrail_version,
            "trace": "enabled",
        }
        with st.spinner("Testing..."):
            try:
                resp = call_converse(
                    MODELS["Claude Sonnet 4.5"],
                    messages,
                    max_tokens=512,
                    temperature=0.7,
                    guardrail_config=guardrail_config,
                )

                stop_reason = resp.get("stopReason", "unknown")
                output_text = resp["output"]["message"]["content"][0]["text"]

                # Determine action
                if stop_reason == "guardrail_intervened":
                    st.error(f"**Guardrail Action:** BLOCKED (stop reason: {stop_reason})")
                else:
                    st.success(f"**Guardrail Action:** ALLOWED (stop reason: {stop_reason})")

                st.subheader("Filtered Output")
                st.write(output_text)

                # Trace details
                trace = resp.get("trace", {}).get("guardrail", {})
                if trace:
                    with st.expander("Guardrail Trace Details", expanded=False):
                        st.json(trace)

            except Exception as e:
                st.error(f"Error: {e}")

# ===================================================================
# TAB 5 — Prompt Lab
# ===================================================================
with tab_prompt:
    st.header("Prompt Engineering Lab")

    technique = st.selectbox(
        "Technique",
        ["Zero-Shot", "Few-Shot", "Chain-of-Thought"],
        key="prompt_technique",
    )

    if technique == "Zero-Shot":
        st.markdown("**Zero-Shot:** Ask the model directly with no examples.")
        template = "Classify the following movie review as POSITIVE or NEGATIVE.\n\nReview: \"{input}\"\n\nClassification:"
        user_input = st.text_area("Movie review to classify", value="This film was absolutely brilliant and kept me on the edge of my seat.", key="prompt_input_zs")

    elif technique == "Few-Shot":
        st.markdown("**Few-Shot:** Provide a few examples before the actual task.")
        template = (
            "Classify each movie review as POSITIVE or NEGATIVE.\n\n"
            "Review: \"I loved every minute of this movie!\"\nClassification: POSITIVE\n\n"
            "Review: \"Terrible acting and a boring plot.\"\nClassification: NEGATIVE\n\n"
            "Review: \"A masterpiece of modern cinema.\"\nClassification: POSITIVE\n\n"
            "Review: \"{input}\"\nClassification:"
        )
        user_input = st.text_area("Movie review to classify", value="The movie was dull and I almost fell asleep.", key="prompt_input_fs")

    else:  # Chain-of-Thought
        st.markdown("**Chain-of-Thought:** Instruct the model to reason step by step.")
        template = (
            "Solve the following problem step by step. Show your reasoning before giving the final answer.\n\n"
            "Problem: {input}\n\n"
            "Step-by-step solution:"
        )
        user_input = st.text_area("Problem to solve", value="A store sells apples for $1.50 each. If you buy 5 or more, you get a 20% discount. How much do 7 apples cost?", key="prompt_input_cot")

    full_prompt = template.replace("{input}", user_input)

    prompt_model = st.selectbox("Model", list(MODELS.keys()), key="prompt_model")

    if st.button("Run", key="prompt_run") and user_input:
        with st.expander("Full Prompt Sent", expanded=False):
            st.code(full_prompt, language="text")

        messages = [{"role": "user", "content": [{"text": full_prompt}]}]
        with st.spinner("Generating..."):
            try:
                resp = call_converse(
                    MODELS[prompt_model], messages, max_tokens=512, temperature=0.7
                )
                output_text = resp["output"]["message"]["content"][0]["text"]
                usage = resp.get("usage", {})

                st.subheader("Response")
                st.write(output_text)
                st.caption(
                    f"Tokens — input: {usage.get('inputTokens', 'N/A')}, "
                    f"output: {usage.get('outputTokens', 'N/A')}, "
                    f"total: {usage.get('totalTokens', 'N/A')}"
                )
            except Exception as e:
                st.error(f"Error: {e}")
