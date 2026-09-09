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
| **Current stage** | Stage 3 — RAG Pipeline |
| **Implemented** | Config, structured logging, tracing, health endpoint, knowledge base + loader, **chunking, embeddings, vector store, retrieval** |
| **Not yet implemented** | LLM, agent, MCP, web UI, Docker |

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
Agent / LLM              ── Stages 4, 5, 7
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
.venv/Scripts/python.exe -m pytest                       # 240 tests
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
│   └── rag/
│       ├── __main__.py      # CLI: build | search | demo | calibrate
│       ├── models.py        # Chunk, EmbeddedChunk, ScoredChunk, RetrievalResult
│       ├── chunker.py       # Heading-aware, token-budgeted splitting
│       ├── embeddings.py    # Embedder protocol + 2 implementations
│       ├── vectorstore.py   # VectorStore protocol + NumPy implementation
│       ├── retriever.py     # Question -> embedding -> search -> sources
│       └── pipeline.py      # build_index / load_retriever / fingerprint
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
│   └── test_rag_integration.py   # Real model — retrieval quality
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
| `BKA_LOG_LEVEL` | `INFO` | Log verbosity |
| `BKA_LOG_FORMAT` | `console` | `console` locally, `json` in Docker |
| `BKA_LOG_DIR` | `logs/` | Where log and trace files are written |

Secrets come from the environment only. They are never hardcoded, never
committed, and never written to logs or traces.

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

## Logging

- **`logs/app.log`** — application events (JSON lines)
- **`logs/traces.log`** — `@traced` function traces, a separate sink so traces
  never pollute the application stream

Function arguments are deliberately never logged: they may carry customer data
or credentials.

---

## Licence

Personal portfolio project. Synthetic data only.
