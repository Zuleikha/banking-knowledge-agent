# HANDOVER — Banking Knowledge Agent
A decision is not recorded until it is written into docs/HANDOVER.md.
Do not let a decision live only in conversation history. 
If a decision is made mid-stage, before implementation begins, 
update HANDOVER.md immediately, not at stage completion.
> **Read this first in any new Claude Code session.**
> This file, not conversation history, is the record of project progress.
> Never assume a previous session completed work unless the repository confirms it.

Last updated: **2026-09-09** · Stage 3 approved, committed and pushed ·
Stage 4 **in progress** (LLM provider decision recorded — mock only, no concrete provider).

---

## ⏱️ SESSION CHECKPOINT — start here

**Session state:** Stage 4 approved by the user, committed and pushed.
**Nothing is in progress.** No half-finished work, no blockers.

### State at checkpoint

| | |
|---|---|
| Last **approved** stage | **Stage 4 — LLM Abstraction** (approved 2026-09-09) |
| `HEAD` | the `docs(stage-4)` commit sitting on top of `bee4b22` (= `origin/main`) |
| Working tree | Clean, apart from git-ignored local files |
| Tests | **385 passed** · ruff clean · mypy strict clean (29 source files) |
| Next stage | **Stage 5 — Knowledge Agent** (not started) |

> ⚠️ **One decision is open and blocks Stage 5:** which concrete LLM provider the first
> adapter targets, and whether a live API key is ever wired in. See *Next Action*.

### To resume

```bash
cd D:/PROJECTS/banking-knowledge-agent

# 1. Confirm the state matches this file before trusting it
git log --oneline -3          # expect docs(stage-4) on top of bee4b22
git status                    # expect clean

# 2. Re-establish the baseline
./.venv/Scripts/python.exe -m pytest        # expect 385 passed
./.venv/Scripts/python.exe -m ruff check .  # expect All checks passed!
./.venv/Scripts/python.exe -m mypy          # expect Success: no issues found in 29 source files

# 3. Rebuild the vector index if data/vectorstore/ is missing (it is git-ignored)
./.venv/Scripts/python.exe -m app.rag build     # expect: Indexed 115 chunks

# 4. See Stage 4 working, entirely offline
./.venv/Scripts/python.exe -m app.llm demo      # 5 grounded answers + 1 refusal
./.venv/Scripts/python.exe -m app.llm prompt "What component handles card authentication?"

# 5. Then read "Next Action" at the bottom of this file.
```

> ⚠️ **If the venv is missing**, recreate it — system `python -m venv` is BROKEN on this
> machine (Problems §4):
> ```
> uv venv .venv --python 3.12
> uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
> ```
> This now installs PyTorch (~250 MB). The first `app.rag build` also downloads the
> ~90 MB embedding model from Hugging Face and needs network access; later runs use the
> local cache.

### Local files that are NOT in the remote (deliberately)

`prompt.md` · `ccp.txt` · `docs/decisions/auto-changes.log` · `.venv/` · `logs/` ·
`data/vectorstore/` · caches.

---

## Current Stage

| | |
|---|---|
| **Stage number** | 4 |
| **Stage name** | LLM Abstraction |
| **Status** | ✅ **COMPLETE AND APPROVED BY THE USER — committed and pushed** |
| **Last completed step** | Stage 4 approved 2026-09-09; committed `bee4b22` and pushed to `origin/main` |
| **Next step** | **Begin Stage 5 — Knowledge Agent.** First settle the open decision: which concrete LLM provider, and whether a live key is wired in |

> ⛔ Stage 5 must STOP after implementation and testing, and wait for explicit approval
> before any commit or push.

### Previous stages

| Stage | Name | Status |
|---|---|---|
| 1 | Project Foundation | ✅ Approved 2026-09-03, committed `d448cc1`, pushed |
| 2 | Domain Knowledge | ✅ Approved 2026-09-08, committed `cca70af`, pushed |
| 3 | RAG Pipeline | ✅ Approved 2026-09-09, committed `be9297c`, pushed |
| 4 | LLM Abstraction | ✅ Approved 2026-09-09, committed `bee4b22`, pushed |

---

## Current Work

### Implemented in Stage 4 (this session)

- **`LLMProvider` protocol** — `app/llm/base.py`. The vendor-agnostic seam, plus the
  six-type error taxonomy (`LLMConfigurationError`, `LLMTimeoutError`,
  `LLMRateLimitError`, `LLMResponseError`, `LLMRefusalError`, `LLMProviderError`), each
  carrying a `retryable` flag. A protocol, not an ABC, so an implementation qualifies
  structurally — the same choice as `Embedder` and `VectorStore` in Stage 3.
- **Prompt management** — `app/llm/prompts.py`. `SYSTEM_PROMPT_VERSION = "1.0.0"`, one
  frozen system prompt recorded on every answer. Grounding rules, mandatory citations,
  the exact refusal sentence, and an explicit statement that fenced text is untrusted.
- **Context injection** — `select_context` (budget) → `render_context` (fence + number +
  label) → `build_user_turn` (context first, question last) → `build_request`.
- **Injection defence** — passages are fenced in `<retrieved_documentation>`, and any
  occurrence of the delimiters *inside* a passage's own text is escaped, so a document
  cannot close the fence early. Without that step the fence would be decorative.
- **Response generation and error handling** — `app/llm/service.py`. Truncated, refused
  and empty generations **raise** rather than being returned as answers; an untyped
  provider exception is wrapped in `LLMProviderError` with the cause preserved.
- **The refusal guard** — when retrieval is empty, the service returns the fixed
  insufficient-evidence sentence and **does not call the provider at all**.
- **Mock provider** — `app/llm/mock.py`. Deterministic and in-process, with three modes
  (synthesise from the injected passages / scripted responses / a handler that may
  raise), and it records every request for assertion.
- **Configuration** — 7 new `BKA_LLM_*` settings, documented in `.env.example`. The API
  key is a `SecretStr`, environment-only, unset.
- **Factory** — `app/llm/factory.py`. An unavailable provider raises; it never falls
  back to the mock.
- **CLI** — `python -m app.llm prompt | ask | demo`.
- **Tests** — 145 new tests across 3 files (240 → **385**).
- **Docs** — architecture guide §20.4 (nine decision records in the Stage 3 form), §9
  rewritten, plus §2, §4, §5, §12, §14, §16, §18, §19 and the stage table. README
  updated with a new "LLM abstraction" section.

### Implemented in Stage 3

- **Chunking** — `app/rag/chunker.py`. Splits on Markdown `##` headings, budgeting size
  in the *embedding model's own tokens*. Oversized sections split at paragraph or
  table-row boundaries; a split table repeats its header row. Code fences are not
  mistaken for headings. Result: 15 documents → 108 sections → **115 chunks**, max 251
  of a 256-token window, zero over.
