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
| **Current stage** | Stage 6 — MCP Tools |
| **Implemented** | Config, structured logging, tracing, health endpoint, knowledge base + loader, chunking, embeddings, vector store, retrieval, prompt management, context injection, provider seam, grounded answers, the knowledge agent, two concrete LLM adapters (Anthropic + OpenAI), **six MCP support tools**, **an in-process tool registry**, **a real MCP server over stdio** |
| **Not yet implemented** | LLM-driven tool selection, conversation context, web UI, Docker |

> **Cloning this repository and running its tests costs nothing.** `BKA_LLM_PROVIDER`
> defaults to a deterministic in-process **mock** — no account, no API key, no spend.
>
> Two real vendor adapters ship (see [LLM providers](#llm-providers--two-adapters-and-why) below), but
> spending needs **two** deliberate acts: switch `BKA_LLM_PROVIDER` **and** set
> `BKA_LLM_API_KEY`. Neither adapter can even be constructed without a key, and the
> multi-question `demo` commands refuse to run against a paid provider without `--paid`.
> **No live API call has ever been made from this repository.**

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
| **`anthropic` + `openai`** | Two adapters behind one seam, so a vendor swap is a config line. Neither is the default; installing them does not enable spending |
| **`mcp`** | The official Model Context Protocol SDK. Used only by the protocol server; the in-process registry the agent calls needs no SDK. Pinned to `1.12.4` — 2.x requires a Starlette that breaks the pinned FastAPI |
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
.venv/Scripts/python.exe -m pytest                       # 775 tests
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
│   ├── mcp/
│   │   ├── __main__.py      # CLI: list | call | demo | serve
│   │   ├── models.py        # ToolSpec, ToolResult, ToolInvocation  (the contract)
│   │   ├── base.py          # Tool protocol + error taxonomy        (the contract)
│   │   ├── registry.py      # register / list / call — what the agent uses
│   │   ├── factory.py       # get_tool_registry — explicit registration
│   │   ├── server.py        # REAL MCP server over stdio (mcp SDK)
│   │   └── tools/           # One module per tool, each owning its own data
│   ├── rag/
│   │   ├── __main__.py      # CLI: build | search | demo | calibrate
│   │   ├── models.py        # Chunk, EmbeddedChunk, ScoredChunk, RetrievalResult
│   │   ├── chunker.py       # Heading-aware, token-budgeted splitting
│   │   ├── embeddings.py    # Embedder protocol + 2 implementations
│   │   ├── vectorstore.py   # VectorStore protocol + NumPy implementation
│   │   ├── retriever.py     # Question -> embedding -> search -> sources
│   │   └── pipeline.py      # build_index / load_retriever / fingerprint
│   ├── llm/
│   │   ├── __main__.py      # CLI: prompt | ask | demo
│   │   ├── models.py        # CompletionRequest, LLMResponse, GroundedAnswer
│   │   ├── base.py          # LLMProvider protocol + error taxonomy    <- seam
│   │   ├── prompts.py       # Versioned instructions, budget + fencing <- seam
│   │   ├── mock.py          # Deterministic in-process provider (default)
│   │   ├── service.py       # Context injection -> generate -> validate
│   │   ├── factory.py       # Provider selection from configuration
│   │   ├── anthropic_provider.py  # Anthropic adapter  <- 1 of 2 vendor modules
│   │   └── openai_provider.py     # OpenAI adapter     <- the other
│   │   #  ^ these two are the ONLY files allowed to import a vendor SDK,
│   │   #    enforced by an AST test over the rest of the package
│   └── agent/               # The seam across rag/, mcp/ and llm/
│       ├── __main__.py      # CLI: ask | demo
│       ├── models.py        # AgentDecision, RetrievalSummary, ToolCallSummary, AgentAnswer
│       ├── policy.py        # decide — search? tools? neither?
│       ├── tool_policy.py   # select_tools — route on identifiers, not topics
│       ├── agent.py         # KnowledgeAgent.ask — decide, retrieve, call tools, generate
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
│   ├── test_llm_adapters.py      # Both vendors, offline — shapes + error mapping
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

Full reasoning, including rejected alternatives, is in §20.4 of
[`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## LLM providers — two adapters, and why

```bash
BKA_LLM_PROVIDER=mock       # DEFAULT · deterministic, in-process, FREE
BKA_LLM_PROVIDER=anthropic  # real Anthropic API · PAID · needs BKA_LLM_API_KEY
BKA_LLM_PROVIDER=openai     # real OpenAI API    · PAID · needs BKA_LLM_API_KEY
```

Switching vendor is **that one line**. No application code changes — not the
service, not the agent, not the CLI. That is the claim an abstraction makes, and
building the *second* adapter is what turns it into evidence: with one adapter,
a seam is indistinguishable from a wrapper shaped around a single vendor's API.

Neither is "the" chosen vendor. The point was to prove the seam and close the
question, not to pick a supplier.

**What the seam actually absorbs** — the two APIs disagree about nearly
everything that crosses it:

| Concern | Anthropic | OpenAI |
|---|---|---|
| System instructions | top-level `system=` | a `system`-role message |
| Output ceiling | `max_tokens` | `max_completion_tokens` |
| Why it stopped | `stop_reason`, 7 values | `finish_reason`, 5 values |
| A refusal | `stop_reason="refusal"` | `message.refusal` — while `finish_reason` still says `"stop"` |
| The generated text | text blocks in a list, possibly after a thinking block | `message.content`, nullable |
| Token counts | `input_tokens` / `output_tokens` | `prompt_tokens` / `completion_tokens` |

Two of those are traps, and both are passing tests: reading `content[0]` on
Anthropic returns *reasoning* as the answer once thinking is on, and trusting
`finish_reason` alone on OpenAI hands back an empty string labelled complete
when the model actually refused.

### Spending is guarded in four places

1. **`BKA_LLM_PROVIDER` defaults to `mock`** — asserted by a test that clears
   the environment variable first.
2. **Neither adapter can be constructed without `BKA_LLM_API_KEY`.** It raises
   *before* an SDK client exists, and it does **not** fall through to
   `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, which both SDKs would read silently.
3. **Every adapter test injects a fake client.** The test settings carry no key,
   so a test that forgot would fail rather than reach the internet.
4. **The `demo` commands refuse a paid run** without `--paid`, checking before
   an index or a client is built. `ask` only warns — one call is a
   proportionate mistake; seven is not.

```
$ BKA_LLM_PROVIDER=anthropic python -m app.agent demo
!! BKA_LLM_PROVIDER=anthropic - this is a PAID API.
!! Every answered question is a billed call. Unset the variable, or
!! set BKA_LLM_PROVIDER=mock, to run free.
REFUSED: demo would make up to 7 paid calls. Re-run with --paid to confirm.
```

**No live API call has ever been made from this repository** — not in the suite,
not by hand. The adapters are proven correct in what they *send, parse and
translate*; whether a real model answers *well* is unmeasured, and is Stage 11's
job. The 99 adapter tests run offline against a fake SDK client, which covers
more than a live call would: every stop-reason value and all nine error mappings,
rather than one happy path.

Full reasoning is in §20.5.6–§20.5.9 of
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
| **Routing decision** | `decide()` returns an `AgentDecision` carrying the rule that produced it and any tool calls to make. Stage 6 added a second real branch — tools alongside retrieval — selected on *identifiers* in the question rather than on topic keywords. |
| **One refusal path** | A question the agent declines to search is routed through the Stage 4 empty-evidence guard, not given a refusal of its own — so the insufficient-evidence sentence has exactly one definition in the system. |
| **Execution record** | `AgentAnswer` returns the decision and a retrieval summary alongside the answer, so a UI renders provenance instead of scraping logs. The summary carries *shape*; passage text stays out of it. |
| **A seam, not a layer** | The agent builds no prompts, owns no model and does no scoring. Retriever and service are injected, which is what keeps 104 agent tests offline, deterministic and free. |

Full reasoning, including rejected alternatives, is in §20.5 of
[`docs/architecture-guide.html`](docs/architecture-guide.html).

---

## MCP tools

Six synthetic banking support tools, reachable two ways: in-process through a tool
registry (what the agent uses), and over the real Model Context Protocol via stdio
(what any MCP client can use). The tools exist once; the protocol server is a thin
wrapper over the same registry, not a second implementation.

Built with **parallel sub-agent development**: the shared tool contract was written
first, then six sub-agents implemented one tool each concurrently against it, then the
results were integrated and reconciled in a single pass. The method, including the
inconsistencies it produced and how they were resolved, is documented in §21 of the
architecture guide.

| Tool | Arguments | Answers |
|---|---|---|
| `get_system_configuration` | `component`, `key` | The **effective** value of a config key, its version, and which precedence level supplied it |
| `check_transaction_status` | `transaction_reference` | How far a transaction got through the eight lifecycle stages, why it stopped, its reversal state |
| `get_component_status` | `component` | Operational state: instances, error rate, throughput, backlog, active incident |
| `look_up_error_code` | `error_code` | Meaning, owning component, class, whether it is a wrapper code, the config key it breached |
| `retrieve_system_version` | `component` *(optional)* | Running version per component or fleet-wide, and any drift from the platform build |
| `check_service_health` | `component` *(optional)* | The liveness probe and its dependency checks — one service or all nine |

```bash
.venv/Scripts/python.exe -m app.mcp list      # the six specs and their arguments
.venv/Scripts/python.exe -m app.mcp demo      # one worked call of each, plus a miss
.venv/Scripts/python.exe -m app.mcp call look_up_error_code error_code=PAY-8003
.venv/Scripts/python.exe -m app.mcp serve     # the real MCP server, stdio JSON-RPC
```

All six are synthetic and offline by construction — each reads a dictionary defined in
its own module. There is no socket, no clock and no filesystem access anywhere in the
layer, so `invoke` is pure: the same arguments always give the same result.

### Documentation is not live information

This is the point of the stage, not a detail of it. RAG answers *what the documentation
says*; a tool answers *what the system is reportedly doing now*. The two are kept apart
all the way through — separate collection, separate fences in the prompt, separate
citation forms, separate fields on the answer:

| | Documentation | Live tool reading |
|---|---|---|
| In the prompt | `<retrieved_documentation>` | `<tool_results>` |
| Cited as | `[1]`, `[2]` | `[T1]`, `[T2]` |
| On the answer | `sources`, `chunks_used` | `tool_results`, `tools_used` |

They are kept apart because they can **disagree**, and when they do the disagreement is
usually the answer:

```
Q: What is LimitService limits.atm.per_transaction_amount set to?

  [1]  documentation   "limits.atm.per_transaction_amount | decimal | 500.00"
  [T1] live tool        value = 250.00, precedence = account_override,
                        reason = "Fraud pattern FP-2291: temporary account-level cap"
```

Both are true. Reporting only the documented default would be confidently wrong. The
system prompt requires the model to report both and say which is which, and
`AgentAnswer.used_live_information` tells a caller in one boolean whether any part of an
answer came from a tool.

### Tool results are untrusted input

They get **the same** injection defence Stage 4 built for retrieved passages — the same
escaping function, one delimiter list, a second fence — rather than a parallel scheme
that could drift from it. A tool result that contains `</tool_results>`, or that tries to
forge a `<retrieved_documentation>` block, is defused and visibly so.

That matters more for tools than for documents: a document is written once and reviewed,
while a tool result is assembled at request time from whatever the backing system holds —
which in a real deployment includes fields an attacker can write.

`get_system_configuration` additionally refuses any key that looks like a credential
(ConfigurationStore holds operational values only), and refuses it *before* checking
whether the component exists, so the refusal cannot be used to discover which components
are real.

### Finding nothing is not failing

| Situation | Result |
|---|---|
| No transaction has that reference | `ok=False`, **returned** — a true, useful answer |
| The service is `DOWN` | `ok=True`, returned — the tool *did* determine the health |
| A required argument is missing | `ToolInputError`, **raised** — the call is wrong, not the answer |
| No such tool | `ToolNotFoundError`, raised |

`ok` describes the lookup, never the thing looked at. Getting that backwards would make
"the service is down" indistinguishable from "there is no such service".

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
