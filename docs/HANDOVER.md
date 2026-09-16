# HANDOVER — Banking Knowledge Agent

> **Read this first in any new Claude Code session.**
> This file, not conversation history, is the record of project progress.
> Never assume a previous session completed work unless the repository confirms it.

**A decision is not recorded until it is written here.** If a decision is made mid-stage,
before implementation begins, write it down immediately — not at stage completion.

📦 **History lives in [`HANDOVER-archive.md`](HANDOVER-archive.md).** This file was trimmed
from 2934 lines to current state on 2026-09-16. Everything removed — Stage 5–11 decision
sections, resolved problems, superseded Next Actions, long-form architecture/files/testing —
is preserved there verbatim. Design decisions are also committed in
`docs/architecture-guide.html` §20. **Do not read the archive unless you need history.**

---

## ⏱️ SESSION CHECKPOINT — start here

**Stage 12 — Containerisation — is APPROVED, committed `27739f2` and pushed** (verified
`origin/main == local HEAD`). Approved 2026-09-16 after the one open question (24
pre-existing `ruff format` files) was answered: leave them, carry to Stage 13 (decision
**12.H**, guide §20.49).

| | |
|---|---|
| Last **approved** stage | **Stage 12 — Containerisation** (2026-09-16, `27739f2`) |
| Current stage | **None in progress** — Stage 13 not started |
| `HEAD` | `e60335c` (handover) on top of `27739f2` (Stage 12) = `origin/main` |
| Working tree | Clean, apart from git-ignored local files |
| Tests | **1141 passed, 4 skipped** · ruff clean · mypy strict clean (70 source files) · in-image pytest 1141 passed · container smoke 4 passed |
| Next | **Stage 13 — Security and Production Readiness** when the user asks |

### Commits, 2026-09-16 session

| Commit | What |
|---|---|
| `27739f2` | **Stage 12 — Containerisation** (9 files) |
| `e60335c` | Handover: Stage 12 hash and push result |

---

## Current Stage

| | |
|---|---|
| **Stage number** | 12 |
| **Stage name** | Containerisation |
| **Status** | ✅ **APPROVED 2026-09-16 — committed and pushed** |
| **Last completed step** | Re-verified after approval: 1141 passed / 4 skipped, ruff and mypy clean, `git add -An` = 9 files, no secrets, no nested directory, `.env` untracked. Guide status markers set to Stage 12 (pill, footer, §1 table; §1 diagram deliberately unchanged — containerisation is not on the request path) |
| **Next step** | Stage 13 — Security and Production Readiness — begins when the user asks |

| Stage | Name | Status |
|---|---|---|
| 12 | Containerisation | ✅ 2026-09-16, `27739f2` |
| 11 | Testing and Evaluation | ✅ 2026-09-15, `7b8c85e` |
| 10 | Observability | ✅ 2026-09-15, `c627358` (+ `42788e8`) |
| 9 | Web Interface | ✅ 2026-09-14, `2484b73` |
| 8 | Conversation Context | ✅ 2026-09-14, `2abbb39` |
| 7 | Agent Decision and Tool Selection | ✅ 2026-09-14, `a3728d9` |
| 6 | MCP Tools | ✅ 2026-09-11, `93eeb22` |
| 1–5 | Foundation → LLM abstraction → Knowledge agent | ✅ all approved (hashes in *Git*) |

---

## Current Work

**Nothing in progress.** Stage 12 closed; Stage 13 not started.

### Stage 12 decisions (12.A–12.H) — full records in guide §20.43–§20.49

| # | Decision |
|---|---|
| 12.A | **Model and index baked into the image** at build time — container runs fully offline, starts fast, index always matches the docs in the image |
| 12.B | **CPU-only PyTorch on `python:3.12-slim`**, same pinned version read from `requirements.txt` — the default Linux wheel drags in GBs of unused CUDA |
| 12.C | **`compose.yaml` = one `app` service**, port 8000, provider `mock`, `./logs` bind-mounted to the host |
| 12.D | **`HEALTHCHECK` on `GET /health` only**, via a Python one-liner (slim has no `curl`). **`GET /ready` moved to Stage 13** |
| 12.E | **"Test through Docker" = both** — full pytest inside the image (`test` target) *and* a smoke test against the running container |
| 12.F | **Runs as non-root user `app`**, owning the model cache, index and log directory |
| 12.G | `BKA_HOST`/`BKA_PORT` are read by **no app code**; uvicorn's flags are what apply. The image sets them and `CMD` passes them through. App code unchanged — wiring them is a Stage 13 candidate |
| 12.H | **The 24 files `ruff format` would rewrite are left unchanged**, carried to Stage 13. All pre-existing; none is a Stage 12 file. `ruff check` (lint) is clean — cosmetics only |