- **Metadata handling** — every `Chunk` carries the complete `DocumentMetadata` of its
  source plus `source_path`, so retrieval can cite and filter.
- **Embedding generation** — `app/rag/embeddings.py`. `Embedder` protocol with two
  implementations: `SentenceTransformerEmbedder` (all-MiniLM-L6-v2, local, lazy-loaded,
  384-dim) and `HashingEmbedder` (deterministic, offline, for fast tests).
- **Vector storage** — `app/rag/vectorstore.py`. `VectorStore` protocol +
  `InMemoryVectorStore`: exact cosine search over one NumPy matrix, persisted as
  `vectors.npy` + `chunks.json` + `manifest.json`.
- **Retrieval and similarity search** — `app/rag/retriever.py`. Question → embed →
  optional metadata pre-filter → top-k cosine → score floor → `RetrievalResult`.
- **Source metadata** — `RetrievalResult.sources`, deduplicated by document.
- **Pipeline + freshness** — `app/rag/pipeline.py`. `build_index`, `load_retriever`,
  `get_retriever`, and a SHA-256 corpus fingerprint so a stale index is refused.
- **CLI** — `app/rag/__main__.py`: `build`, `search`, `demo`, `calibrate`.
- **Configuration** — 8 new `BKA_*` settings, documented in `.env.example`.
- **Tests** — 168 new tests across 5 files (72 → **240**).
- **Docs** — `docs/architecture-guide.html` substantially rewritten, including a new
  **§20 Decision records** section carrying the full reasoning for every Stage 3 choice
  (what was chosen, why, what was rejected and why). `README.md` updated.

### Currently being worked on

Nothing is in progress. Stage 4 is complete, tested and documented, and is waiting for
the user's approval before any commit.

### What remains unfinished in Stage 4

Nothing that Stage 4's scope requires. Two things are **deliberately** absent and are
recorded as deferred, not missed:

1. **A concrete provider adapter** — deferred to a decision before Stage 5, by the
   user's instruction. See the decision record in *Next Action*.
2. **Prompt quality evidence** — the prompt is tested for *structure* (what is sent,
   what is not, what is escaped) but not for *answer quality*, because no real model has
   run against it. That measurement is Stage 11's evaluation set.

### Not yet implemented (later stages)

Concrete LLM provider (5) · Knowledge agent (5) · MCP tools (6) · Tool selection (7) ·
Conversation context (8) · Web interface (9) · Request observability (10) ·
Evaluation framework (11) · Docker (12) · Security review (13) ·
Production architecture (14) · Final review (15)

---

## Architecture

### Current

```
INDEXING (offline build step — python -m app.rag build)

data/knowledge/**/*.md                              15 documents
   │
   ▼  loader (Stage 2) — front matter → validated metadata
KnowledgeDocument(metadata, content, source_path)
   │
   ▼  chunker — split on ##; budget = embedder.max_tokens
   │            oversized sections split; tables keep their header
   │            each chunk prefixed "Title — Heading" for embedding
Chunk × 115                                         max 251 / 256 tokens
   │
   ▼  embed_chunks — one batched call, L2-normalised
EmbeddedChunk × 115                                 (115, 384) float32
   │
   ▼  InMemoryVectorStore.save()
data/vectorstore/  vectors.npy · chunks.json · manifest.json
                   manifest pins model id + dimension + corpus fingerprint

RETRIEVAL (per question — no LLM involved)

Question
   │
   ▼  embedder.embed_query          SAME model as indexing (manifest-enforced)
Query vector (384,)
   │
   ▼  metadata pre-filter (optional)   domain / component / doc_type / version
   ▼  cosine = matrix @ query          one BLAS matvec
   ▼  top-k via argpartition
   ▼  min_score floor ── below ──▶ EMPTY RESULT → agent must refuse (Stage 5)
RetrievalResult(chunks, sources, candidates_considered, min_score, top_score)
   │
   └──▶ logs/app.log  "rag.retrieved"

GENERATION (Stage 4 — per question, no vendor involved)

RetrievalResult
   │
   ▼  select_context      max 5 passages / 12,000 chars; dropped WHOLE, never cut
   │                      EMPTY ──▶ refuse with the fixed sentence, NO provider call
   ▼  build_request       frozen system prompt v1.0.0
   │                      + <retrieved_documentation> fenced, numbered, escaped
   │                      + the question, last and outside the fence
CompletionRequest         system · messages · max_tokens      (no sampling params)
   │
   ▼  LLMProvider.complete()          ← the seam; no vendor above this line
   │        └── MockLLMProvider       deterministic, in-process, free
LLMResponse               text · stop_reason · usage · provider/model id
   │
   ▼  validate            refusal / max_tokens / empty  ──▶ RAISE, never shown
GroundedAnswer            text + sources + chunks_used + llm_called + prompt_version
   │
   └──▶ logs/app.log  "llm.answered"   shape and cost only — never the prompt or
                                       the answer, both of which embed document text

HTTP (unchanged from Stage 1 — not yet wired to retrieval or generation; that is
Stage 5)
GET /health → FastAPI router → HealthResponse
```

### Components implemented

| Component | Responsibility |
|---|---|
| `app/main.py` | App factory, router mounting, lifespan logging |
| `app/core/config.py` | Typed, frozen, env-based `Settings`; cached `get_settings()` |
| `app/core/logging.py` | structlog + stdlib bridge; app sink and separate trace sink |
| `app/core/tracing.py` | `@traced` / `@traced_async` structured trace decorators |
| `app/api/dependencies.py` | `SettingsDep` — resolves settings from `app.state` |
| `app/api/routes/health.py` | `GET /health` liveness endpoint |
| `app/knowledge/models.py` | `DocumentMetadata`, `KnowledgeDocument`, `Domain`, `DocType` |
| `app/knowledge/loader.py` | Front-matter parsing, validation, corpus loading |
| `app/rag/models.py` | `Chunk`, `EmbeddedChunk`, `ScoredChunk`, `RetrievalResult` |
| `app/rag/chunker.py` | `split_sections`, `chunk_document`, `chunk_documents` |
| `app/rag/embeddings.py` | `Embedder` protocol, sentence-transformers + hashing impls |
| `app/rag/vectorstore.py` | `VectorStore` protocol, `InMemoryVectorStore`, persistence |
| `app/rag/retriever.py` | `Retriever.retrieve` / `retrieve_many` |
| `app/rag/pipeline.py` | `build_index`, `load_retriever`, `get_retriever`, fingerprint |
| `app/rag/__main__.py` | CLI: build / search / demo / calibrate |
| `app/llm/models.py` | `CompletionRequest`, `LLMResponse`, `TokenUsage`, `GroundedAnswer` |
| `app/llm/base.py` | `LLMProvider` protocol + the six-type error taxonomy |
| `app/llm/prompts.py` | Versioned instructions, context budget, fencing and escaping |
| `app/llm/mock.py` | `MockLLMProvider` — the only provider that ships |
| `app/llm/service.py` | `LLMService.answer` — inject, generate, validate, attribute |
| `app/llm/factory.py` | `get_provider`, `get_llm_service` — configuration → provider |
| `app/llm/__main__.py` | CLI: prompt / ask / demo |

