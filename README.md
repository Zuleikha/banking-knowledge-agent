# Banking Knowledge Agent

A source-backed AI knowledge and support agent for a banking technology
platform — ATM and self-service banking, digital banking, cards, payments,
APIs, integrations, configuration and incident troubleshooting.

The goal is not "a chatbot". The goal is to demonstrate production-oriented AI
engineering: RAG, an agent loop, MCP tools, guardrails, testing, observability,
containerisation and clean architecture.

> **All banking documentation in this repository is synthetic**, written for
> this project. No proprietary, confidential or copyrighted material is used.

---

## Status

| | |
|---|---|
| **Current stage** | Stage 5 — Knowledge Agent |
| **Implemented** | Config, structured logging, tracing, health endpoint, knowledge base + loader, chunking, embeddings, vector store, retrieval, prompt management, context injection, provider seam, grounded answers, **the knowledge agent: question → decide → retrieve → ground → source-backed answer, or an explicit refusal** |
| **Not yet implemented** | A concrete LLM provider, MCP tools, tool selection, conversation context, web UI, Docker |

> **No paid API call exists in this repository.** The only LLM provider that ships is a
> deterministic in-process mock, so the whole project clones, runs and tests with no
> account, no API key and no spend.

Detailed progress and the exact next action live in
[`docs/HANDOVER.md`](docs/HANDOVER.md).

---

## Target architecture

```
User
 │
 ▼
Web Interface            ── Stage 9
 │
 ▼
API  (FastAPI)           ── Stage 1  ✅
 │
 ▼
Agent / LLM              ── Stages 4 ✅, 5 ✅ · Stage 7 (tool selection)
 │
 ├── RAG Knowledge Retrieval   ── Stages 2, 3  ✅
 ├── MCP Tools                 ── Stage 6
 ├── Conversation Context      ── Stage 8
 └── Guardrails                ── Stage 13
 │
 ▼
Source-backed Answer
```

Every layer sits behind an interface so knowledge sources, banking domains,
tools, LLM providers and vector stores can be added or swapped without a
redesign. See [`docs/architecture-guide.html`](docs/architecture-guide.html)
for the full reference.

---

## Technology stack

| Technology | Why it is here |
|---|---|
| **Python 3.12** | Ecosystem for LLM, embedding and vector tooling |
| **FastAPI** | Async API, typed request/response models, free OpenAPI docs |
| **Pydantic / pydantic-settings** | Validation at the boundary; typed env-based config |
| **structlog** | Log *events with fields*, not formatted strings — required for Stage 10 |
| **sentence-transformers** | Local `all-MiniLM-L6-v2` embeddings — semantic search with no API key and no per-query cost |
| **NumPy** | The vector index *is* a NumPy matrix; search is one `matrix @ query` |
| **pytest** | Test suite, including async API tests |
| **ruff / mypy** | Formatting, linting and strict type checking |

Nothing is included because it is fashionable — each entry has an
architectural job.

---

## Requirements

- Python 3.12+
- Git

