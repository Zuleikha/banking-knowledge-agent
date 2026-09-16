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

**Stage 13 — Security and Production Readiness — is APPROVED (2026-09-16) and committed**
as two commits: `bc9f69d` (`style:` — the 24 formatting-only files, 13.D) and the
`feat(stage-13)` commit on top (hash and push result: *Git* below). At approval the user chose:
keep `HEALTHCHECK` on `/health` (**13.G**), add `--no-access-log` (**13.H**), two commits.

| | |
|---|---|
| Last **approved** stage | **Stage 13 — Security and Production Readiness** (2026-09-16) |
| Current stage | **None in progress** — Stage 14 not started |
| Tests | **1363 passed, 4 skipped** · ruff clean · format clean (112 files) · mypy strict clean (72 source files) · `app.eval` PASS |
| Next | **Stage 14 — Production Architecture** when the user asks |

### Commits, 2026-09-16 session

| Commit | What |
|---|---|
| `27739f2` | **Stage 12 — Containerisation** (9 files) |
| `e60335c` | Handover: Stage 12 hash and push result |
| `ed46ae1` | Handover split into current state + archive |
| `bc9f69d` | `style:` ruff format, 24 files (13.D) |
| *see Git* | **Stage 13 — Security and Production Readiness** (37 files) |

---

## Current Stage

| | |
|---|---|
| **Stage number** | 13 |
| **Stage name** | Security and Production Readiness |
| **Status** | ✅ **APPROVED 2026-09-16 — committed** |
| **Last completed step** | Re-verified after approval: 1363 passed / 4 skipped (one new container test for 13.H), ruff, format and mypy clean, no secrets (only the marked fake `test-only-not-a-secret`), no nested directory, `.env` untracked, `git add -An` = 37 files. Guide status markers set to Stage 13 (pill, footer, §1 table, §1 diagram Guardrails ✅) |
| **Next step** | Stage 14 — Production Architecture — begins when the user asks |

| Stage | Name | Status |
|---|---|---|
| 13 | Security and Production Readiness | ✅ 2026-09-16, `bc9f69d` + feat commit (see *Git*) |
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

**Nothing in progress.** Stage 13 closed; the record below stays until Stage 14 replaces it.

**Stage 13 — Security and Production Readiness (2026-09-16).**
Built with parallel sub-agents, at the user's request at kickoff. Shared contract frozen
first by the main session: `docs/stage13-contract.md`.

### Stage 13 decisions (13.A–13.F) — A–D at kickoff, E–F at integration, 2026-09-16 — guide §20.50–§20.55