### Important design decisions (Stage 4)

Summary only — the **full reasoning, with rejected alternatives, is in
`docs/architecture-guide.html` §20.4**, which is the authoritative record.

| Decision | Reasoning (short) |
|---|---|
| **No concrete provider in Stage 4** (4.1) | An abstraction is proved by what it is independent of. Everything the stage must show is exercisable without a vendor — and it makes the no-paid-call property *structural*: no code path calls anything |
| **An unavailable provider raises** (4.2) | The alternative failure — an app that starts, answers, and looks healthy while running a stub — is the one nobody notices |
| **Passages fenced, escaped, declared untrusted** (4.3) | Without the escaping step the fence is theatre: a document containing the closing tag would break out of it. Written while the corpus is synthetic and the risk is nil, because the day a real document arrives the architecture must already be right |
| **No evidence → no model call** (4.4) | A generation with zero context can only refuse or invent. Removing the request removes the only path to an ungrounded answer — and is free, fast and deterministic |
| **Truncated / refused generations raise** (4.5) | A cut-off answer about a transaction limit reads as complete. An error is loud and recoverable; a plausible half-sentence is neither |
| **Error taxonomy at the seam, not in adapters** (4.6) | Callers need one distinction — retry or broken. Vendor hierarchies leaking upward would put an SDK's name in every call site |
| **Passages dropped whole, never truncated** (4.7) | Half a configuration table reads as complete and is wrong. A single oversized passage is always kept, so a budget can never turn a valid answer into a refusal |
| **`SecretStr` API key, provider-neutral name** (4.8) | "Never log secrets" enforced by the type, not by memory — and asserted in the suite. No fall-through to an SDK's ambient variable, which would turn a config mistake into a silent paid call |
| **No sampling params; messages already a tuple** (4.9) | Opposite calls, deliberately: sampling is omitted (several current models reject it, and faithfulness beats variety here) while the message tuple is paid for now so Stage 8 appends rather than reshapes every call site |

### Important design decisions (Stage 3)

Summary only — the **full reasoning, with rejected alternatives, is in
`docs/architecture-guide.html` §20**, which is the authoritative record.

| Decision | Reasoning (short) |
|---|---|
| **Local `all-MiniLM-L6-v2`** over a hosted embedding API | Free, offline, no key, no data leaves the machine. A hosted API is a paid per-query call and needs explicit sign-off |
| **Embeddings over lexical TF-IDF** | Paraphrase: *"money left the account but no cash came out"* must find *"Troubleshooting a Failed Cash Withdrawal"*. Lexical cannot |
| **Split on `##` headings** | The author already marked where topics change. Measured: 108 sections, 32–411 tokens, median 99 — already chunk-sized |
| **Budget in the model's tokens, never words** | Measured 1.13–2.82 tokens/word; one 146-word section = 411 tokens. MiniLM truncates **silently** at 256, so a word budget would have amputated the densest sections invisibly |
| **Tables split row-wise, header repeated** | 6 sections exceed the window, mostly config-key/error-code tables. A table fragment without its header is unreadable |
| **`embedding_text` ≠ `content`** | A chunk about reversals never says "ATM". A `"Title — Heading"` prefix restores the entity names without polluting the cited text |
| **Brute-force NumPy, not FAISS/Chroma** | 115×384 is one BLAS matvec. ANN trades recall for scaling that is not needed. The protocol makes it replaceable |
| **Cosine via normalised dot product** | MiniLM is trained with a cosine objective — the metric the space was built for, not merely convenient |
| **Pre-filter, not post-filter** | Post-filtering top-k can return zero results despite ample matching material |
| **min_score = 0.25, calibrated** | Measured: on-topic min 0.388, off-topic max 0.122, midpoint 0.255. Without a floor, an off-topic question still yields five banking passages |
| **Index is an offline build artefact** | Startup stays fast, replicas share one index, and a document edit is not invisible until restart. Git-ignored: it is derived, not source |
| **Manifest pins model + fingerprint** | Both failure modes are *silent* — a foreign model returns plausible nonsense; a stale index returns fluent, resolvable, outdated answers |
| **Two embedders behind one protocol** | Fast offline tests, and it *proves* the decoupling rather than claiming it. A mock would prove neither |

---

## Files

### Added in Stage 4 (11 files, uncommitted)

| File | Purpose |
|---|---|
| `app/llm/__init__.py` | Package exports and the layer overview docstring |
| `app/llm/models.py` | `CompletionRequest`, `LLMResponse`, `TokenUsage`, `GroundedAnswer` |
| `app/llm/base.py` | `LLMProvider` protocol; six-typed errors with `retryable` |
| `app/llm/prompts.py` | System instructions v1.0.0, budget, fencing, escaping |
| `app/llm/mock.py` | `MockLLMProvider` — synthesise / script / raise, records calls |
| `app/llm/service.py` | `LLMService.answer` — the orchestration |
| `app/llm/factory.py` | `get_provider`, `get_llm_service`, `AVAILABLE_PROVIDERS` |
| `app/llm/__main__.py` | CLI: prompt / ask / demo |
| `tests/test_llm_prompts.py` | 38 tests — instructions, budget, rendering, injection |
| `tests/test_llm_provider.py` | 61 tests — protocol, errors, mock, factory, no-network |
| `tests/test_llm_service.py` | 46 tests — injection, refusal, errors, provenance |

### Modified in Stage 4 (7 files, uncommitted)

| File | Change |
|---|---|
| `app/core/config.py` | 7 LLM settings; `SecretStr` import |
| `.gitignore` | `prompt1.md` added beside `prompt.md` — see the Git section |
| `.env.example` | New LLM section; the secrets section rewritten |
| `tests/conftest.py` | `llm_settings`, `mock_provider`, `llm_service`, `retrieval`, `empty_retrieval` |
| `README.md` | Status, layout, configuration table, new "LLM abstraction" section, test count |
| `docs/architecture-guide.html` | §9 rewritten; §20.4 added (9 records); §2, §4, §5, §12, §14, §16, §18, §19, stage table, header, footer |
| `docs/HANDOVER.md` | This file |

> `requirements.txt` is **unchanged** — Stage 4 added no dependency. That is a
> consequence of shipping no vendor adapter, and it is worth noticing.

### Added in Stage 3