> **Note:** on this machine the stdlib `venv` module is missing from the system
> Python install, so the setup below uses [`uv`](https://docs.astral.sh/uv/)
> (or `virtualenv`) to create the environment. Plain `python -m venv .venv`
> works fine on a healthy Python install.

---

## Setup

```bash
git clone https://github.com/Zuleikha/banking-knowledge-agent.git
cd banking-knowledge-agent

# Create the virtual environment (pick one)
uv venv .venv --python 3.12        # recommended here
# python -m venv .venv             # standard, if your Python has venv
# python -m virtualenv .venv       # fallback

# Install dependencies
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
# or:  .venv/Scripts/python.exe -m pip install -r requirements-dev.txt

# Configuration (optional — every setting has a safe default)
cp .env.example .env
```

`.env` is git-ignored and must never be committed.

---

## Run

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

| URL | What it is |
|---|---|
| <http://127.0.0.1:8000/health> | Liveness check |
| <http://127.0.0.1:8000/docs> | Interactive API documentation |
| <http://127.0.0.1:8000/openapi.json> | OpenAPI schema |

Example:

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "service": "Banking Knowledge Agent",
  "version": "0.1.0",
  "environment": "local"
}
```

---

## Test

```bash
.venv/Scripts/python.exe -m pytest                       # 489 tests
.venv/Scripts/python.exe -m pytest -m "not integration"  # skip the real model
.venv/Scripts/python.exe -m ruff check .                 # lint
.venv/Scripts/python.exe -m ruff format .                # format
.venv/Scripts/python.exe -m mypy                         # strict type check
```

Run pytest from the repository root.

Most RAG tests run on a deterministic hashing embedder, so the suite is fast and
offline. Tests marked `integration` load the real model and assert retrieval
*quality* — that each brief question finds its own document, and that off-topic
questions find nothing.

**Temp directory:** `tmp_path` is pointed at a project-local `.pytest_tmp/`
(git-ignored) via `--basetemp` in `pyproject.toml`, rather than
`%LOCALAPPDATA%\Temp\pytest-of-<user>`. pytest strips inherited ACLs from its temp
root, so if that directory is ever created by an **elevated** process it becomes
unwritable for normal runs — every `tmp_path` test then fails with
`PermissionError: [WinError 5]`, and the state persists because pytest reuses the
directory. An explicit basetemp is wiped at the start of each session, so it cannot
go stale that way.

---

## Repository layout

```
banking-knowledge-agent/
├── app/
│   ├── main.py              # FastAPI app factory and entry point
│   ├── api/
│   │   ├── dependencies.py  # Shared FastAPI dependencies
│   │   └── routes/
│   │       └── health.py    # GET /health
│   ├── core/
│   │   ├── config.py        # Typed, environment-based settings
│   │   ├── logging.py       # structlog configuration + on-disk sinks
│   │   └── tracing.py       # @traced / @traced_async decorators
│   ├── knowledge/
│   │   ├── models.py        # DocumentMetadata, KnowledgeDocument
│   │   └── loader.py        # Markdown + YAML front-matter loader
│   ├── rag/
│   │   ├── __main__.py      # CLI: build | search | demo | calibrate
│   │   ├── models.py        # Chunk, EmbeddedChunk, ScoredChunk, RetrievalResult
│   │   ├── chunker.py       # Heading-aware, token-budgeted splitting
│   │   ├── embeddings.py    # Embedder protocol + 2 implementations
│   │   ├── vectorstore.py   # VectorStore protocol + NumPy implementation
│   │   ├── retriever.py     # Question -> embedding -> search -> sources
│   │   └── pipeline.py      # build_index / load_retriever / fingerprint
│   ├── llm/                 # No vendor SDK is imported anywhere in here
│   │   ├── __main__.py      # CLI: prompt | ask | demo
│   │   ├── models.py        # CompletionRequest, LLMResponse, GroundedAnswer
│   │   ├── base.py          # LLMProvider protocol + error taxonomy
│   │   ├── prompts.py       # Versioned instructions, context budget + fencing
│   │   ├── mock.py          # Deterministic in-process provider (the only one)
│   │   ├── service.py       # Context injection -> generate -> validate -> answer
│   │   └── factory.py       # Provider selection from configuration
│   └── agent/               # The seam between rag/ and llm/
│       ├── __main__.py      # CLI: ask | demo
│       ├── models.py        # RetrievalDecision, RetrievalSummary, AgentAnswer
│       ├── policy.py        # decide_retrieval — is a knowledge search required?
│       ├── agent.py         # KnowledgeAgent.ask — decide, retrieve, generate, record
│       └── factory.py       # get_agent — composition from configuration
├── data/
│   ├── knowledge/           # 15 synthetic banking documents, by domain
│   └── vectorstore/         # Built index — git-ignored build artefact
├── tests/
│   ├── conftest.py          # Shared fixtures (settings, app, client, corpus, retriever)
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_logging.py
│   ├── test_loader.py
│   ├── test_chunker.py
│   ├── test_embeddings.py
│   ├── test_vectorstore.py
│   ├── test_retriever.py
│   ├── test_rag_integration.py   # Real model — retrieval quality
│   ├── test_llm_prompts.py       # Context budget, fencing, injection defence
│   ├── test_llm_provider.py      # Protocol, mock, factory, errors, no-network
│   ├── test_llm_service.py       # Injection, refusal, errors, provenance
│   ├── test_agent.py             # Routing, wiring, refusals, execution record
│   └── test_agent_integration.py # Real model — the 5 seed questions end to end
├── docs/
│   ├── HANDOVER.md          # Session recovery point — read this first
│   └── architecture-guide.html
├── .env.example
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Configuration

