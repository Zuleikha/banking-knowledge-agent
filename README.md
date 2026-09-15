# Banking Knowledge Agent

A source-backed AI support agent for a banking technology platform — ATM and self-service,
digital banking, cards, payments, APIs, configuration and incident troubleshooting. It answers
from its own documentation and from live support tools, cites every claim, and says plainly when
it does not know. The goal is not "a chatbot" but production-oriented AI engineering: retrieval,
an agent loop, MCP tools, conversation context, testing and clean, swappable boundaries.

> **All banking data in this repository is synthetic** — documents, error codes, component
> names and tool responses are invented for this project. No proprietary, confidential or
> copyrighted material is used.

---

## Status

| | |
|---|---|
| **Current stage** | **Stage 10 — Observability** implemented, awaiting approval |
| **Implemented** | Config, logging, tracing · knowledge base · RAG pipeline · LLM abstraction + Anthropic/OpenAI adapters · knowledge agent with rule-based decisions · six MCP tools + MCP server · conversation sessions · conversation API + web page · request ids, latency logging and in-process metrics |
| **Next** | Evaluation (11) · Docker (12) · guardrails and security (13) · production architecture (14) |

Detailed progress, decisions and the exact next action: [`docs/HANDOVER.md`](docs/HANDOVER.md).

---

## Architecture

```
Browser ──▶ Web page (static) ──▶ FastAPI  /api/sessions/*
                                     │
                                     ▼
                           ConversationService      session store · follow-up rules
                                     │
                                     ▼
                             KnowledgeAgent         decide: docs? tools? both? refuse?
                          ┌──────────┴──────────┐
                          ▼                     ▼
                  Retriever (RAG)         ToolRegistry (MCP)
                  documentation           live readings
                          └──────────┬──────────┘
                                     ▼
                              LLMService ──▶ LLMProvider   mock · anthropic · openai
                                     │
                                     ▼
                     Answer + sources + tool activity + route taken
```