| File | Purpose |
|---|---|
| `app/rag/__init__.py` | Package exports and the pipeline overview docstring |
| `app/rag/models.py` | `Chunk`, `EmbeddedChunk`, `ScoredChunk`, `RetrievalResult` |
| `app/rag/chunker.py` | Heading-aware, token-budgeted chunking; table splitting |
| `app/rag/embeddings.py` | `Embedder` protocol; sentence-transformers + hashing impls |
| `app/rag/vectorstore.py` | `VectorStore` protocol; NumPy store; persistence + guards |
| `app/rag/retriever.py` | `Retriever` — embed, filter, search, threshold |
| `app/rag/pipeline.py` | `build_index`, `load_retriever`, `get_retriever`, fingerprint |
| `app/rag/__main__.py` | CLI: build / search / demo / calibrate |
| `tests/test_chunker.py` | 36 tests — boundaries, tables, the no-truncation invariant |
| `tests/test_embeddings.py` | 19 tests — the `Embedder` protocol contract |
| `tests/test_vectorstore.py` | 37 tests — ranking, filtering, persistence, guards |
| `tests/test_retriever.py` | 43 tests — end-to-end, threshold, sources, staleness |
| `tests/test_rag_integration.py` | 33 tests — retrieval **quality** with the real model |

### Modified in Stage 3

| File | Change |
|---|---|
| `app/core/config.py` | 8 RAG settings: vectorstore dir, embedding model/device/batch, chunk max/overlap tokens, top-k, min score |
| `requirements.txt` | `sentence-transformers==5.7.0`, `torch==2.14.0`, `numpy==2.5.3` |
| `pyproject.toml` | Registered the `integration` pytest marker; added `--basetemp=.pytest_tmp` (Problems §15) |
| `.env.example` | Documented every new `BKA_*` variable |
| `tests/conftest.py` | Added `rag_settings`, `real_settings`, `corpus`, `retriever` fixtures |
| `README.md` | Status, stack, layout, configuration, new "RAG pipeline" section, test commands |
| `docs/architecture-guide.html` | §1 stages, §2 structure, §3 stack, §4 components, §5 data flow, §6 RAG flow (rewritten with measurements), §10 vector database (rewritten), §12 config, §14 testing, §16 security, §18 extension points, and **new §20 Decision records** |

### Unchanged from Stages 1–2

`app/main.py` · `app/core/logging.py` · `app/core/tracing.py` ·
`app/api/**` · `app/knowledge/**` · `data/knowledge/**` ·
`tests/test_config.py` · `tests/test_health.py` · `tests/test_logging.py` ·
`tests/test_loader.py` · `.gitignore`

---

## Testing

### Result (Stage 4)

**385 passed, 0 failed** (240 from Stages 1–3, **145 new**). Runtime ~36 s.
`ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 29 source files*

> ⚠️ **Context this was measured in** (Problems §15 lesson): run inside the Claude Code
> session, which is **elevated**. The `--basetemp=.pytest_tmp` fix means a non-elevated
> run should behave identically, but the user should confirm 385 passed in their own
> shell before approving.

| Stage 4 test file | Tests | Covers |
|---|---|---|
| `tests/test_llm_prompts.py` | 38 | System instructions (grounding, citations, the exact refusal sentence, no vendor or proprietary name in the text); context budget (chunk and char limits, order preserved, never truncated, always ≥1 passage); rendering and citation metadata; **injection defence** — attribute escaping and a passage containing the literal closing fence failing to escape it; and the central claim asserted against the real corpus — only selected passages reach the prompt, every other document is absent |
| `tests/test_llm_provider.py` | 61 | Protocol conformance including a structurally-typed implementation that inherits nothing; the full error taxonomy and its `retryable` flags; the mock's three modes and its call recording; the factory refusing an unavailable provider **without falling back**; configuration including a key that appears in neither a repr nor a dump; and an **AST walk over every module in `app/llm/`** asserting no vendor SDK, no HTTP client, no URL |
| `tests/test_llm_service.py` | 46 | What actually reaches the provider (versioned system prompt, question present once, passages fenced, knowledge base absent, budgets honoured); the refusal path making **zero** provider calls; error handling — timeout and rate limit propagate with retry hints, an untyped exception is wrapped with its cause preserved, refused/truncated/empty generations raise; the five seed questions end to end; and the Stage 4/5 boundary — the service does not retrieve |

### Commands used (Stage 4)

```bash
./.venv/Scripts/python.exe -m pytest                        # 385 passed
./.venv/Scripts/python.exe -m pytest tests/test_llm_*.py    # 145 passed, ~4 s
./.venv/Scripts/python.exe -m ruff check .                  # All checks passed!
./.venv/Scripts/python.exe -m mypy                          # 29 source files

./.venv/Scripts/python.exe -m app.llm demo                  # 5 grounded + 1 refusal
./.venv/Scripts/python.exe -m app.llm prompt "What component handles card authentication?"
./.venv/Scripts/python.exe -m app.llm ask "How would I troubleshoot a failed cash withdrawal?"
```

### Measured results worth keeping (Stage 4)

```
python -m app.llm demo   (mock provider, real corpus, real retrieval)

  5 seed questions   → all grounded, 5 of 5 passages used, correct document cited
                       e.g. "troubleshoot a failed cash withdrawal" → all 5 passages
                       from atm-cash-withdrawal-troubleshooting.md
  1 off-topic        → "What is the capital of France?"
                       REFUSED, provider call count = 0

python -m app.llm prompt "What component handles card authentication?"

  system  1,826 characters   (frozen, identical for every request)
  user    3,034 characters   (5 fenced passages + the question)
  Corpus is ~55,000 characters — the prompt carries ~5% of it, and the test suite
  asserts every non-cited document is absent from the prompt.
```

### Stage 4 required coverage (prompt.md §12)

| Requirement | Status |
|---|---|
| LLM service abstraction | ✅ `app/llm/base.py` — `LLMProvider` protocol |
| Not tightly coupled to one provider | ✅ No vendor named anywhere in `app/llm/`; asserted by an AST test |
| Implementation replaceable | ✅ One class + one factory branch; the service, CLI and callers are untouched |
| Prompt management | ✅ `app/llm/prompts.py`, versioned `1.0.0`, recorded on every answer |
| System instructions | ✅ `SYSTEM_INSTRUCTIONS`, frozen and identical per request |
| User question handling | ✅ `build_user_turn`; blank questions rejected before any call |
| Context injection | ✅ Fenced, numbered, labelled, escaped; budgeted |
| Response generation | ✅ `LLMService.answer` → `GroundedAnswer` |
| Error handling | ✅ 6 typed errors; timeouts, rate limits, malformed/truncated/refused responses |
| Environment configuration | ✅ 7 `BKA_LLM_*` settings; key is environment-only `SecretStr` |
| **LLM receives retrieved context, not the whole KB** | ✅ Enforced by two configured limits; asserted against the real corpus |
| Mocked LLM tests | ✅ 145 tests; the suite is offline and free *by construction* |
| Handover updated | ✅ This file, continuously through the stage |
| Architecture guide reasoning (§20) | ✅ §20.4 — nine records in the Stage 3 what/why/rejected form |

---

### Result (Stage 3, for reference)

**240 passed, 0 failed** (72 from Stages 1–2, 168 new). Runtime ~33 s.
`ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 21 source files*