All settings are read from the environment with the `BKA_` prefix. See
[`.env.example`](.env.example) for the full documented list.

| Variable | Default | Purpose |
|---|---|---|
| `BKA_ENVIRONMENT` | `local` | `local` / `test` / `production` |
| `BKA_HOST` / `BKA_PORT` | `127.0.0.1` / `8000` | Bind address |
| `BKA_KNOWLEDGE_DIR` | `data/knowledge/` | Synthetic banking documents |
| `BKA_VECTORSTORE_DIR` | `data/vectorstore/` | Built index (git-ignored artefact) |
| `BKA_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Or `hashing` for no model download |
| `BKA_CHUNK_MAX_TOKENS` | *(unset)* | Unset = use the model's own limit |
| `BKA_RETRIEVAL_TOP_K` | `5` | Passages returned per question |
| `BKA_RETRIEVAL_MIN_SCORE` | `0.25` | Cosine floor; below it, retrieval returns nothing |
| `BKA_LLM_PROVIDER` | `mock` | The only constructible value; anything else raises |
| `BKA_LLM_MODEL` | *(unset)* | No vendor chosen yet |
| `BKA_LLM_MAX_TOKENS` | `4096` | Runaway-generation ceiling, not a target |
| `BKA_LLM_CONTEXT_MAX_CHUNKS` | `5` | How "never the whole knowledge base" is enforced |
| `BKA_LLM_CONTEXT_MAX_CHARS` | `12000` | Second half of the same budget |
| `BKA_LLM_API_KEY` | *(unset)* | Environment only; `SecretStr`; nothing can use it yet |
| `BKA_LOG_LEVEL` | `INFO` | Log verbosity |
| `BKA_LOG_FORMAT` | `console` | `console` locally, `json` in Docker |
| `BKA_LOG_DIR` | `logs/` | Where log and trace files are written |

Secrets come from the environment only. They are never hardcoded, never
committed, and never written to logs or traces. `BKA_LLM_API_KEY` is typed as a
Pydantic `SecretStr`, so it renders as `**********` in any repr or dump — the rule
is enforced by the type rather than by remembering, and asserted in the suite.

---

## Knowledge base

`data/knowledge/` holds 15 synthetic banking documents (~7,800 words) describing
a fictional *Meridian* banking platform, organised by domain: `atm`, `cards`,
`payments`, `digital-banking`, `api`, `configuration`, `operations`, `platform`.

All content is written specifically for this project. No vendor documentation,
branding or confidential material is reproduced.

Each document is Markdown with a YAML front-matter header:

```markdown
---
document_id: atm-transaction-lifecycle
title: ATM Transaction Lifecycle
domain: atm
component: TransactionSwitch
version: "4.2"
doc_type: reference
tags: [atm, withdrawal]
---

# ATM Transaction Lifecycle
...
```

| Field | Required | Notes |
|---|---|---|
| `document_id` | yes | Lowercase slug; **must match the filename** |
| `title` | yes | Human-readable name used in citations |
| `domain` | yes | One of the eight domains above |
| `component` | yes | Platform component the document describes |
| `version` | yes | Component version |
| `doc_type` | yes | `reference` / `api` / `configuration` / `runbook` / `troubleshooting` |
| `tags` | no | Free-form keywords |

Load the corpus:

```bash
.venv/Scripts/python.exe -c "from app.knowledge import load_knowledge_base; print(len(load_knowledge_base()), 'documents')"
```

The loader is strict on purpose: malformed front matter, an unknown domain, an
unrecognised key, a `document_id` that disagrees with its filename, a duplicate
id, an empty body or an empty knowledge directory all raise. A silently skipped
document would become an answer the agent cannot ground.

---

## RAG pipeline

Question → embedding → vector search → relevant documents → sources.
No LLM involved: retrieval is measurable on its own.

```bash
# Build the index (first run downloads ~90 MB from Hugging Face)
.venv/Scripts/python.exe -m app.rag build

