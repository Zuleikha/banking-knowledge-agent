# HANDOVER — Banking Knowledge Agent

> **Read this first in any new Claude Code session.**
> This file, not conversation history, is the record of project progress.
> Never assume a previous session completed work unless the repository confirms it.

Last updated: **2026-09-03** · Session ended cleanly at this checkpoint.

---

## ⏱️ SESSION CHECKPOINT — start here

**Session ended:** 2026-09-03, immediately after Stage 1 was approved, committed and pushed.
**Nothing is in progress.** No half-finished work, no uncommitted changes, no blockers.

### State at checkpoint

| | |
|---|---|
| Last approved stage | **Stage 1 — Project Foundation** |
| `HEAD` | `d7f2619` (= `origin/main`, verified) |
| Working tree | Clean |
| Tests | 20 passed · ruff clean · mypy strict clean |
| Next stage | **Stage 2 — Domain Knowledge** (not started) |

### To resume

```bash
cd D:/PROJECTS/banking-knowledge-agent

# 1. Confirm the state matches this file before trusting it
git log --oneline -3          # expect d7f2619 on top
git status                    # expect clean

# 2. The venv already exists and is git-ignored. If it is missing, recreate it:
#    (system `python -m venv` is BROKEN on this machine -- see Problems §4)
#    uv venv .venv --python 3.12
#    uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt

# 3. Re-establish the baseline
./.venv/Scripts/python.exe -m pytest        # expect 20 passed
./.venv/Scripts/python.exe -m ruff check .  # expect All checks passed!
./.venv/Scripts/python.exe -m mypy          # expect Success: no issues found

# 4. Then read "Next Action" at the bottom of this file and begin Stage 2.
```

### Local files that are NOT in the remote (deliberately)

`prompt.md` · `ccp.txt` · `docs/decisions/auto-changes.log` · `.venv/` · `logs/` · caches.

A fresh clone will not contain `prompt.md` — the project brief lives only on this
machine. Keep it; the stage definitions come from it.

---

## Current Stage

| | |
|---|---|
| **Stage number** | 1 |
| **Stage name** | Project Foundation |
| **Status** | ✅ **COMPLETE AND APPROVED BY THE USER — committed and pushed** |
| **Last completed step** | Stage 1 approved 2026-09-03; committed `d448cc1` and pushed to `origin/main` |
| **Next step** | **Begin Stage 2 — Domain Knowledge** (synthetic banking documentation + loader) |

> ⛔ Stage 2 must STOP after implementation and testing, and wait for explicit approval
> before any commit or push.

---

## Current Work

### Implemented

- Clean repository structure (`app/`, `tests/`, `docs/`) — no nested project directory
- `requirements.txt` (runtime) and `requirements-dev.txt` (test/tooling), all pinned
- `.gitignore` — covers `.env`, secrets, keys, venvs, caches, `logs/`, build artefacts
- `.env.example` — every setting documented; no real secret values
- `README.md` — setup, run, test, layout, configuration
- `pyproject.toml` — pytest, ruff and mypy(strict) configuration
- **Application entry point** — `app/main.py` with a `create_app()` factory and lifespan logging
- **Configuration management** — `app/core/config.py`, typed/frozen `Settings` from `BKA_*` env vars
- **Structured logging** — `app/core/logging.py`, structlog → stdout + rotating JSON files
- **Tracing** — `app/core/tracing.py`, `@traced` / `@traced_async` → dedicated on-disk sink
- **Health endpoint** — `GET /health`
- **Test structure** — `tests/` with shared fixtures; 20 tests
- `docs/HANDOVER.md` (this file)
- `docs/architecture-guide.html` — full personal architecture reference

### Currently being worked on

Nothing. Stage 1 is approved and pushed. Stage 2 has not been started.

### Not yet implemented (later stages)

Knowledge base and loader (2) · RAG pipeline (3) · LLM abstraction (4) · Knowledge agent (5) ·
MCP tools (6) · Tool selection (7) · Conversation context (8) · Web interface (9) ·
Request observability (10) · Evaluation framework (11) · Docker (12) · Security review (13) ·
Production architecture (14) · Final review (15)

---

## Architecture

### Current

```
HTTP request
   │
   ▼
FastAPI app  (app/main.py — create_app factory)
   │   settings stored on app.state
   ▼
Router  (app/api/routes/health.py)
   │   SettingsDep reads request.app.state.settings
   ▼
Pydantic-validated response
   │
   ├──▶ logs/app.log      structured application events
   └──▶ logs/traces.log   @traced function traces (separate sink)
```

### Components implemented

