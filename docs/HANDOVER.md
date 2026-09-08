# HANDOVER — Banking Knowledge Agent

> **Read this first in any new Claude Code session.**
> This file, not conversation history, is the record of project progress.
> Never assume a previous session completed work unless the repository confirms it.

Last updated: **2026-09-08** · Stage 2 approved, committed and pushed.

---

## ⏱️ SESSION CHECKPOINT — start here

**Session ended:** 2026-09-08, immediately after Stage 2 was approved, committed and pushed.
**Nothing is in progress.** No half-finished work, no uncommitted changes, no blockers.

### State at checkpoint

| | |
|---|---|
| Last approved stage | **Stage 2 — Domain Knowledge** |
| `HEAD` | *(recorded in the follow-up docs commit)* (= `origin/main`, verified) |
| Working tree | Clean |
| Tests | 72 passed · ruff clean · mypy strict clean |
| Next stage | **Stage 3 — RAG Pipeline** (not started) |

### To resume

```bash
cd D:/PROJECTS/banking-knowledge-agent

# 1. Confirm the state matches this file before trusting it
git log --oneline -3          # expect the stage-2 docs commit on top
git status                    # expect clean

# 2. The venv already exists and is git-ignored. If it is missing, recreate it:
#    (system `python -m venv` is BROKEN on this machine -- see Problems §4)
#    uv venv .venv --python 3.12
#    uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt

# 3. Re-establish the baseline
./.venv/Scripts/python.exe -m pytest        # expect 72 passed
./.venv/Scripts/python.exe -m ruff check .  # expect All checks passed!
./.venv/Scripts/python.exe -m mypy          # expect Success: no issues found

# 4. Then read "Next Action" at the bottom of this file.
```

### Local files that are NOT in the remote (deliberately)

`prompt.md` · `ccp.txt` · `docs/decisions/auto-changes.log` · `.venv/` · `logs/` · caches.

A fresh clone will not contain `prompt.md` — the project brief lives only on this
machine. Keep it; the stage definitions come from it.

---

## Current Stage

| | |
|---|---|
| **Stage number** | 2 |
| **Stage name** | Domain Knowledge |
| **Status** | ✅ **COMPLETE AND APPROVED BY THE USER — committed and pushed** |
| **Last completed step** | Stage 2 approved 2026-09-08; committed *(hash in the follow-up docs commit)* and pushed to `origin/main` |
| **Next step** | **Begin Stage 3 — RAG Pipeline** (chunking, embeddings, vector store, retrieval) |

> ⛔ Stage 3 must STOP after implementation and testing, and wait for explicit approval
> before any commit or push.

### Previous stage

| | |
|---|---|
| **Stage 1** | Project Foundation |
| **Status** | ✅ Complete, approved 2026-09-03, committed `d448cc1`, pushed |

---

## Current Work

### Implemented in Stage 2

- **Synthetic knowledge corpus** — `data/knowledge/`, 15 Markdown documents,
  ~7,800 words, across all eight domains. Describes a fictional *Meridian*
  banking platform invented for this project.
- **Document metadata schema** — `app/knowledge/models.py`.
  `DocumentMetadata` carries the five required fields (document, domain,
  component, version, doc_type) plus optional tags. `Domain` and `DocType` are
  closed `Literal` sets; unknown front-matter keys are rejected.
- **Document loader** — `app/knowledge/loader.py`. Parses Markdown + YAML front
  matter into validated `KnowledgeDocument` objects, deterministically ordered.
- **Typed error hierarchy** — `KnowledgeLoadError` and five specific subclasses,
  so callers can distinguish a malformed document from a missing directory.
- **Configuration** — `BKA_KNOWLEDGE_DIR` added to `Settings` and `.env.example`.
- **Tests** — `tests/test_loader.py`, 52 new tests (20 → 72 total).
- **Docs** — `README.md` and `docs/architecture-guide.html` updated.

### Currently being worked on

Nothing. Stage 2 is approved and pushed. Stage 3 has not been started.

### Not yet implemented (later stages)