# Ask a question
.venv/Scripts/python.exe -m app.rag search "Why would an ATM transaction fail after card authentication?"

# The representative examples: seed, paraphrased and off-topic questions
.venv/Scripts/python.exe -m app.rag demo

# Evidence behind the score threshold
.venv/Scripts/python.exe -m app.rag calibrate
```

Example output:

```
Q: Why would an ATM transaction fail after card authentication?
   1. 0.790  ATM Transaction Lifecycle — Why a transaction can fail after card authentication
             atm / TransactionSwitch v4.2 · atm/atm-transaction-lifecycle.md
   2. 0.627  Card Authentication and Authorisation — The authorisation decision
             cards / AuthorizationService v4.2 · cards/card-authentication.md
   sources: 2 document(s)

Q: What is the capital of France?
   NO MATCH — nothing scored above 0.25 of 115 chunks.
```

| Stage | What it does |
|---|---|
| **Chunking** | Splits on Markdown `##` headings. Size is budgeted in the *embedding model's own tokens*, because identifiers like `switch.downstream_timeout_ms` cost far more tokens than words (measured: 1.13–2.82 tokens per word). Oversized tables split row-wise, repeating the header. |
| **Embedding** | `all-MiniLM-L6-v2`, locally, 384 dimensions, L2-normalised. Behind an `Embedder` protocol. |
| **Vector store** | Exact cosine search over one NumPy matrix — 115 chunks needs no ANN index. Behind a `VectorStore` protocol. |
| **Retrieval** | Optional metadata pre-filter, top-k, then a cosine floor. Below the floor it returns **nothing**, which is what lets the agent say "I don't have that documented" instead of guessing. |

The index in `data/vectorstore/` is a **git-ignored build artefact** of
`data/knowledge/`. Its manifest pins the embedding model and a fingerprint of
the corpus, and loading refuses a mismatch — searching an index built by a
different model does not fail, it silently returns nonsense.