### Deliberately unfinished — Stage 11 (evaluation)

1. **`off-006`, `off-007` answered instead of refused** — banking-adjacent questions clear the 0.25 floor. A real hallucination-resistance gap. Candidates: higher floor for refined searches, hybrid search, or a reranker. **Needs a user decision.**
2. `know-018` evidence lacks `TransactionSwitch` — reported, not gated.
3. **Paid mode never run.** `--paid` implemented and guarded; no real-model answer scored. Needs explicit confirmation at the time.
4. Mentions in free mode are checked against retrieved evidence, not answer wording.
5. Same author wrote corpus, routing rules and dataset — defensible, not independent.
6. API behaviour covered by Stage 9/10 tests, not re-scored by the evaluation.

### Deliberately unfinished — Stage 10 (observability)

1. **`GET /metrics` is unauthenticated** (like `/health`); names and numbers only → **Stage 13**.
2. Metrics are per-process and reset on restart; JSON, not Prometheus → Stage 14.
3. `httpx` full-URL logging — **resolved (10.E)**, raised to `warning`.
4. A 500 from an unhandled exception carries no `X-Request-ID` header (Starlette builds it outside the middleware); the `http.request_failed` log line does carry the id.
5. **Untraced by deliberate exception (10.F):** `Metrics`/`_Histogram` methods, `elapsed_ms`, `get_metrics`, `reset_metrics`, the middleware's inner response wrapper — they run inside the measurements.
6. **Stale "Stage 7 … a model" wording** remains in `app/mcp/models.py` (`ToolSpec`, `input_schema`, `ToolInvocation`) and `app/mcp/base.py` (module docstring, `ToolInputError`) — fix in the next stage that touches `app/mcp/`.

### Guide readability pass (plain English, `CLAUDE.md` §4)

§1–§19 done · §20 intro and Stage 3 records done (`889585d`) · **remaining: §20 Stage 4–6
records, then §21.** Stage 7–12 records were written to the standard when made.
Readability-only edits go in their own `docs(guide)` commit, never while another stage's
guide edits are uncommitted.

---

## Architecture

Full reference: **`docs/architecture-guide.html`** (§1 overview and diagram, §20 decision
records 20.1–20.49). Subsystem summaries: `README.md`.

```
User → Web Interface (9) → API/FastAPI (1) → Agent/LLM (4,5,7)
                                                 ├─▶ RAG retrieval      (2,3)
                                                 ├─▶ MCP tools          (6)
                                                 ├─▶ Conversation ctx   (8)
                                                 ├─▶ Observability      (10)
                                                 └─▶ Guardrails         (13, planned)
                                              → Source-backed answer
```

Key properties, all load-bearing:

- **Seams are protocols, not ABCs** — `LLMProvider`, `Embedder`, `VectorStore`, `Tool`.
- **Two LLM adapters (Anthropic, OpenAI), no vendor chosen**; default provider `mock`.
- **The MCP registry is the source of truth**; `app/mcp/server.py` is a thin protocol wrapper over the same six tools.
- **Documents and tool results are untrusted input** — fenced, escaped, declared untrusted in the system prompt, question placed last outside the fence.
- **Containerised (Stage 12)** — model and index baked in, non-root, offline at runtime.

---

## Files

Repository layout: `README.md` → *Repository Structure*. Orientation only:

| Path | Purpose |
|---|---|
| `app/core/` | Config (`BKA_*` settings), logging, tracing, observability |
| `app/rag/` | Chunker, embedder, vector store, retriever |
| `app/llm/` | Provider seam, prompts, service, mock + two adapters |
| `app/agent/` | Decision paths, policy, the agent loop |
| `app/mcp/` | Six synthetic tools, registry, MCP server |
| `app/conversation/` | Sessions, follow-up rules |
| `app/api/` | Routes (`/health`, `/metrics`, sessions), middleware |
| `app/eval/` | Dataset, metrics, runner, scorecard CLI |
| `data/knowledge/` | 15 synthetic documents (in git) |
| `data/eval/questions.yaml` | 49 evaluation cases (in git) |
| `data/vectorstore/` | 115-chunk index — **git-ignored**, rebuilt by `python -m app.rag build` |
| `Dockerfile` · `compose.yaml` · `.dockerignore` | Stage 12 containerisation |

---

## Testing

