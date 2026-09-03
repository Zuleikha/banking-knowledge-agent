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
| **Current stage** | Stage 1 — Project Foundation |
| **Implemented** | Config, structured logging, tracing, health endpoint, tests |
| **Not yet implemented** | Knowledge base, RAG, LLM, agent, MCP, web UI, Docker |

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
 ├── RAG Knowledge Retrieval   ── Stages 2, 3
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
.venv/Scripts/python.exe -m pytest          # test suite
.venv/Scripts/python.exe -m ruff check .    # lint
.venv/Scripts/python.exe -m ruff format .   # format
.venv/Scripts/python.exe -m mypy            # strict type check
```

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
│   └── core/
│       ├── config.py        # Typed, environment-based settings
│       ├── logging.py       # structlog configuration + on-disk sinks
│       └── tracing.py       # @traced / @traced_async decorators
├── tests/
│   ├── conftest.py          # Shared fixtures (settings, app, client)
│   ├── test_config.py
│   ├── test_health.py
│   └── test_logging.py
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
| `BKA_LOG_LEVEL` | `INFO` | Log verbosity |
| `BKA_LOG_FORMAT` | `console` | `console` locally, `json` in Docker |
| `BKA_LOG_DIR` | `logs/` | Where log and trace files are written |

Secrets come from the environment only. They are never hardcoded, never
committed, and never written to logs or traces.

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