Full reasoning for every choice above, including the alternatives that were
rejected and why, is in §20 of
[`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## LLM abstraction

Retrieved context → prompt → generation → **an answer with its sources**.

```bash
# Show the EXACT prompt that would be sent — the interesting part is what is absent
.venv/Scripts/python.exe -m app.llm prompt "What component handles card authentication?"

# Retrieve and answer one question
.venv/Scripts/python.exe -m app.llm ask "How would I troubleshoot a failed cash withdrawal?"

# The seed questions end to end, plus one the corpus cannot answer
.venv/Scripts/python.exe -m app.llm demo
```

Example output:

```
Q  How would I troubleshoot a failed cash withdrawal?
A  Answering from the retrieved documentation. ... [1][2][3][4][5]
   [grounded: 5 of 5 passages used · prompt v1.0.0]
   [1] Troubleshooting a Failed Cash Withdrawal (atm/atm-cash-withdrawal-troubleshooting.md)
   ...
   [mock/mock-deterministic-v1 · in≈1310 out≈64 tokens]

Q  What is the capital of France?
A  The knowledge base does not contain enough information to answer this question.
   [refused: no passage cleared the score floor; no model call made]
```

| Piece | What it does |
|---|---|
| **`LLMProvider` protocol** | The seam. Nothing above `app/llm/` imports an SDK, names a model, or catches a vendor's exception type. A test parses every import in the package to keep it that way. |
| **Prompt management** | One frozen, versioned system prompt (`v1.0.0`) recorded on every answer, so a stored answer can be tied to the instructions that produced it. |
| **Context injection** | Retrieved passages only — capped at 5 passages / 12,000 characters, dropped *whole* rather than truncated. The knowledge base is never sent. |
| **Injection defence** | Passages are fenced, numbered, and declared untrusted data before the model sees them; delimiters occurring *inside* a passage are escaped so a document cannot break out of the fence. |
| **Error handling** | Six typed errors, each carrying `retryable`. Truncated, refused and empty generations **raise** — a half-finished sentence about a transaction limit reads as complete, which makes it worse than an error. |
| **No evidence → no call** | When retrieval finds nothing, the service refuses without calling the provider at all. A generation with zero context can only refuse or invent. |

**The only provider is a deterministic in-process mock.** No network, no key, no
cost — and that is structural rather than a discipline: no code path exists that
calls anything. Setting `BKA_LLM_PROVIDER` to anything else **raises** rather than
falling back to the mock, because an application that answers questions with a stub
while looking healthy is worse than one that refuses to start.

Full reasoning, including rejected alternatives, is in §20.4 of
[`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## Knowledge agent

Question → **decide** → retrieve → ground → a source-backed answer, or an explicit
refusal. This is the first component that owns a complete request.

```bash
# Answer one question
.venv/Scripts/python.exe -m app.agent ask "Why would an ATM transaction fail after card authentication?"

# The five seed questions, plus two the agent must decline for different reasons
.venv/Scripts/python.exe -m app.agent demo
```

Example output — the prose is the mock's wiring check, the **provenance** is the
part worth reading:

```
Q  Why would an ATM transaction fail after card authentication?
A  Answering from the retrieved documentation. ... [1][2][3][4][5]
   [decision: knowledge_required — ... the knowledge base was searched ...]
   [retrieval: 5 of 115 passages cleared 0.25 · top score 0.790]
   [grounded: 5 passage(s) in the prompt · prompt v1.0.0]
   [1] ATM Transaction Lifecycle — Why a transaction can fail after card
       authentication (atm/atm-transaction-lifecycle.md)

Q  What is the capital of France?
A  The knowledge base does not contain enough information to answer this question.
   [retrieval: 0 of 115 passages cleared 0.25 · top score none]
   [refused: no supporting evidence; no model call was made]

Q  !!! ???
A  The knowledge base does not contain enough information to answer this question.
   [decision: no_searchable_content — ... the knowledge base was not searched.]
   [retrieval: not performed]
```

**Three outcomes, distinguishable without reading the prose:**

| Outcome | How it is identified | What it means |
|---|---|---|
| Grounded answer | `is_grounded` | The documentation supports this, and here are the citations |
| Refused **after** searching | `refused` + `retrieval.performed` | We searched; nothing was close enough. *"We don't document this."* |
| Refused **without** searching | `refused` + `not retrieval.performed` | There was nothing to search for. *"That isn't a question."* |

A provider failure is none of the three — it **raises**. A broken model and an
undocumented answer need different responses from whoever is reading, and
collapsing them would quietly fold infrastructure noise into the refusal rate.

| Piece | What it does |
|---|---|
| **Routing decision** | `decide_retrieval()` returns a `RetrievalDecision` with the rule that produced it. Stage 5 has one substantive branch, and the module says why a keyword classifier or an LLM router would be a guess rather than a decision. |
| **One refusal path** | A question the agent declines to search is routed through the Stage 4 empty-evidence guard, not given a refusal of its own — so the insufficient-evidence sentence has exactly one definition in the system. |
| **Execution record** | `AgentAnswer` returns the decision and a retrieval summary alongside the answer, so a UI renders provenance instead of scraping logs. The summary carries *shape*; passage text stays out of it. |
| **A seam, not a layer** | The agent builds no prompts, owns no model and does no scoring. Retriever and service are injected, which is what keeps 104 agent tests offline, deterministic and free. |

Full reasoning, including rejected alternatives, is in §20.5 of
[`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## Logging

- **`logs/app.log`** — application events (JSON lines)
- **`logs/traces.log`** — `@traced` function traces, a separate sink so traces
  never pollute the application stream

Function arguments are deliberately never logged: they may carry customer data
or credentials.

---

## Licence

Personal portfolio project. Synthetic data only.