RAG pipeline (3) · LLM abstraction (4) · Knowledge agent (5) · MCP tools (6) ·
Tool selection (7) · Conversation context (8) · Web interface (9) ·
Request observability (10) · Evaluation framework (11) · Docker (12) ·
Security review (13) · Production architecture (14) · Final review (15)

---

## Architecture

### Current

```
data/knowledge/**/*.md         Markdown + YAML front matter
   │
   ▼  loader.split_front_matter
(front matter, body)
   │
   ▼  loader.parse_metadata  → yaml.safe_load → DocumentMetadata (validated)
   │
   ▼  loader.load_document   → id/filename check, empty-body check
KnowledgeDocument(metadata, content, source_path)
   │
   ▼  loader.load_knowledge_base → sorted, duplicate-id checked
tuple[KnowledgeDocument, ...]        ← Stage 3 chunks and embeds this
   │
   ├──▶ logs/app.log      "knowledge.loaded" event
   └──▶ logs/traces.log   @traced function traces (separate sink)

HTTP request
   │
   ▼
FastAPI app  (app/main.py — create_app factory)
   │
   ▼
Router  (app/api/routes/health.py)  →  Pydantic-validated response
```

The knowledge layer is deliberately **not** wired into the API yet. Stage 2 owns
document sourcing only; retrieval is Stage 3 and the agent is Stage 5.

### Components implemented

| Component | Responsibility |
|---|---|
| `app/main.py` | App factory, router mounting, lifespan startup/shutdown logging |
| `app/core/config.py` | Typed, frozen, env-based `Settings`; cached `get_settings()` |
| `app/core/logging.py` | structlog + stdlib bridge; app sink and separate trace sink |
| `app/core/tracing.py` | `@traced` / `@traced_async` structured trace decorators |
| `app/api/dependencies.py` | `SettingsDep` — resolves settings from `app.state` |
| `app/api/routes/health.py` | `GET /health` liveness endpoint |
| `app/knowledge/models.py` | `DocumentMetadata`, `KnowledgeDocument`, `Domain`, `DocType` |
| `app/knowledge/loader.py` | Front-matter parsing, validation, corpus loading, errors |

### Important design decisions (Stage 2)

| Decision | Reasoning |
|---|---|
| **Markdown + YAML front matter** | The body *is* the text Stage 3 chunks and embeds; it stays readable in a diff; metadata travels with the content it describes |
| **`yaml.safe_load`, never `load`** | Front matter must not be able to construct arbitrary Python objects |
| **Closed `Literal` sets for domain and doc_type** | A typo should fail the load, not silently create a domain nothing filters on |
| **`extra="forbid"` on metadata** | A misspelled `compnent:` would otherwise be dropped and the document would lose the field retrieval filters on |
| **Loader raises instead of skipping** | A silently skipped document becomes an answer the agent cannot ground — much harder to diagnose than a failed load |
| **Empty knowledge dir is an error** | Otherwise it surfaces as an agent that answers nothing, with no signal as to why |
| **`document_id` must equal the filename stem** | Citations are addressed by id; the two disagreeing makes a citation unresolvable |
| **`source_path` normalised to POSIX** | A citation must read identically on Windows and inside a Linux container |
| **Deterministic (sorted) ordering** | Indexing runs and test assertions stay reproducible |
| **Frozen models** | A retrieved document must not be mutable by the code that consumes it |
| **Corpus scanned for secrets in the test suite** | A banking corpus is exactly where a fake-looking-but-real credential would hide |
| **Documents kept free of instruction-like prose** | From Stage 5 they are untrusted LLM input |

---

## Files

### Added in Stage 2