| Test file | Tests | Covers |
|---|---|---|
| `tests/test_config.py` | 6 | Defaults, env overrides, invalid values, caching, immutability |
| `tests/test_health.py` | 5 | 200 + payload, schema, OpenAPI, 404, settings wiring |
| `tests/test_logging.py` | 9 | Disk sinks, trace separation, sync/async paths, arguments never logged |
| `tests/test_loader.py` | 52 | Loader behaviour, failure modes, corpus validity, corpus security |
| `tests/test_chunker.py` | 36 | Heading splitting, H1 dropped, code fences, metadata carried, `content` vs `embedding_text`, oversized splitting, overlap, table header repetition, no row lost, **no chunk over budget** |
| `tests/test_embeddings.py` | 19 | Protocol conformance, width, unit length, float32, determinism, token counting, lazy load, blank-input failure, config selection |
| `tests/test_vectorstore.py` | 37 | Ranking, cosine bounds, k handling, **pre-filter vs post-filter**, duplicate/width rejection, save-load round trip, foreign-model / wrong-dimension / old-format / inconsistent-index refusal |
| `tests/test_retriever.py` | 43 | Whole corpus indexed, unique ids, ordering, top-k, filters, score floor, empty-result reporting, source dedup, persistence, **staleness detection**, fingerprint behaviour |
| `tests/test_rag_integration.py` | 33 | **Real model.** Each of the 5 brief questions retrieves its own document first and scores > 0.5; paraphrases find the right domain; all 5 off-topic questions return nothing; distributions separate and the floor sits between them; no chunk silently truncated |

### Commands used

```bash
./.venv/Scripts/python.exe -m pytest                       # 240 passed
./.venv/Scripts/python.exe -m pytest -m "not integration"  # skip the real model
./.venv/Scripts/python.exe -m ruff check .                 # All checks passed!
./.venv/Scripts/python.exe -m mypy                         # Success: 21 source files

./.venv/Scripts/python.exe -m app.rag build                # Indexed 115 chunks
./.venv/Scripts/python.exe -m app.rag demo                 # representative examples
./.venv/Scripts/python.exe -m app.rag calibrate            # threshold evidence
./.venv/Scripts/python.exe -m app.rag search "what error code means the cassette is empty"
```

### Measured results worth keeping

```
Chunking       15 documents → 108 sections → 115 chunks
               tokens: min 31 · median 104 · mean 116 · max 251   (limit 256, 0 over)
               tokens per word across the corpus: 1.13 – 2.82

Calibration    on-topic  (10 questions)  min 0.388  median 0.775  max 0.819
               off-topic ( 5 questions)  min 0.032  median 0.104  max 0.122
               separation +0.266 · midpoint 0.255 · configured 0.250

Seed questions all 5 retrieve their own document at rank 1:
   ATM fail after card auth        0.790  atm-transaction-lifecycle
   what handles card auth          0.804  card-authentication
   payment authorisation API       0.784  payment-authorisation-api
   troubleshoot cash withdrawal    0.819  atm-cash-withdrawal-troubleshooting
   config for transaction limits   —      transaction-limits-configuration

Off-topic      all 5 return NO MATCH
```

### Stage 3 required coverage (prompt.md §11)