| Component | Responsibility |
|---|---|
| `app/main.py` | App factory, router mounting, lifespan startup/shutdown logging |
| `app/core/config.py` | Typed, frozen, env-based `Settings`; cached `get_settings()` |
| `app/core/logging.py` | structlog + stdlib bridge; app sink and separate trace sink |
| `app/core/tracing.py` | `@traced` / `@traced_async` structured trace decorators |
| `app/api/dependencies.py` | `SettingsDep` — resolves settings from `app.state` |
| `app/api/routes/health.py` | `GET /health` liveness endpoint |

### Important design decisions

| Decision | Reasoning |
|---|---|
| App **factory** (`create_app()`) | Tests build an app with overridden settings instead of mutating globals |
| Settings from **`app.state`**, not cached global | Factory is the single source of truth (see Problems §1) |
| **structlog from Stage 1** | Stage 10 needs queryable fields; retrofitting means rewriting every call site |
| **Separate trace sink**, `propagate = False` | High-volume traces would bury operational events in the app log |
| **Never log traced arguments** | They may carry card data, customer IDs or API keys |
| **`@traced` not on route handlers** | Breaks FastAPI annotation resolution (see Problems §2) |
| **Frozen settings** | Config mutating at runtime is a debugging trap |
| **Pinned dependencies** | Local, CI and Docker resolve identically |
| **mypy strict** | Catches contract drift across the many interfaces coming in Stages 3–6 |

---

## Files

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI application factory and entry point (`uvicorn app.main:app`) |
| `app/core/config.py` | All configuration, from `BKA_*` environment variables |
| `app/core/logging.py` | Structured logging setup; `configure_logging`, `reset_logging`, `get_logger` |
| `app/core/tracing.py` | `traced`, `traced_async` — structured function tracing to disk |
| `app/api/dependencies.py` | Shared FastAPI dependencies (`SettingsDep`) |
| `app/api/routes/health.py` | `GET /health` + `HealthResponse` model |
| `tests/conftest.py` | Fixtures: `settings` (logs → `tmp_path`), `app`, `client` |
| `tests/test_config.py` | Configuration behaviour and validation |
| `tests/test_health.py` | Health endpoint, OpenAPI, 404, settings wiring |
| `tests/test_logging.py` | Log/trace files, sink separation, secret-safety, tracing errors |
| `pyproject.toml` | pytest / ruff / mypy configuration |
| `requirements.txt` | Pinned runtime dependencies |
| `requirements-dev.txt` | Pinned test and tooling dependencies |
| `.env.example` | Documented configuration template (no secrets) |
| `.gitignore` | Excludes secrets, venvs, caches, logs, and local working files |
| `README.md` | Developer setup and usage |
| `docs/HANDOVER.md` | This recovery file |
| `docs/architecture-guide.html` | Personal architecture reference |
| `prompt.md`, `ccp.txt` | Project brief and workflow rules — **local only, git-ignored** |
| `docs/decisions/auto-changes.log` | Written by a local Claude Code hook — **git-ignored** |

---

## Testing

### Result

**20 passed, 0 failed.** `ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 10 source files*
Live `uvicorn` startup verified: `/health` 200, `/openapi.json` 200, `/docs` 200;
both log sinks written and correctly separated.

| Test file | Tests | Covers |
|---|---|---|
| `tests/test_config.py` | 6 | Defaults, env overrides, invalid port/environment rejected, caching, immutability |
| `tests/test_health.py` | 5 | 200 + payload, exact schema, OpenAPI, 404, settings wiring |
| `tests/test_logging.py` | 9 | Log to disk, trace sink separation, sync/async trace ok+error paths, arguments never logged, metadata preserved, idempotent config |

### Commands used

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m mypy
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload   # manual startup check
curl http://127.0.0.1:8000/health
```

### Stage 1 required test coverage

| Requirement | Status |
|---|---|
| Virtual environment setup | ✅ Verified (see Problems §3) |
| Dependency installation | ✅ Verified — all imports succeed |
| Application startup | ✅ Verified via `TestClient` **and** a live `uvicorn` run |
| Health endpoint | ✅ 5 tests + live `curl` returning 200 |
| Test suite | ✅ 20 tests passing; lint and strict types clean |

---

## Problems and Decisions

### 1. Health endpoint ignored the app's settings — FIXED

`GET /health` used `Depends(get_settings)`, the cached global, so it reported the
process-wide environment rather than the settings the app was actually built with.
The test suite caught it (`assert 'local' == 'test'`).

**Fix:** `app/api/dependencies.py` resolves settings from `request.app.state.settings`,
making the app factory the single source of truth.

### 2. `@traced` cannot decorate FastAPI route handlers — RESOLVED, CONSTRAINT DOCUMENTED