| File | Purpose |
|---|---|
| `app/knowledge/__init__.py` | Package exports (models, loader, error types) |
| `app/knowledge/models.py` | `DocumentMetadata`, `KnowledgeDocument`, `Domain`, `DocType` |
| `app/knowledge/loader.py` | `load_document`, `load_knowledge_base`, error hierarchy |
| `tests/test_loader.py` | 52 tests: loader behaviour, failure modes, corpus validity, corpus security |
| `data/knowledge/atm/atm-transaction-lifecycle.md` | Eight-stage lifecycle; why a transaction fails *after* authentication |
| `data/knowledge/atm/atm-cash-withdrawal-troubleshooting.md` | Six-step withdrawal diagnosis procedure |
| `data/knowledge/atm/atm-device-states.md` | Terminal states, cassettes, dispense outcomes |
| `data/knowledge/cards/card-authentication.md` | AuthorizationService: identification, verification, decisions |
| `data/knowledge/cards/card-pin-verification.md` | CardSecurityModule, HSM pool, PIN and cryptogram errors |
| `data/knowledge/payments/payment-authorisation-api.md` | `POST /v1/payments/authorise`, idempotency, statuses, errors |
| `data/knowledge/payments/payment-processing-overview.md` | Authorise → capture → clear → settle; reversals |
| `data/knowledge/digital-banking/digital-channel-overview.md` | DigitalGateway: sessions, step-up, rate limits |
| `data/knowledge/api/api-integration-guide.md` | Shared API conventions: auth, headers, errors, retries |
| `data/knowledge/api/core-banking-integration.md` | CoreBankingAdapter: operations, balances, timeouts |
| `data/knowledge/configuration/transaction-limits-configuration.md` | Limit keys, precedence, account-not-card scope |
| `data/knowledge/configuration/configuration-reference.md` | ConfigurationStore, timeout and channel keys |
| `data/knowledge/operations/error-code-reference.md` | Every error code by component, with fault class |
| `data/knowledge/operations/incident-response-runbook.md` | Severity, blast radius, component checks |
| `data/knowledge/platform/platform-component-overview.md` | The nine components and the request paths |

### Modified in Stage 2

| File | Change |
|---|---|
| `app/core/config.py` | Added `knowledge_dir` setting |
| `.env.example` | Documented `BKA_KNOWLEDGE_DIR` |
| `requirements.txt` | Pinned `PyYAML==6.0.2` (was only an implicit uvicorn extra) |
| `requirements-dev.txt` | Added `types-PyYAML` for mypy strict |
| `tests/conftest.py` | Added `knowledge_root` fixture |
| `.gitignore` | Added `.pytest_tmp/` (see Problems §9) |
| `README.md` | Status, layout, configuration table, new "Knowledge base" section |
| `docs/architecture-guide.html` | §1 stages, §2 structure, §3 stack, §4 components, §6 RAG, §12 config, §14 testing, §16 security |

### From Stage 1 (unchanged)

`app/main.py` · `app/core/logging.py` · `app/core/tracing.py` ·
`app/api/dependencies.py` · `app/api/routes/health.py` · `tests/test_config.py` ·
`tests/test_health.py` · `tests/test_logging.py` · `pyproject.toml` · `.gitignore`

---

## Testing

### Result

**72 passed, 0 failed** (20 from Stage 1, 52 new).
`ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 13 source files*
Manual corpus load verified: 15 documents, 8 domains, 9 components, ~7,800 words,
`knowledge.loaded` event written to the app sink and traces to the separate sink.

| Test file | Tests | Covers |
|---|---|---|
| `tests/test_config.py` | 6 | Defaults, env overrides, invalid port/environment, caching, immutability |
| `tests/test_health.py` | 5 | 200 + payload, exact schema, OpenAPI, 404, settings wiring |
| `tests/test_logging.py` | 9 | Log to disk, trace sink separation, sync/async ok+error paths, arguments never logged |
| `tests/test_loader.py` | 52 | See breakdown below |

### `tests/test_loader.py` breakdown

| Group | Tests | Covers |
|---|---|---|
| Valid loading | 8 | Metadata parsed, front matter stripped, POSIX relative path, tags, BOM tolerated, citation, immutability |
| Front-matter failures | 6 | Missing, unterminated, invalid YAML, scalar, empty file, split helper |
| Metadata failures | 11 | Each of the 5 required fields missing, unknown domain, unknown doc_type, unrecognised key, id/filename mismatch, non-slug id, empty body |
| Directory loading | 7 | Nested dirs, deterministic order, missing dir, empty dir, duplicate ids, one bad doc fails the load, default from settings |
| Corpus validity | 14 | Document count, all 8 domains, complete metadata, unique ids, substantial content, doc types, components, 8 seed-question phrases |
| Corpus security | 3 | No secret-shaped values, no card-number-shaped digit runs, no vendor names |
| Type contracts | 3 | Closed `Domain`/`DocType` sets, blank component rejected |

### Commands used

```bash
./.venv/Scripts/python.exe -m pytest        # 72 passed
./.venv/Scripts/python.exe -m ruff check .  # All checks passed!
./.venv/Scripts/python.exe -m mypy          # Success: no issues found in 13 source files