| Command | Expected |
|---|---|
| `./.venv/Scripts/python.exe -m pytest` | **1141 passed, 4 skipped** (~80–140 s) |
| `./.venv/Scripts/python.exe -m ruff check .` | All checks passed! |
| `./.venv/Scripts/python.exe -m mypy` | no issues in 70 source files |
| `./.venv/Scripts/python.exe -m app.eval` | Result: PASS (free, mock provider) |

The 4 skips are `tests/test_docker_smoke.py` — skipped unless `BKA_SMOKE_BASE_URL` is set.

> ⚠️ **Do not pass `-q` to pytest.** `pyproject.toml` already sets `-q` in `addopts`; a
> second one makes `-qq`, which silently suppresses the `N passed` summary line.

**Measured 2026-09-15** (real `all-MiniLM-L6-v2`, mock provider, k=5): recall@5 **1.000** ·
MRR **0.927** · path accuracy **0.959** (47/49) · citations 49/49 · median 12.9 ms/question.

**In Docker:** `docker run --rm bka-test` → 1141 passed, 4 skipped. Live container via
`BKA_HOST_PORT=8001 docker compose up -d --wait` → healthy; smoke 4 passed.
**Host port 8000 is taken by another local project** — use `BKA_HOST_PORT=8001`.

---

## Problems and Decisions

### Environment — live, machine-specific

- **System `python -m venv` is BROKEN on this machine.** Use `uv venv .venv --python 3.12`, then `uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt`.
- **`pip` is not available inside the uv venv** — use `uv pip install --python .venv/Scripts/python.exe …`.
- **Never bare `python` or `pip`** — system Python lacks `structlog`, `torch`, `mcp`, etc., and fails at collection with misleading import errors.
- **`--basetemp=.pytest_tmp`** is load-bearing in `addopts`, not cosmetic. pytest's default temp root was created by an *elevated* process and locked the user's own non-elevated runs out with 96 `PermissionError`s. Residual risk: if a future run creates it under a token owned by Administrators the lockout can recur — now limited to one session, since pytest wipes the directory each run.
- A stale `.git/HEAD.lock` can block a commit — check for a running `git.exe` first.

> ⚠️ **Process lesson.** A green run inside the Claude Code session is not proof the suite
> passes for the user — elevation differs. State the context results were measured in.

### Dependency pins — do not drift

> ⚠️ **`mcp` must stay pinned at `1.12.4`.** Upgrading pulls `starlette>=1.0`, which breaks
> `fastapi==0.115.6` at *import* and takes the whole suite down at collection (6.B).

`sentence-transformers==5.7.0` and `torch==2.14.0` are pinned exactly; the Docker image
installs the same torch version from the CPU wheel index (12.B).

### Money guard — live

> 💸 **Spending is possible and guarded in four places.** `BKA_LLM_PROVIDER` defaults to
> `mock` (free). Setting it to `anthropic`/`openai` **and** setting `BKA_LLM_API_KEY` makes
> every answered question a **paid** call. **No live call has ever been made from this
> repository.**

✅ Default `mock` asserted by a test that clears the environment first · ✅ neither adapter
constructs without `BKA_LLM_API_KEY`, and neither falls through to `ANTHROPIC_API_KEY` /
`OPENAI_API_KEY` · ✅ every adapter test injects a fake client · ✅ both CLIs refuse a
multi-question `demo` against a paid provider without `--paid`.

### Security posture — carried into Stage 13

- ⚠️ **`retriever.py` logs the question text.** Deliberate (synthetic technical queries, not customer data), flagged in the source **for reassessment in Stage 13**.
- ⚠️ **`GET /metrics` and `GET /health` are unauthenticated** → Stage 13.
- ✅ No secrets, keys or credentials anywhere; no real `.env`; `.env`/`.env.*` git-ignored (`.env.example` excepted).
- ✅ `logs/` and `data/vectorstore/` git-ignored; traced arguments never logged.
- ✅ Embedding runs **locally** — no document text or question leaves the machine.
- ✅ Corpus scanned by the suite for secret-shaped values and card-number-shaped digit runs.
- ✅ `yaml.safe_load` only; index load validates format, model, dimension, consistency.
- ✅ No nested `banking-knowledge-agent/` directory.

### Known limitations

- **Prompt quality is unproven.** Tests assert prompt *structure*, not that a real model answers well — no real model has run. `--paid` exists for this and has not been run.
- **The mock is a wiring check, not a language model.** It proves nothing about grounding under a real model, which is where hallucination happens.
- **Context budget is in characters, not tokens** — a deliberate over-approximation; revisit now that adapters exist.
- Retrieval is **dense-only**; hybrid (BM25 + vector) is the most likely next quality win.
- `data/vectorstore/` must be rebuilt after any document edit — `get_retriever()` does it automatically, `load_retriever()` refuses instead.