Wrapping a handler in `@traced_async` caused `422` responses and OpenAPI generation
failures. Cause: with `from __future__ import annotations`, FastAPI resolves a handler's
postponed annotations against that function's `__globals__`. A wrapper defined in
`app/core/tracing.py` resolves them against the tracing module, where `SettingsDep` does
not exist — so the dependency silently degraded into a query parameter.

**Decision:** route handlers are **not** decorated. Request-level tracing is added as
middleware in Stage 10, which is the correct layer for it anyway. The constraint is
documented in `app/core/tracing.py`, `app/api/routes/health.py` and
`architecture-guide.html` §13.

### 3. Stale `.git/HEAD.lock` blocked the first commit attempt — RESOLVED

`git commit` failed with *"cannot lock ref 'HEAD'"*. A zero-byte `.git/HEAD.lock` dated
12:50 — predating this session's work — was left behind by an earlier crashed git
process. Confirmed no `git.exe` was running, then removed the stale lock. The commit
succeeded immediately after. If this recurs, check for a running git process **first**.

### 4. Broken system Python `venv` — WORKED AROUND

`python -m venv` fails on this machine: `No module named venv` (system Python at
`D:\Python\Python312` is a partial install). A `virtualenv`-created environment was
worse — it segfaulted on `import structlog` and `import httpx`.

**Decision:** use `uv venv .venv --python 3.12` (CPython 3.12.13). All imports and the
full suite work. Documented in `README.md`; plain `python -m venv` remains correct on a
healthy install.

### Assumptions

- `prompt.md` is authoritative over `ccp.txt` where they differ (`ccp.txt` says
  "Phase 0"; `prompt.md` defines Stage 1 as the first stage). Started at Stage 1.
- `prompt.md` and `ccp.txt` are user-provided briefs kept local and git-ignored. They
  exist on disk in the repository root but will never appear in the remote.
- Global engineering rules require `@traced` on new functions. Applied to application
  functions, with three documented exceptions: FastAPI route handlers (§2 above),
  `tracing._emit` (would recurse infinitely), and trivial Pydantic property accessors.

### 5. Unexpected file: `docs/decisions/auto-changes.log` — RESOLVED

A user-configured Claude Code hook appends every file edit to
`docs/decisions/auto-changes.log`. It was **not** created by Stage 1 work and contains no
secrets — only timestamps and file paths.

**Decision (user, 2026-09-03):** git-ignored. The file stays on disk for the hook to
append to, but is never committed.

### Resolved questions

| Question | User's decision (2026-09-03) |
|---|---|
| Commit `prompt.md` and `ccp.txt`? | **No — keep local.** Both are git-ignored. |
| Commit `docs/decisions/auto-changes.log`? | **No — git-ignored.** |

### Open questions for the user

None.

### Security check

✅ No secrets, keys, tokens or credentials anywhere in the repository.
✅ No real `.env` file exists. `.env` and `.env.*` are git-ignored (`.env.example` excepted).
✅ `logs/` is git-ignored. Traced function arguments are never logged.

---

## Git

| | |
|---|---|
| **Branch** | `main` |
| **Remote** | `origin` → `https://github.com/Zuleikha/banking-knowledge-agent.git` |
| **Previous commit** | `a2bd8e5` — "initial commit" (contained only `.gitignore`) |
| **Stage 1 commit** | `d448cc1` — `feat(stage-1): project foundation — config, logging, tracing, health` |
| **Push status** | ✅ Pushed to `origin/main`; verified `origin/main == local HEAD` (`d448cc1`) |
| **Working tree** | Clean, apart from git-ignored local files |
| **Committed in Stage 1** | 23 files: 22 added, `.gitignore` modified |
| **Deliberately not committed** | `prompt.md`, `ccp.txt`, `docs/decisions/auto-changes.log`, `.venv/`, `logs/`, caches |

---

## Next Action

**Begin Stage 2 — Domain Knowledge.** Stage 1 is approved, committed and pushed.

Stage 2 scope (from `prompt.md` §10):

1. Write synthetic banking technical documentation under `data/knowledge/`, covering:
   ATM transactions · card authentication · payment processing · digital banking ·
   API integration · configuration · common errors · incident troubleshooting ·
   system components. Enough content that retrieval is meaningful.
2. Implement document loading in `app/knowledge/loader.py`.
3. Attach metadata to every document: **document, domain, component, version, doc_type**.
4. Add document-loading tests in `tests/test_loader.py`.
5. Update `docs/architecture-guide.html` (§2 structure, §4 components, §6 RAG flow).
6. Update this handover.
7. **STOP** and wait for approval. Do not commit or push Stage 2 unapproved.

Constraints carried forward:

- Synthetic content only. No proprietary, confidential or copyrighted material.
- Documents are data, not instructions — they become untrusted LLM input in Stage 5.
- No secrets in documents, tests or logs.
- Do not create a nested `banking-knowledge-agent/` directory.
