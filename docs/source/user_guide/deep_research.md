# Deep Research

`kanoa` supports "Deep Research" workflows that go beyond single-turn interpretation. These backends can perform multi-step reasoning, browse the web, and synthesize information from multiple sources before providing an answer.

## Supported Backends

| Backend | Type | Provider | Best For |
| :--- | :--- | :--- | :--- |
| `gemini-deep-research` | Official Agent | Google AI Studio | General research, GDrive integration, Free Tier users |
| `gemini-example-custom-research` | Custom Implementation | Vertex AI | Enterprise control, transparent RAG + Search, "White-box" research |

## Official Gemini Deep Research

The `gemini-deep-research` backend wraps Google's official `deep-research-pro-preview-12-2025` agent via the Interactions API.

### Prerequisites

- **Google AI Studio API Key**: This backend currently requires an API key from [AI Studio](https://aistudio.google.com/).
- **Library Support**: Requires `google-genai >= 2.0`.

### Usage

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="gemini-deep-research",
    api_key="YOUR_API_KEY",  # pragma: allowlist secret
    # Optional configuration
    max_research_time=600,  # 10 minutes
    enable_thinking_summaries=True
)

# The interpreter will stream status updates as it researches
iterator = interpreter.interpret(
    context="Investigating recent breakthroughs in solid state batteries.",
    focus="Summarize the top 3 papers from the last 6 months."
)

for chunk in iterator:
    if chunk.type == "status":
        print(f"Status: {chunk.content}")
    elif chunk.type == "text":
        print(chunk.content, end="")
```

### Features

- **Thinking Summaries**: By default, the agent streams its "thought process" (e.g., "Searching for X...", "Reading paper Y...").
- **File Search**: You can connect to existing File Search stores in AI Studio.

```python
interpreter = AnalyticsInterpreter(
    backend="gemini-deep-research",
    file_search_stores=["fileSearchStores/my-research-docs"]
)
```

## Custom Research (Vertex AI)

The `gemini-example-custom-research` backend is a reference implementation of a "white-box" research agent built on Vertex AI. Unlike the official agent, this backend explicitly orchestrates the research steps in Python, giving you full visibility and control.

### Architecture

1. **RAG Retrieval**: First, it queries your local Knowledge Base (if provided).
2. **Prompt Construction**: It synthesizes a research plan based on the user query and RAG results.
3. **Google Search**: It uses the Vertex AI `google_search` tool to find external information.
4. **Synthesis**: It combines internal knowledge and external search results into a final answer.

### Prerequisites

- **Google Cloud Project**: A GCP project with Vertex AI API enabled.
- **Authentication**: Application Default Credentials (ADC) configured (`gcloud auth application-default login`).

### Usage

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="gemini-example-custom-research",
    project="my-gcp-project",
    location="us-central1",
    # Optional: Connect a local Knowledge Base
    kb_path="./docs/internal_reports"
)

iterator = interpreter.interpret(
    context="Analyze our Q3 sales performance.",
    focus="Compare against competitor X's public earnings report."
)
```

### When to use Custom Research?

- **Transparency**: You need to know exactly *why* the agent decided to search for a specific term.
- **Control**: You want to force the agent to check internal documents *before* going to the web.
- **Enterprise Security**: You need to run entirely within your VPC/Vertex AI environment without using AI Studio API keys.