Every layer sits behind a small interface (a Python `Protocol`), so embedders, vector stores,
LLM vendors, tools and session stores can be swapped without touching the layers around them.
Full reference, diagrams and decision records: [`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.12** | Language with the most mature LLM, embedding and vector-search ecosystem |
| **FastAPI + uvicorn** | HTTP API and static web page; typed models and generated OpenAPI docs |
| **Pydantic / pydantic-settings** | Validation at the boundary; typed `BKA_*` environment configuration |
| **structlog** | Structured log events with fields, written to `logs/` |
| **sentence-transformers** (`all-MiniLM-L6-v2`) | Local embeddings — semantic search, no API key, no per-query cost |
| **NumPy** | The vector index is one matrix; search is one matrix multiplication |
| **`anthropic` + `openai`** | Two vendor adapters behind one provider interface — neither is the default |
| **`mcp`** (pinned `1.12.4`) | Official Model Context Protocol SDK, used only by the MCP server |
| **PyYAML** | Document front matter, `safe_load` only |
| **pytest · ruff · mypy (strict)** | Tests, lint and format, static type checking |

---

## Requirements

- Python 3.12
- Git
- ~90 MB free for the embedding model (downloaded once from Hugging Face on first use)

No API key is needed. The default LLM provider is a free, deterministic, in-process mock.

---

## Setup

```bash
git clone https://github.com/Zuleikha/banking-knowledge-agent.git
cd banking-knowledge-agent

uv venv .venv --python 3.12                       # or: python -m venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt

cp .env.example .env                               # optional — every setting has a safe default
.venv/Scripts/python.exe -m app.rag build          # build the search index (git-ignored)
```

---

## Run

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload

.venv/Scripts/python.exe -m app.agent demo               # decision paths, end to end
.venv/Scripts/python.exe -m app.agent conversation-demo  # follow-up rules, end to end
.venv/Scripts/python.exe -m app.mcp demo                 # one call of each tool
```

| URL | What it is |
|---|---|
| <http://127.0.0.1:8000/> | Web page — ask questions, see sources, tool activity and the route taken |
| <http://127.0.0.1:8000/health> | Liveness check |
| <http://127.0.0.1:8000/metrics> | In-process counters and latency histograms (JSON) |
| <http://127.0.0.1:8000/docs> | Interactive API documentation |
| <http://127.0.0.1:8000/openapi.json> | OpenAPI schema |

---

## Test

```bash
.venv/Scripts/python.exe -m pytest                        # full suite
.venv/Scripts/python.exe -m pytest -m "not integration"   # skip the real embedding model
.venv/Scripts/python.exe -m ruff check . && .venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy
```

**1040 tests**, none of which call a paid API; 71 are marked `integration` and load the real embedding model.

---

## RAG Pipeline

```
Markdown docs ──▶ load + validate ──▶ chunk (## headings) ──▶ embed ──▶ NumPy index
question ──▶ embed ──▶ filter ──▶ cosine score ──▶ top-k ──▶ score floor ──▶ passages + sources
```

- 15 synthetic documents → 115 chunks, each within the model's 256-token window.
- Chunk size is measured in the embedding model's own tokens; tables keep their header row.
- Exact cosine search over one matrix — no approximate index needed at this size.
- A **score floor (0.25)** returns nothing when nothing is relevant, so the agent can refuse.
- The index manifest pins the model and a corpus fingerprint; a stale or foreign index is refused.

## LLM Abstraction

```
passages + tool results ──▶ budget ──▶ fenced prompt (v1.1.0) ──▶ LLMProvider ──▶ validate ──▶ GroundedAnswer
```

- One `LLMProvider` protocol; only the two adapter modules may import a vendor SDK (enforced by a test).
- Switching vendor is one setting: `BKA_LLM_PROVIDER=mock | anthropic | openai`.
- Spending needs two deliberate acts — a paid provider **and** `BKA_LLM_API_KEY`; `demo` refuses without `--paid`.
- Retrieved text is fenced and escaped as untrusted data (prompt-injection defence).
- No evidence → refusal with **no model call**; truncated, refused or empty generations raise.
- Seven typed errors, each with a `retryable` flag.

## Knowledge Agent

```
question ──▶ plan ──▶ call tools ──▶ search (once more if weak) ──▶ answer ──▶ record the route
```

- Five paths: answer from docs · retrieve more · call a tool · use both · refuse.
- Every choice is a **deterministic rule** — no model decides routing.
- A weak search (top score < 0.50) gets one refined retry; the score floor is never lowered.
- Tools are chosen from the registry's own specs (error codes, transaction refs, config keys, components).
- The answer carries **decisions, not reasoning**: route, each choice point, search and tool summaries.

## Conversation Context

```
session id + question ──▶ resolve follow-up (rules) ──▶ agent(question, earlier QUESTIONS) ──▶ store turn
```

- "Is it healthy?" becomes a standalone question using the previous question's identifiers or topic.
- The model sees earlier **questions** only, fenced as *not evidence*; earlier answers are never sent.
- Bounded: 3 earlier questions / 1000 characters sent · 50 turns · 1000 sessions · 30-minute idle expiry.
- In-memory store behind a `SessionStore` protocol; an unknown session id is an error, never a new session.

## Web Interface

```
index.html + app.js ──▶ POST /api/sessions · /ask · /turns · /end ──▶ ConversationService
```

- No build step: plain HTML, JavaScript and CSS served by FastAPI; all text inserted as text.
- Badges for RAG used, MCP tools used, sources consulted and insufficient information.
- The session id travels only in the JSON body — never in a URL or access log.
- Errors: unknown session → 404 · blank question → 422 · tool or model failure → 502, no internal detail.
- One question at a time per session (per-session lock).

## MCP Tools

```
KnowledgeAgent ──▶ ToolRegistry (in-process) ◀── MCP server (stdio JSON-RPC) ◀── any MCP client
                        │
                        ▼
      six synthetic tools, one module each
```

- `get_system_configuration` · `check_transaction_status` · `get_component_status` · `look_up_error_code` · `retrieve_system_version` · `check_service_health`.
- The tools exist once; the MCP server is a thin wrapper over the same registry.
- Pure and offline: no clock, network or file access — same arguments, same result.
- "Not found" is a normal result (`ok=False`); a malformed call raises.
- Tool results are untrusted input and get the same fencing as documents.

## Documentation vs Live Information

```
<retrieved_documentation>  [1] [2]  how the platform SHOULD behave
<tool_results>             [T1]     how it IS behaving now
```

- Kept apart end to end: separate prompt fences, citation forms and answer fields.
- They can disagree — e.g. a documented limit of 500.00 vs a live account override of 250.00 — and the answer must report both.
- `AgentAnswer.used_live_information` says whether any part of an answer came from a tool.

## Observability

```
request ──▶ middleware: X-Request-ID ──▶ rag · tools · llm (latency_ms each) ──▶ http.request (latency_ms)
                              │                                                        │
                              └──── request_id on every app + trace log line ──────────┴──▶ GET /metrics
```

- One `request_id` per HTTP request, on every log and trace line; returned in `X-Request-ID`.
- An incoming `X-Request-ID` is used only if it is 1–64 letters, digits or dashes; otherwise one is generated.
- `latency_ms` on retrieval, each LLM call, each tool call and the whole request; failures logged by error type only.
- The question is logged as a 12-character hash and a length — never the text; the query string is never logged.
- `GET /metrics`: in-memory counters and latency histograms as JSON; no new dependency; resets on restart.

---

## Configuration

All settings are optional `BKA_*` environment variables with safe defaults. Full descriptions and
defaults: [`.env.example`](.env.example). Secrets come from the environment only and are never logged.

| Area | Variables |
|---|---|
| App / server | `BKA_APP_NAME` `BKA_APP_VERSION` `BKA_ENVIRONMENT` `BKA_DEBUG` `BKA_HOST` `BKA_PORT` |
| Knowledge / RAG | `BKA_KNOWLEDGE_DIR` `BKA_VECTORSTORE_DIR` `BKA_EMBEDDING_MODEL` `BKA_EMBEDDING_DEVICE` `BKA_EMBEDDING_BATCH_SIZE` `BKA_CHUNK_MAX_TOKENS` `BKA_CHUNK_OVERLAP_TOKENS` `BKA_RETRIEVAL_TOP_K` `BKA_RETRIEVAL_MIN_SCORE` |
| Agent | `BKA_AGENT_CONFIDENT_SCORE` |
| Conversation | `BKA_CONVERSATION_MAX_HISTORY_TURNS` `BKA_CONVERSATION_MAX_HISTORY_CHARS` `BKA_CONVERSATION_MAX_TURNS` `BKA_CONVERSATION_MAX_SESSIONS` `BKA_CONVERSATION_TTL_SECONDS` |
| LLM | `BKA_LLM_PROVIDER` `BKA_LLM_MODEL` `BKA_LLM_MAX_TOKENS` `BKA_LLM_TIMEOUT_SECONDS` `BKA_LLM_MAX_RETRIES` `BKA_LLM_CONTEXT_MAX_CHUNKS` `BKA_LLM_CONTEXT_MAX_CHARS` `BKA_LLM_API_KEY` |
| Logging | `BKA_LOG_LEVEL` `BKA_LOG_FORMAT` `BKA_LOG_DIR` `BKA_LOG_TO_FILE` |

---

## Repository Structure

```
banking-knowledge-agent/
├── app/
│   ├── agent/           Knowledge agent: decisions, tool selection, answering
│   ├── api/             FastAPI dependencies, request middleware, routes (health, metrics, conversation)
│   ├── conversation/    Sessions, follow-up rules, conversation service
│   ├── core/            Settings, logging, tracing, observability (request ids, metrics)
│   ├── knowledge/       Document models and the strict loader
│   ├── llm/             Provider protocol, prompts, mock and vendor adapters
│   ├── mcp/             Tool contract, registry, MCP server, six tools
│   ├── rag/             Chunking, embeddings, vector store, retrieval
│   └── web/static/      The no-build web page
├── data/
│   ├── knowledge/       15 synthetic banking documents, by domain
│   └── vectorstore/     Built search index (git-ignored)
├── docs/
│   ├── HANDOVER.md              Progress, decisions, next action
│   ├── PROJECT_PLAN.md          Stage requirements
│   └── architecture-guide.html  Architecture reference and decision records
├── tests/               Unit, integration and API tests
├── CLAUDE.md            Working rules for AI-assisted development
├── .env.example         Documented configuration
├── pyproject.toml       pytest, ruff and mypy configuration
└── requirements*.txt    Pinned runtime and dev dependencies
```

---

## Engineering Focus

- **Grounded answers** — every claim cited; no evidence means an explicit refusal with no model call.
- **Deterministic, testable decisions** — routing, tool choice and follow-ups are rules, not model calls.
- **Swappable boundaries** — protocols for embedders, vector stores, LLM providers, tools and session stores.
- **Vendor neutrality, proven** — two real adapters behind one interface; switching is one setting.
- **Security by default** — prompt-injection fencing, secrets only from the environment, questions, tool argument values and session ids kept out of logs.
- **Observable** — a request id on every log line, per-step latency, and in-process metrics.
- **Cost safety** — free mock by default; paid calls need two deliberate settings.
- **Real protocols** — a genuine MCP server alongside the in-process registry.
- **Quality gates** — 1040 offline tests, strict mypy, ruff; retrieval quality measured with the real model.
- **Documented reasoning** — every design decision recorded with what was chosen, why and what was rejected.

---

## Licence

Personal portfolio project. Synthetic data only.