| Requirement | Status |
|---|---|
| Document chunking | ✅ `app/rag/chunker.py` |
| Metadata handling | ✅ Full `DocumentMetadata` on every chunk, filterable |
| Embedding generation | ✅ `app/rag/embeddings.py`, behind a protocol |
| Vector storage | ✅ `app/rag/vectorstore.py` + on-disk index |
| Retrieval | ✅ `app/rag/retriever.py` |
| Similarity search | ✅ Exact cosine, top-k, pre-filtering |
| Source metadata | ✅ `RetrievalResult.sources`, deduplicated by document |
| Clean vector-store abstraction | ✅ `VectorStore` protocol; store is injected, not imported |
| Question → Embedding → Search → Docs → Sources demonstrated | ✅ `python -m app.rag demo`, guide §6, README |
| Retrieval layer independently testable | ✅ No LLM anywhere; 4 test files run without the real model |
| Retrieval tests | ✅ 168 new tests |
| Representative retrieval examples | ✅ `python -m app.rag demo`; output in guide §6 and README |
| Handover updated | ✅ This file |
| Architecture guide updated with reasoning | ✅ New §20 decision record (user's additional requirement) |

---

## Problems and Decisions

### 16. The provider decision changed mid-stage, and the venv had to be reverted

**What happened.** The session opened with an instruction to record a decision as
*"Anthropic, key optional, adapter tested against a mock"*. That was written into this
file before any code, and the Anthropic SDK (`anthropic==1.4.0` plus six transitive
packages) was installed into `.venv` to support the adapter. The user then revised the
decision mid-turn: **no concrete provider at all in Stage 4.**

**What was done.** The SDK and its transitive packages were uninstalled with
`uv pip uninstall`. It was never added to `requirements.txt`, never imported, and no
adapter code was written. The decision section in this file was rewritten to the new
decision, with the reversal recorded rather than erased.

**Why the record keeps the reversal.** A handover that shows only the final decision
hides that an alternative was seriously considered and why it was dropped — which is
exactly the context a future session needs when the question comes back before Stage 5.

**Verification that the environment is clean:** `pytest` (385 passed), `ruff`, and
`mypy` all pass with the SDK absent, and a test walks every import in `app/llm/` to
assert no vendor package is reachable. `requirements.txt` is untouched by Stage 4.

### 17. `ruff format --check` disagrees with the repository — NOT a defect

`ruff format --check` reports that `app/llm/prompts.py` and `app/knowledge/loader.py`
(committed and approved in Stage 2) "would be reformatted". The project's Definition of
Done uses `ruff check` (lint) and `mypy`, not `ruff format`; the formatter has never been
applied to this repository. No formatting change was made, to avoid a large unrelated
diff across previously-approved files. **Decision for a later stage:** either adopt
`ruff format` repo-wide in one deliberate commit, or drop the `ruff format` line from
`README.md`'s test section. Flagged for Stage 15.

### 10. `sentence-transformers` 5.x renamed a method — RESOLVED

`get_sentence_embedding_dimension()` is deprecated in favour of
`get_embedding_dimension()` and emits a `FutureWarning` that printed source lines into
the CLI output. Switched to the new name. The dependency is pinned exactly
(`sentence-transformers==5.7.0`), so this is a fixed contract, not a guess.

### 11. The tokenizer warned on text the chunker deliberately over-feeds — RESOLVED

`tokenizer.encode()` warns *"sequence longer than the maximum"* whenever the chunker
measures an oversized section — which is precisely what it exists to do. The warning
made correct behaviour look like a bug. Fixed with `verbose=False` on that one call,
with a comment explaining why. Not a suppressed lint warning; a library warning that is
wrong in this context.

### 12. mypy strict caught two `int | None` model properties — RESOLVED

`get_embedding_dimension()` and `max_seq_length` are typed `int | None`. Coercing with
`int(...)` would have crashed on `None` at an unhelpful place. Both now raise a typed
`EmbeddingError` naming the model, because the whole pipeline is sized from those two
numbers and a wrong size fails as *bad search results*, not as an exception.

### 13. Windows console mangled em dashes in CLI output — RESOLVED

Citations contain `—` and `·`; a cp1252 console rendered them as `?`. `main()` now
reconfigures stdout to UTF-8 rather than degrading the output to ASCII everywhere.

### 14. A test assumption was wrong and the test was corrected, not the code

A test asserted that a punctuation-only query (`"!!! ???"`) raises `EmbeddingError`. It
does not — the string is non-blank, so the hashing embedder returns a zero vector, every
score is 0.0 and the floor rejects everything. That outcome is *better* than raising: it
routes into the agent's "no documented answer" path. The test now asserts the real,
safer behaviour.

### 15. `tmp_path` failed with 96 `PermissionError` for the user — RESOLVED

**Symptom.** The user ran `pytest` in their own shell and got **96 errors**, all
`PermissionError: [WinError 5] Access is denied` on
`C:\Users\New User\AppData\Local\Temp\pytest-of-zk`, from the `tmp_path` fixture.
The same suite passed 240/240 in the Claude Code session.

**Root cause — three facts combined:**

1. Claude Code's shell tools run **elevated** (`IsInRole(Administrator) = True`); the
   user's interactive shell does not.
2. pytest hardens its temp root: `pytest-of-<user>` was created with inheritance
   stripped, holding only `SYSTEM:(F)`, `BUILTIN\Administrators:(F)` and
   `OWNER RIGHTS:(F)`. The parent `Temp` folder *does* carry
   `ZULU\zk:(I)(OI)(CI)(F)`, but none of it was inherited.
3. That directory's **owner was `BUILTIN\Administrators`**, so `OWNER RIGHTS:(F)`
   resolved to Administrators, not to `zk`. There was no ACE for `zk` at all.

Result: an elevated run had access via the Administrators ACE and passed; a
non-elevated run of the same user was denied outright. Because pytest **reuses**
`pytest-of-<user>` across runs, the broken state persisted indefinitely — and was
invisible to whoever created it.

> ⚠️ **Process lesson.** A green test run inside the Claude Code session is not
> evidence the suite passes for the user. The elevation differs. Stage 3's first
> "STAGE COMPLETE" report claimed 240 passed as a project fact when it was only
> true in the elevated context. Verify environment-sensitive results, or state the
> context they were measured in.

**Fix.** `--basetemp=.pytest_tmp` added to `addopts` in `pyproject.toml`, so
`tmp_path` / `tmp_path_factory` no longer touch the Windows user Temp folder at all.
Two properties make this robust rather than a relocation:

- `nodefaultadminowner` is unset (Windows default), so an elevated `zk` process
  creates directories **owned by `zk`** — verified: `.pytest_tmp` owner is `ZULU\zk`,
  and `OWNER RIGHTS:(F)` therefore grants `zk` Full Control.
- pytest **deletes and recreates** an explicit basetemp at the start of every
  session, so a bad state cannot survive a run the way `pytest-of-<user>` did.

**Verified empirically**, not just by reading the ACL: a non-elevated restricted
token (`runas /trustlevel:0x20000`) wrote into `.pytest_tmp` successfully
(`WRITE_OK`). The stale `pytest-of-zk` was deleted, and is no longer recreated.

`.pytest_tmp/` was already git-ignored (added in Stage 2 — see §9).

**Residual risk.** The fix depends on the basetemp being owned by the invoking user.
If a future run creates it under a token whose default owner is the Administrators
group, the same lockout could recur — now limited to a single session, since the
directory is wiped each run. How the original `pytest-of-zk` acquired Administrators
ownership was not determined.

### 9 (revised). `.pytest_tmp/` in the repo root — CAUSE NOW KNOWN

Stage 2 recorded 33 pytest temp files appearing in a `.pytest_tmp/` directory that
"could not be reproduced" and whose cause was "unexplained". It is the same
phenomenon as §15: pytest's temp root resolution behaving differently between an
elevated and a non-elevated context. The directory is now the *deliberate* basetemp,
and the entry that was added to `.gitignore` defensively is now load-bearing.

The process lesson recorded then still stands and applied again this stage:
**always list the exact file set `git add` would stage before committing.**

### Known limitations (carried into Stage 11)

- **Prompt quality is unproven.** The Stage 4 tests assert prompt *structure* — what is
  sent, what is not, what is escaped, what is refused. They cannot assert that a real
  model answers well from these instructions, because no real model has run. That is
  Stage 11's evaluation set, and it is the honest cost of shipping no adapter (§20.4.1).
- **The context budget is in characters, not tokens.** A deliberate over-approximation:
  owning a tokenizer for a provider not yet chosen is not possible, and every provider
  tokenizes differently. Revisit when the first adapter lands (§20.4.7).
- **The mock is a wiring check, not a language model.** It proves context injection,
  citation numbering, error handling and provenance. It proves nothing about grounding
  behaviour under a real model, which is where hallucination actually happens.
- The threshold is calibrated on 10 on-topic and 5 off-topic questions, written by the
  same author as the corpus. Defensible, not proven. Stage 11's evaluation set is where
  it is tested properly.
- Retrieval is dense-only. Hybrid (BM25 + vector) search is the most likely next
  quality improvement and is noted as an extension point.
- `data/vectorstore/` must be rebuilt after any document edit. `get_retriever()` does
  this automatically; `load_retriever()` refuses instead.

### Carried forward from Stages 1–2

- **§1** Health endpoint settings resolution — fixed, `SettingsDep` reads `app.state`.
- **§2** `@traced` cannot decorate FastAPI route handlers — request tracing is Stage 10.
- **§3** Stale `.git/HEAD.lock` blocked a commit — check for a running `git.exe` first.
- **§4** System `python -m venv` is broken on this machine — use `uv venv`.
- **§5** `docs/decisions/auto-changes.log` is written by a local hook — git-ignored.
- **§6** `PyYAML` was an undeclared transitive dependency — now pinned directly.
- **§7** `pip` is unavailable inside the uv venv — use `uv pip install --python ...`.
- **§8** `pytest.raises(Exception)` rejected by ruff `B017` — use the specific type.
- **§9** `.pytest_tmp/` almost got committed — **always list the exact file set
  `git add` would stage before committing.** Applies again this stage. Its
  previously-unexplained cause is now identified: see §9 (revised) and §15.

### Assumptions

- `prompt.md` is authoritative over `ccp.txt` where they differ.
- Global rules require `@traced` on new functions. Applied to public RAG functions, with
  documented exceptions: private helpers on hot paths inside an already-traced call
  (`chunker._split_blocks`, `_pack`, `vectorstore._matching_indices`), Pydantic property
  accessors, and `HashingEmbedder` methods used in tight test loops — tracing those
  would emit thousands of events per index build for no diagnostic value.
- The embedding model is downloaded from Hugging Face on first use. This is a free
  public model download, not a paid API call.

### Open questions for the user

**One, and it blocks Stage 5, not Stage 4:** which concrete LLM provider the first
adapter targets, and whether a live API key is ever wired in. Detail in *Next Action →
Decision required before Stage 5 implementation begins*.

Decisions already taken with the user's explicit answer:

1. **The embedding model** (Stage 3) — local `sentence-transformers` /
   `all-MiniLM-L6-v2`, chosen over a lexical embedder or a paid hosted API.
2. **The LLM provider** (Stage 4) — **no concrete provider this stage; build and test
   against a mock only. The real adapter and any live key are deferred to a decision
   before Stage 5.** Full record in *Next Action → Decision taken before Stage 4
   implementation begins*. Superseded an earlier instruction in the same session
   (Problems §16).

### Assumptions added in Stage 4

- `@traced` is applied to the public functions of the LLM layer. Deliberate exceptions,
  consistent with Stage 3: Pydantic property accessors on the models, and the private
  helpers `prompts._attribute` / `prompts._fence_safe` and `mock._build` /
  `_next_scripted` / `_synthesise`, which run inside an already-traced call.
- The mock's token counts are a crude `len(text) // 4` estimate, named as an estimate in
  the source. They exist so usage accounting is exercised end to end, not to be accurate.

### Security check (Stage 4)

✅ **No paid API call is possible.** The only provider is in-process. A test parses every
import in `app/llm/` and asserts no vendor SDK, no HTTP client and no URL is reachable
from the package. This is structural, not procedural.
✅ **No API key anywhere.** `BKA_LLM_API_KEY` is unset, environment-only, and typed
`SecretStr` — asserted to appear in neither `repr(settings)` nor `settings.model_dump()`.
✅ **No vendor name in the system prompt** and no proprietary reference (CR2, BankWorld) —
both asserted by tests.
✅ **Prompt-injection guards implemented, not just documented:** passages fenced in
`<retrieved_documentation>`, declared untrusted in the system prompt before the model sees
them, delimiters occurring inside a passage escaped so a document cannot break out, and
the question placed last, outside the fence. The escape is a passing test using hostile
content.
✅ **Neither the prompt nor the answer text is logged.** Both embed document content;
`llm.answered` records provider, model, prompt version, counts, tokens and stop reason
only. What a request record should contain is decided deliberately in Stage 10.
⚠️ **Carried forward, unchanged:** `retriever.py` still logs the question text —
deliberate, flagged in Stage 3 for reassessment in Stage 13.

### Security check (all stages)

✅ No secrets, keys, tokens or credentials anywhere in the repository.
✅ No real `.env` file exists. `.env` and `.env.*` are git-ignored (`.env.example` excepted).
✅ `logs/` and `data/vectorstore/` are git-ignored. Traced arguments are never logged.
✅ The embedding model runs **locally** — no document text and no question leaves the
machine during indexing or retrieval.
✅ Corpus still scanned by the test suite for secret-shaped values and card-number-shaped
digit runs; no matches.
✅ `yaml.safe_load` only. Index load validates format, model, dimension and consistency.
✅ No nested `banking-knowledge-agent/` directory.
⚠️ **Noted, not a defect:** `retriever.py` logs the question text. Deliberate — these are
technical support queries about a synthetic platform, not customer data. Flagged in the
source for reassessment in Stage 13.

---

## Git

| | |
|---|---|
| **Branch** | `main` |
| **Remote** | `origin` → `https://github.com/Zuleikha/banking-knowledge-agent.git` |
| **Stage 1 commit** | `d448cc1` — `feat(stage-1): project foundation — config, logging, tracing, health` |
| **Stage 2 commit** | `cca70af` — `feat(stage-2): synthetic banking knowledge base and document loader` |
| **Stage 3 commit** | `be9297c` — `feat(stage-3): RAG pipeline — chunking, embeddings, vector store, retrieval` |
| **Stage 3 docs commit** | `docs(stage-3): record commit hash and push result in handover` — this file's own commit, directly on top of `be9297c` |
| **Stage 4 commit** | `bee4b22` — `feat(stage-4): LLM abstraction — provider seam, prompts, context injection` |
| **Push status** | ✅ Pushed to `origin/main`; verified `origin/main == local HEAD == bee4b22` |
| **Working tree** | Clean, apart from git-ignored local files |
| **Committed in Stage 4** | 18 files: 11 added, 7 modified — 3,574 insertions, 205 deletions |
| **Committed in Stage 3** | 21 files: 13 added, 8 modified — 4,816 insertions, 302 deletions |
| **Deliberately not committed** | `prompt.md`, `prompt1.md`, `ccp.txt`, `docs/decisions/auto-changes.log`, `.venv/`, `logs/`, `data/vectorstore/`, `.pytest_tmp/`, caches |

### The exact Stage 4 file set — verified with `git add -An`, 2026-09-09

18 paths, and **no others**:

```
add '.env.example'                    add 'app/llm/__init__.py'
add '.gitignore'                      add 'app/llm/__main__.py'
add 'README.md'                       add 'app/llm/base.py'
add 'app/core/config.py'              add 'app/llm/factory.py'
add 'docs/HANDOVER.md'                add 'app/llm/mock.py'
add 'docs/architecture-guide.html'    add 'app/llm/models.py'
add 'tests/conftest.py'               add 'app/llm/prompts.py'
                                      add 'app/llm/service.py'
add 'tests/test_llm_prompts.py'
add 'tests/test_llm_provider.py'
add 'tests/test_llm_service.py'
```

### `prompt1.md` — RESOLVED, and why `.gitignore` is in the Stage 4 commit

`prompt1.md` appeared as a new untracked local file this session. It was **not** in
`.gitignore`, so `git add -An` confirmed it would have been staged — the exact trap
Problems §9 was written about, caught by running the checklist rather than by assuming.

**Fix.** `prompt1.md` added to `.gitignore` beside `prompt.md`, in the *Local working
files* section. Re-ran `git add -An` and confirmed it no longer appears. That is why
`.gitignore` is a modified file in the Stage 4 set: it is a Stage 4 change, not a stray
edit.

> **Process note.** The listing was produced *before* the commit, which is what made this
> visible. `git status` alone would not have shown it as clearly — it collapses untracked
> directories into one line. Third stage running, third time this step has earned itself.

### Pre-commit checklist (worked for Stages 3 and 4; reuse it)

1. `git add -An` — list the **exact** file set. `git status` collapses untracked
   directories into a single line and will hide what is really being staged
   (Problems §9).
2. Confirm `data/vectorstore/`, `logs/`, `.venv/`, `.pytest_tmp/`, `prompt.md`,
   `prompt1.md`, `ccp.txt` are **not** in that list. Grep precisely — a loose
   `vectorstore` pattern matches the legitimate `app/rag/vectorstore.py` source file.
3. Scan the staged set for secret-shaped assignments, long base64/hex literals and
   card-number-shaped digit runs. *(Stage 4: run over all new files — no matches.)*
4. Check for a stale `.git/*.lock` and a running `git.exe` (Problems §3).
5. Re-run `pytest`, `ruff check .`, `mypy`.
6. Commit, push, verify `origin/main == HEAD`, then record the hash here.

> **When a new local working file appears, ignore it rather than remembering to skip it.**
> An entry in `.gitignore` survives the session; an intention does not.

---

## Next Action

**Begin Stage 5 — Knowledge Agent.** Stage 4 is approved, committed (`bee4b22`) and
pushed. Settle the decision below **before** implementation begins, and write the answer
into this file before writing code.

### Stage 5 scope (from `prompt.md` §13), for when it starts

1. An agent that receives a technical question, decides whether retrieval is required,
   retrieves, passes context to the LLM, and produces a source-backed answer.
2. It must clearly indicate when the knowledge base is insufficient, and must not invent
   technical facts. Stage 4's `LLMService` already refuses without a model call when
   retrieval is empty — the agent builds on that guard rather than replacing it.
3. The five seed questions in `prompt.md` §13 are the worked examples.
4. Agent tests. They can stay offline against `MockLLMProvider`, exactly as Stage 4 did,
   regardless of how the provider decision below is answered.
5. Update `docs/architecture-guide.html` (§7 agent flow, and a §20.5 decision record in
   the same what / why / rejected form).
6. Update this handover. **STOP** and wait for approval.

### Decision required before Stage 5 implementation begins

**Which concrete LLM provider the first adapter targets, and whether a live API key is
ever wired in.** This was explicitly deferred out of Stage 4 by the user. The seam,
the prompt layer, the error taxonomy and the configuration are all in place, so the
adapter is an additive change: one class implementing `LLMProvider`, one branch in
`app/llm/factory.py`, one entry in `AVAILABLE_PROVIDERS`, and a pinned SDK in
`requirements.txt`.

Points the answer needs to cover:

- **Which vendor.** Anthropic was proposed and then withdrawn earlier in this session
  (Problems §16); no vendor is currently chosen.
- **Whether a real key is used at all.** Stage 5's agent can be built and tested entirely
  against the mock, exactly as Stage 4 was. A live call is a **paid** call and needs the
  user's explicit confirmation at the time — this decision does not pre-authorise one.
- **What happens to the no-network guarantee.** The AST test in
  `tests/test_llm_provider.py` currently asserts that no vendor SDK is importable from
  `app/llm/`. Adding an adapter must consciously amend that test rather than delete it —
  ideally narrowing it so the seam modules stay vendor-free and only the adapter is
  exempt.

### Decision taken before Stage 4 implementation begins — LLM provider

**Decided by the user, 2026-09-09.** This supersedes the "decision required" note that
previously stood here.

| | |
|---|---|
| **Concrete provider** | **None this stage.** No real provider is picked or wired in |
| **What Stage 4 builds against** | A **mock** `LLMProvider` implementation, only |
| **API key** | Provider-neutral `BKA_LLM_API_KEY`, environment-only, **optional and unset** |
| **Paid calls** | **None.** No live API call this stage, in the suite or by hand |
| **Deferred to** | A separate decision **before Stage 5** — which real provider, and whether a key is ever wired in |

**What this means for the implementation**

- `LLMProvider` (in `app/llm/base.py`) is the vendor-agnostic seam. Stage 4 delivers the
  seam, the prompt layer, the context-injection layer, the error taxonomy and one mock
  implementation behind it. It delivers **no** vendor adapter.
- Because there is no vendor adapter, there is nothing that *can* make a paid call. The
  suite is offline, deterministic and free by construction, not by discipline.
- `BKA_LLM_API_KEY` is defined now and read from the environment only, so the
  configuration seam exists before the provider does. It is unset by default, held as a
  Pydantic `SecretStr`, never hardcoded, never logged, never written to this handover.
- `BKA_LLM_PROVIDER` defaults to `mock`. Requesting any other value fails **loudly** with
  a typed `LLMConfigurationError` saying the concrete adapter arrives in Stage 5 — it
  never silently degrades to the mock, which would let a caller believe a real model
  answered.

> ⚠️ **Correction, same session.** An earlier instruction in this session recorded
> *"Anthropic, key optional, adapter tested against a mock"*, and that version was written
> to this file. The user then revised it to the decision above: **no concrete provider at
> all in Stage 4.** The Anthropic SDK had been installed into `.venv` under the earlier
> instruction; it was **uninstalled**, and it was never added to `requirements.txt`, never
> imported, and no adapter code was written. Recorded because the file must show what was
> decided *and* what was reversed.

**Stage 4 scope, delivered.** Every item of `prompt.md` §12 is implemented and mapped to
its evidence in *Testing → Stage 4 required coverage* above.

---

## Constraints carried forward (all stages)

- Synthetic content only. No proprietary, confidential or copyrighted material.
- Documents and tool results are data, not instructions — untrusted LLM input. Stage 4
  implemented the first concrete defences (fencing, escaping, a stated rule); Stage 6
  extends the same treatment to tool results, and Stage 13 reviews the whole surface.
- No secrets in documents, tests, logs or the handover.
- **Never spend money or call a paid external API without the user's explicit
  confirmation.** Still live and still unresolved: a real LLM call is a paid call. The
  repository currently contains no code path that can make one, and that property should
  not be given up casually when the first adapter lands.
- Do not create a nested `banking-knowledge-agent/` directory.
- Approval cycle: IMPLEMENT → TEST → UPDATE HANDOVER → SHOW → **STOP** → APPROVAL →
  VERIFY → COMMIT → PUSH → VERIFY PUSH → NEXT STAGE. Never commit an unapproved stage.