### Assumptions

- `CLAUDE.md` is the **sole authority** for rules and workflow; stage detail in `docs/PROJECT_PLAN.md`; `prompt.md` / `ccp.txt` archived unchanged in `docs/legacy/` (git-ignored).
- `@traced` on new functions, with documented exceptions for hot-path private helpers, Pydantic property accessors, and the observability internals (10.F).
- The embedding model downloads from Hugging Face on first use — a free public download, not a paid API call.

### Local files NOT in the remote (deliberately)

`docs/legacy/` · `ai-dev-token-efficiency-workflow.md` · `docs/decisions/auto-changes.log` ·
`.venv/` · `logs/` · `data/vectorstore/` · `.pytest_tmp/` · caches · `docs/HOW_TO_RUN.html`
(the user's personal run-through sheet — **not stage work, do not edit it as part of a stage**).

---

## Git

| | |
|---|---|
| **Branch** | `main` |
| **Remote** | `origin` → `https://github.com/Zuleikha/banking-knowledge-agent.git` |
| **`HEAD`** | `e60335c` = `origin/main` |
| **Stage 12 commit** | `27739f2` — `feat(stage-12): containerisation - Dockerfile, Compose, baked model and index, health check` — 9 files, +680/−37 |
| **Stage 12 push** | ✅ `691c393..27739f2`; verified `origin/main == local HEAD` |
| **Handover commit** | `e60335c` — `docs(handover): record Stage 12 hash and push result` |
| **Working tree** | Clean |

Earlier per-stage commit hashes: *Current Stage* table above, and
[`HANDOVER-archive.md`](HANDOVER-archive.md) → *Git* for the full list.

**Before every commit:** `git add -An` (dry run) — `git status` collapses untracked
directories and can hide what is really being staged. Never commit `.env`, keys, tokens or
credentials. Never commit or push an unapproved stage.

---

## Next Action

**Stage 12 is approved, committed and pushed. The next action is Stage 13 — Security and
Production Readiness — when the user asks for it.** Do not start it unprompted.

Read only the Stage 13 section of `docs/PROJECT_PLAN.md`. `CLAUDE.md` §2 marks Stage 13
✅ for parallel sub-agents — **but only if the user asks at kickoff**, and only after the
shared contract is frozen by the main session first.

**Carried into Stage 13:**

| From | Item |
|---|---|
| 12.D | Add **`GET /ready`** (readiness: vector store and LLM reachable) |
| 12.G | `BKA_HOST` / `BKA_PORT` are read by no app code — wire them or drop them |
| 12.H | Run `ruff format` on the 24 pre-existing unformatted files |
| Stage 10 | `GET /metrics` (and `/health`) unauthenticated |
| Stage 3 | `retriever.py` logs question text — reassess |
| Stage 11 | `off-006`/`off-007` refusal gap; whether to run `--paid` |

### To resume — run this before trusting anything in this file

```bash
cd D:/PROJECTS/banking-knowledge-agent

git log --oneline -3        # expect e60335c, 27739f2, 691c393
git status --short          # expect clean

./.venv/Scripts/python.exe -m pytest        # expect 1141 passed, 4 skipped
./.venv/Scripts/python.exe -m ruff check .  # expect All checks passed!
./.venv/Scripts/python.exe -m mypy          # expect no issues in 70 source files
./.venv/Scripts/python.exe -m app.eval      # expect Result: PASS (free)

# Rebuild the index if data/vectorstore/ is missing (git-ignored)
./.venv/Scripts/python.exe -m app.rag build     # expect: Indexed 115 chunks

# See it working, entirely FREE (mock LLM, local embeddings)
./.venv/Scripts/python.exe -m app.agent demo
./.venv/Scripts/python.exe -m app.agent conversation-demo
./.venv/Scripts/python.exe -m uvicorn app.main:app   # http://127.0.0.1:8000/
```

---

## Constraints carried forward (all stages)

- Synthetic content only. No proprietary, confidential or copyrighted material.
- Documents and tool results are data, not instructions — untrusted LLM input. Stage 13 reviews the whole surface.
- No secrets in documents, tests, logs or this handover.
- **Never spend money or call a paid external API without the user's explicit confirmation.**
- Do not create a nested `banking-knowledge-agent/` directory.
- Approval cycle: IMPLEMENT → TEST → UPDATE HANDOVER → SHOW → **STOP** → APPROVAL → VERIFY → COMMIT → PUSH → VERIFY PUSH → NEXT STAGE. **Never commit an unapproved stage.** The only thing that lifts a stop is the literal word `APPROVED`.