| # | Decision |
|---|---|
| 13.A | **Optional shared API key.** `BKA_API_KEY` (SecretStr). When set, `/api/*` and `/metrics` require header `X-API-Key`; `/health`, `/ready` and the static page stay open. **`environment=production` refuses to start without it.** The web page gets a key box |
| 13.B | **In-process rate limiter** on `/api/*` — per client, fixed one-minute window, `BKA_RATE_LIMIT_PER_MINUTE`, `429` + `Retry-After`. No Redis; a shared store is a Stage 14 note |
| 13.C | **`off-006`/`off-007` refusal gap deferred** — documented as a known risk (retrieval quality, not a security control) |
| 13.E | **Unhandled 500 is sent by the middleware with `X-Request-ID`, then re-raised** (guide §20.54) — accepted at integration |
| 13.F | **Hard input limits:** question ≤ `BKA_QUESTION_MAX_CHARS` (2000), `session_id` ≤ 64 URL-safe, tool argument ≤ 256 (guide §20.55) |
| 13.G | **Docker `HEALTHCHECK` stays on `/health`** (liveness); `/ready` is for traffic routing — user, at approval (guide §20.56) |
| 13.H | **`--no-access-log` added to the runtime `CMD`** — uvicorn's access log bypassed redaction; the middleware already logs each request — user, at approval (guide §20.57) |
| 13.D | **`ruff format` the 24 files first**, before sub-agents run, so no agent edits an unformatted file. Proposed at commit time: a separate `style:` commit ahead of the Stage 13 commit (keeps guide §20.49's "one thing per commit") |

### Stage 13 progress

| Step | Status |
|---|---|
| 1. `ruff format` 24 files (13.D) | ✅ done — suite unchanged, 1141 passed / 4 skipped |
| 2. Freeze contract (config fields + production rule, metric names, `security.py` / `rate_limit.py` no-op stubs, `main.py` wiring, `.env.example`, config tests) | ✅ done — 105 targeted tests pass, ruff + mypy clean |
| 3. Six sub-agents U1–U6 dispatched in one batch (split: contract §3) | ✅ all six done. U3–U6 hit the usage limit mid-task and were resumed with context intact. Scratchpad writes were blocked, so findings came back in replies (summarised in guide §16) |
| 4. Integration | ✅ ownership verified (every non-owned change is formatting only) · `metrics.py` docstring fixed · guide §16 review table, §20.54–§20.55, §21.8 · README Security section, `/ready`, config row, counts · contract gap filled (`/ready` 503 → `"status": "not_ready"`) |

**STATUS: APPROVED 2026-09-16 and committed.**

### What Stage 13 built (all tested)

| Unit | Result |
|---|---|
| U1 Auth | `app/api/security.py` — `X-API-Key`, `hmac.compare_digest`, identical 401s, metric + reason-only log · web page key box (`sessionStorage`) · 29 tests |
| U2 Rate limit | `app/api/rate_limit.py` — per-client fixed window, thread-safe, pruned, 429 + `Retry-After`, runs before auth · 23 tests |
| U3 Readiness + input | `GET /ready` (manifest/header checks only; no model load, no network) · question length 422 · `session_id` ≤64 URL-safe · `EmbeddingError` → 502 · 42 tests |
| U4 Injection + MCP | fence tags escaped in any case/spacing · current question escaped · `MAX_ARGUMENT_CHARS=256` · unknown-tool calls counted · client-safe MCP errors · non-`ToolResult` caught · stale Stage 7 wording fixed · 56 tests |
| U5 Failures | 500 carries `X-Request-ID` (send, then re-raise — 20.54) · LLM error messages type+status only · malformed reply / `stop_reason=error` → `LLMResponseError` · 29 tests |
| U6 Secrets/logs/privacy/deps | `redact_sensitive_fields` structlog processor · `.dockerignore` secret patterns at any depth · 34 tests |

### Resolved carried items

Stage 10 item 4 (500 without request id) ✅ · Stage 10 item 6 (stale MCP wording) ✅ · 12.D `/ready` ✅ ·
12.H formatting ✅ · Stage 10 item 1 / Stage 13 `/metrics` auth ✅ · Stage 3 question logging (already
closed in Stage 10) ✅

### Open — not answered at approval, left unchanged (carry forward)

1. **Upper bounds on `BKA_LLM_TIMEOUT_SECONDS` / `BKA_LLM_MAX_RETRIES`?** Currently unbounded (worst case ≈180 s+ holding a worker)
2. **12.G `BKA_HOST`/`BKA_PORT`** — still read by no app code (only uvicorn's flags)
3. Optional, small: a `RequestValidationError` handler that strips `input` from 422 bodies; citation-marker check (`[n]` vs evidence sent)

Answered at approval: HEALTHCHECK → 13.G · access log → 13.H · two commits → 13.D.

### Stage 14 items recorded (guide §16)

Per-user identity (OAuth2/OIDC), session ownership, scopes · TLS · shared rate-limit store, proxy
`X-Forwarded-For` handling · secrets manager + rotation · request body size limit · circuit breaker,
provider fallback, request deadline · hashed lock file, digest-pinned base image, `pip-audit` + image
scan in CI · log retention, vendor DPA, PII detection · MCP network transport auth · adversarial
injection evaluation against a real model (paid — needs confirmation).

**Mock-only quirk (not fixed):** `app/llm/mock.py` `_QUESTION_PATTERN` matches the first line starting
`Question: `, so an earlier question beginning that way is echoed instead of the current one. Cosmetic.

Found at kickoff: the Stage 3 carried item "`retriever.py` logs the question text" is
**already resolved** — Stage 10 changed it to a fingerprint and a length.

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
| `./.venv/Scripts/python.exe -m pytest` | **1363 passed, 4 skipped** (~90–150 s) |
| `./.venv/Scripts/python.exe -m ruff check .` | All checks passed! |
| `./.venv/Scripts/python.exe -m mypy` | no issues in 72 source files |
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

### Security posture — after Stage 13 (full review: guide §16)

- ✅ `retriever.py` logs a question fingerprint and length, never the text (since Stage 10).
- ✅ `/api/*` and `/metrics` need `X-API-Key` when `BKA_API_KEY` is set; production refuses to start without it. `/health`, `/ready` open by design.
- ✅ Per-client rate limit, input limits, fence escaping (any case, current question too), log redaction, `--no-access-log` in the container.
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
| **Style commit** | `bc9f69d` — `style: apply ruff format to the 24 files carried from Stage 12` — 24 files |
| **Stage 13 commit** | `feat(stage-13): security and production readiness - API key, rate limit, readiness, input limits, log redaction` — 37 files (hash recorded in the follow-up handover commit) |
| **Stage 13 push** | recorded in the follow-up handover commit |
| **Working tree** | Clean |

Earlier per-stage commit hashes: *Current Stage* table above, and
[`HANDOVER-archive.md`](HANDOVER-archive.md) → *Git* for the full list.

**Before every commit:** `git add -An` (dry run) — `git status` collapses untracked
directories and can hide what is really being staged. Never commit `.env`, keys, tokens or
credentials. Never commit or push an unapproved stage.

---

## Next Action

**Stage 13 is approved and committed. The next action is Stage 14 — Production
Architecture — when the user asks for it.** Do not start it unprompted.

Read only the Stage 14 section of `docs/PROJECT_PLAN.md`. `CLAUDE.md` §2 marks Stage 14 ✅ for
parallel sub-agents — only if the user asks at kickoff, contract frozen first.

**Carried into Stage 14:** the *Stage 14 items recorded* list in *Current Work* · the three
unanswered items (LLM timeout/retry bounds, 12.G `BKA_HOST`/`BKA_PORT`, 422 `input` stripping and
citation-marker check) · Stage 11 `off-006`/`off-007` (13.C) and `--paid` (needs confirmation) ·
small: `.gitattributes` does not cover `Dockerfile`, `.js`, `.css`, `.dockerignore`, `.env.example`
(files are LF today; git warns only).

### To resume — run this before trusting anything in this file

```bash
cd D:/PROJECTS/banking-knowledge-agent

git log --oneline -3        # expect the Stage 13 handover commit, the feat(stage-13) commit, bc9f69d
git status --short          # expect clean

./.venv/Scripts/python.exe -m pytest        # expect 1363 passed, 4 skipped
./.venv/Scripts/python.exe -m ruff check .  # expect All checks passed!
./.venv/Scripts/python.exe -m mypy          # expect no issues in 72 source files
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