# Manual corpus check
./.venv/Scripts/python.exe -c "from app.knowledge import load_knowledge_base; print(len(load_knowledge_base()), 'documents')"
```

### Stage 2 required coverage (prompt.md §10)

| Requirement | Status |
|---|---|
| Synthetic docs: ATM transactions | ✅ `atm-transaction-lifecycle` |
| Synthetic docs: card authentication | ✅ `card-authentication`, `card-pin-verification` |
| Synthetic docs: payment processing | ✅ `payment-processing-overview`, `payment-authorisation-api` |
| Synthetic docs: digital banking | ✅ `digital-channel-overview` |
| Synthetic docs: API integration | ✅ `api-integration-guide`, `core-banking-integration` |
| Synthetic docs: configuration | ✅ `transaction-limits-configuration`, `configuration-reference` |
| Synthetic docs: common errors | ✅ `error-code-reference` |
| Synthetic docs: incident troubleshooting | ✅ `incident-response-runbook`, `atm-cash-withdrawal-troubleshooting` |
| Synthetic docs: system components | ✅ `platform-component-overview`, `atm-device-states` |
| Enough content for meaningful retrieval | ✅ 15 documents, ~7,800 words, min 431 words each |
| Document loading implemented | ✅ `app/knowledge/loader.py` |
| Metadata: document, domain, component, version, doc type | ✅ All five required and validated |
| No real vendor documentation | ✅ All synthetic; asserted by test |
| Document-loading tests | ✅ 52 tests |
| Handover updated | ✅ This file |

---

## Problems and Decisions

### 6. `PyYAML` was an undeclared transitive dependency — RESOLVED

The loader needs YAML. `PyYAML` was already importable because
`uvicorn[standard]` pulls it in, so the tests would have passed before it was
declared. That is a trap: a change to uvicorn's extras would break the loader
with no prior signal.

**Fix:** `PyYAML==6.0.2` pinned in `requirements.txt` as a direct dependency, and
`types-PyYAML` added to `requirements-dev.txt` for mypy strict.

### 7. `pip` is unavailable inside the uv-created venv — WORKED AROUND

`./.venv/Scripts/python.exe -m pip` fails with *No module named pip*: `uv venv`
does not install pip by default. Use
`uv pip install --python .venv/Scripts/python.exe <package>` instead. Consistent
with Problems §4.

### 8. `pytest.raises(Exception)` rejected by ruff `B017` — RESOLVED

Two tests asserted immutability and validation with a bare `Exception`. Ruff's
`B017` flagged them as too broad, correctly: they would pass on an unrelated
failure. Replaced with `pydantic.ValidationError`, which is what both cases
actually raise. Warnings were fixed rather than suppressed, per the global rules.

### 9. `.pytest_tmp/` almost got committed — RESOLVED

During the pre-commit review, `git add -An` listed 33 pytest temporary fixture
files under a `.pytest_tmp/` directory in the repository root. It was not
git-ignored, so it would have been committed alongside Stage 2.

The directory could not be reproduced afterwards: deleting it and re-running the
suite from both Git Bash and PowerShell did not recreate it, and nothing in
`pyproject.toml`, `.claude/` or the environment configures a project-local
pytest basetemp. It appears to have been a one-off from a shell invocation where
the temp root did not resolve.

**Fix:** `.pytest_tmp/` added to `.gitignore`. The cause is unexplained, so the
lesson is the process rather than the directory: **always list the exact file set
`git add` would stage before committing**, rather than trusting `git status`
summary lines, which collapse untracked directories into a single entry.

### Carried forward from Stage 1

- **§1** Health endpoint settings resolution — fixed, `SettingsDep` reads `app.state`.
- **§2** `@traced` cannot decorate FastAPI route handlers — constraint documented;
  request tracing arrives as middleware in Stage 10.
- **§3** Stale `.git/HEAD.lock` blocked a commit — if it recurs, check for a
  running `git.exe` **first**, then remove the lock.
- **§4** System `python -m venv` is broken on this machine — use `uv venv`.
- **§5** `docs/decisions/auto-changes.log` is written by a local hook — git-ignored.

### Assumptions

- `prompt.md` is authoritative over `ccp.txt` where they differ.
- `prompt.md` and `ccp.txt` are local, git-ignored briefs; they will never appear
  in the remote.
- Global rules require `@traced` on new functions. Applied to every new loader
  function, with the documented exceptions: FastAPI route handlers, `tracing._emit`,
  and trivial Pydantic property accessors (`KnowledgeDocument.citation`).
- The platform described in the corpus (*Meridian*, its components, error codes,
  API paths and configuration keys) is entirely invented for this project and is
  internally consistent so that cross-document retrieval is meaningful.

### Open questions for the user

None.

### Security check

✅ No secrets, keys, tokens or credentials anywhere in the repository.
✅ No real `.env` file exists. `.env` and `.env.*` are git-ignored (`.env.example` excepted).
✅ `logs/` is git-ignored. Traced function arguments are never logged.
✅ Corpus scanned by the test suite for secret-shaped values and card-number-shaped
digit runs; no matches.
✅ `yaml.safe_load` only — front matter cannot construct arbitrary Python objects.
✅ No nested `banking-knowledge-agent/` directory.

---

## Git

| | |
|---|---|
| **Branch** | `main` |
| **Remote** | `origin` → `https://github.com/Zuleikha/banking-knowledge-agent.git` |
| **Stage 1 commit** | `d448cc1` — `feat(stage-1): project foundation — config, logging, tracing, health` |
| **Stage 2 commit** | *(recorded in the follow-up docs commit)* — `feat(stage-2): synthetic banking knowledge base and document loader` |
| **Stage 2 docs commit** | *(this commit's successor)* — `docs(stage-2): record commit hash and push result in handover` |
| **Push status** | ✅ Pushed to `origin/main`; verified `origin/main == local HEAD` |
| **Working tree** | Clean, apart from git-ignored local files |
| **Committed in Stage 2** | 28 files: 19 added, 9 modified |
| **Deliberately not committed** | `prompt.md`, `ccp.txt`, `docs/decisions/auto-changes.log`, `.venv/`, `logs/`, caches |

---

## Next Action

**Begin Stage 3 — RAG Pipeline.** Stage 2 is approved, committed and pushed.

### Stage 3 scope (from `prompt.md` §11), for when it starts

1. Chunking in `app/rag/chunker.py`, carrying document metadata onto every chunk.
2. Embedding generation behind an interface (`app/rag/embeddings.py`).
3. A `VectorStore` protocol plus a local implementation (`app/rag/vectorstore.py`)
   so the store can be replaced later. Index artefacts go to `data/vectorstore/`,
   which is already git-ignored.
4. Retrieval and similarity search in `app/rag/retriever.py`, returning source
   metadata. Must be independently testable without an LLM.
5. Retrieval tests plus representative examples.
6. Update `docs/architecture-guide.html` §6 and this handover.
7. **STOP** and wait for approval.

Constraints carried forward:

- Synthetic content only. No proprietary, confidential or copyrighted material.
- Documents are data, not instructions — they become untrusted LLM input in Stage 5.
- No secrets in documents, tests or logs.
- Never spend money or call a paid API without explicit confirmation — relevant
  from Stage 3, since a hosted embedding model would be a paid call.
- Do not create a nested `banking-knowledge-agent/` directory.
