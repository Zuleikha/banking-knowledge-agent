# HANDOVER — Banking Knowledge Agent
A decision is not recorded until it is written into docs/HANDOVER.md.
Do not let a decision live only in conversation history. 
If a decision is made mid-stage, before implementation begins, 
update HANDOVER.md immediately, not at stage completion.
> **Read this first in any new Claude Code session.**
> This file, not conversation history, is the record of project progress.
> Never assume a previous session completed work unless the repository confirms it.

Last updated: **2026-09-10** · Stage 5 **Checkpoint A approved, committed (`1478631`) and
pushed** · Checkpoint B **implemented and awaiting approval**. The previously-open
provider decision is **RESOLVED** — two adapters, no vendor chosen, default stays `mock`,
no live key. See *Stage 5 decision*.

---

## ⏱️ SESSION CHECKPOINT — start here

**Session state:** Stage 5 **Checkpoint B implemented, awaiting the user's approval.**

### State at checkpoint

| | |
|---|---|
| Last **approved** work | **Stage 5 Checkpoint A** (approved 2026-09-10, `1478631`, pushed) |
| `HEAD` | `1478631` = `origin/main` |
| Working tree | 15 uncommitted Checkpoint B paths |
| Tests | **601 passed** · ruff clean · mypy strict clean (37 source files) |
| Current stage | **Stage 5 — Knowledge Agent + concrete LLM adapters** |

> 💸 **Spending is now possible and is guarded in four places.** `BKA_LLM_PROVIDER`
> defaults to `mock` (free). Setting it to `anthropic` or `openai` **and** setting
> `BKA_LLM_API_KEY` makes every answered question a **paid** call. No live call has ever
> been made from this repository.

### To resume Stage 5 work

```bash
cd D:/PROJECTS/banking-knowledge-agent
git log --oneline -3          # expect 1478631 feat(stage-5a) on top
./.venv/Scripts/python.exe -m pytest        # expect 601 passed
./.venv/Scripts/python.exe -m app.agent demo    # 5 grounded + 2 refusals, FREE
```

> If the venv is missing, recreate it per the Stage 4 instructions below — note that
> `requirements.txt` now also installs `anthropic` and `openai` (small pure-Python
> packages; the large artefact is still PyTorch).

### Stage 5 is split into two approval checkpoints

| | Scope | Status |
|---|---|---|
| **Checkpoint A** | The knowledge agent itself (`prompt.md` §13), tested entirely against `MockLLMProvider`. No vendor involved | ✅ **Approved 2026-09-10, committed `1478631`, pushed** |
| **Checkpoint B** | Two concrete adapters — `AnthropicProvider` **and** `OpenAIProvider` — offline-tested, default still `mock` | 🔄 **in progress** |

> ⛔ Each checkpoint stops for explicit approval before any commit or push.

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
| **Stage number** | 5 |
| **Stage name** | Knowledge Agent + concrete LLM adapters |
| **Status** | 🔄 **IN PROGRESS — Checkpoint B** |
| **Last completed step** | Checkpoint A approved 2026-09-10; committed `1478631` and pushed to `origin/main`, push verified |
| **Next step** | Implement Checkpoint B — `AnthropicProvider` and `OpenAIProvider`, offline-tested, default still `mock` |

> ⛔ Each Stage 5 checkpoint must STOP after implementation and testing, and wait for
> explicit approval before any commit or push. Checkpoint B must not begin until
> Checkpoint A is approved.

### Previous stages

| Stage | Name | Status |
|---|---|---|
| 1 | Project Foundation | ✅ Approved 2026-09-03, committed `d448cc1`, pushed |
| 2 | Domain Knowledge | ✅ Approved 2026-09-08, committed `cca70af`, pushed |
| 3 | RAG Pipeline | ✅ Approved 2026-09-09, committed `be9297c`, pushed |
| 4 | LLM Abstraction | ✅ Approved 2026-09-09, committed `bee4b22`, pushed |

---

## Stage 5 decision — the concrete LLM provider (previously deferred, now RESOLVED)

**Decided by the user, 2026-09-10.** This resolves the question left open at the end of
Stage 4 (*"which vendor, and is a live key ever wired in?"*) and supersedes the
"decision required before Stage 5" note that previously stood in *Next Action*.

| | |
|---|---|
| **How many adapters** | **Two, not one** — `AnthropicProvider` and `OpenAIProvider` |
| **Which vendor is "the" vendor** | **None.** No vendor is exclusively chosen; the seam is proved rather than asserted |
| **Default provider** | **`mock`, unchanged.** Nothing calls a real API unless someone deliberately sets `BKA_LLM_PROVIDER` |
| **API key** | `BKA_LLM_API_KEY` stays environment-only, optional, **unset**. Not wired in, not hardcoded, not committed |
| **Live calls** | **None.** No live call in Checkpoint A, in Checkpoint B, in the test suite, or by hand. Building two adapters does **not** authorise a live call, now or later |
| **Adapter tests** | Offline — the SDK client / HTTP layer is mocked. No network, no cost, in CI or locally |
| **The AST guard** | **Narrowed, not deleted.** `base.py` · `prompts.py` · `service.py` · `factory.py` · `mock.py` must stay vendor-free; only the two adapter modules are exempt |

**Why two adapters rather than one.** One adapter proves an adapter can be written. Two
prove the *abstraction* — that a vendor swap is a configuration change and nothing else.
It also retires the vendor question permanently instead of re-litigating it at Stage 9 or
Stage 14. Full record with rejected alternatives goes in
`docs/architecture-guide.html` §20.6.

> ⚠️ This reverses the Stage 4 rejected-alternative *"Two adapters, to 'prove' the seam"*
> (guide §20.4.1), which was rejected on the grounds that a second implementation means a
> second paid vendor account. That objection does not survive the "no live call" rule:
> both adapters are offline-tested, so neither requires an account. Recorded because the
> file must show what was reversed, not only what was decided.

---

## Current Work

### Implemented in Stage 5 — Checkpoint B (this session)

- **`AnthropicProvider`** — `app/llm/anthropic_provider.py`. Official `anthropic` SDK.
  Translates request, response and the whole exception hierarchy. Reads text from the
  **text blocks**, not `content[0]` — with thinking on, the first block is reasoning, and
  reading it positionally would put reasoning where the answer belongs.
- **`OpenAIProvider`** — `app/llm/openai_provider.py`. Official `openai` SDK. Same seam,
  different shape: system prompt as a message, `max_completion_tokens` (not the
  deprecated `max_tokens`, which reasoning models reject), and a refusal reported on
  `message.refusal` **while `finish_reason` still says `"stop"`**.
- **Pinned** — `anthropic==1.4.0`, `openai==3.11.0` in `requirements.txt`, with a comment
  stating that installing them does not enable spending.
- **Factory extended** — `AVAILABLE_PROVIDERS = ("mock", "anthropic", "openai")`, plus
  `PAID_PROVIDERS` and `is_paid_provider()`. **The default is unchanged: `mock`.** The
  SDK import is *deferred into the branch that needs it*, so the app still starts, still
  serves `/health` and still runs on the mock with neither SDK installed; a missing SDK
  becomes a typed configuration error, not an `ImportError`.
- **AST guard narrowed, not deleted** — `ADAPTER_MODULES` is an explicit two-name
  allow-list; every other module in `app/llm/` is default-denied. The five seam modules
  named in the instruction are asserted to exist, so a rename cannot empty the guarded
  set. The adapters stay bound by the secrets rule (no hardcoded URL, no key literal).
- **Cost guard** — both CLIs warn when a paid provider is configured, and `demo` (7
  questions in `app.agent`, 6 in `app.llm`) **refuses** without `--paid`, checking before
  an index or a client is built. `ask` only warns: one call is a proportionate mistake.
- **Tests** — 112 new (489 → **601**): `tests/test_llm_adapters.py` (99) plus the
  rewritten guard and default-provider tests in `tests/test_llm_provider.py`. **Entirely
  offline** — every test injects a fake SDK client. No network call, no key, no cost.
- **Docs** — guide §20.6–§20.9 (four records), §2, §3, §4, §9, §12, §14, §16, §19;
  README gained an "LLM providers — two adapters, and why" section.

> ⚠️ **No live API call has been made** — not in the suite, not by hand. Building the
> adapters did not authorise one, and it still needs the user's explicit confirmation at
> the time.

#### One thing was added beyond the stated Checkpoint B scope, deliberately

`LLMConnectionError` was added to `app/llm/base.py` (a seam module). **Why:** Stage 4
designed the error taxonomy with no adapter to test it against, and it had a gap — the
only retryable types were a timeout and a rate limit. Both SDKs raise a plain
`APIConnectionError` and an `InternalServerError` that are neither. The two available
mappings were each wrong in the one field callers branch on: `LLMTimeoutError` would
misname a connection reset, and `LLMProviderError` would mark a transient 502 permanently
broken. Shipping a knowingly-wrong `retryable` flag is worse than adding a class, so the
class was added — additive, nothing else changed. Recorded in guide §20.9, and it is the
clearest evidence that building a real adapter was worth doing: Stage 4's own tests could
never have found this, because a mock raises whatever a test tells it to.

### Implemented in Stage 5 — Checkpoint A (approved, committed `1478631`, pushed)

- **Routing decision** — `app/agent/policy.py`. `decide_retrieval(question)` returns a
  frozen `RetrievalDecision` carrying the rule that produced it. Two reasons:
  `knowledge_required` (search) and `no_searchable_content` (a question with no
  alphanumeric character at all — skip the search, say so). Every real question takes the
  first branch, and the module states plainly why a second substantive branch would be
  fiction in Stage 5: retrieval is the agent's only evidence until MCP lands in Stage 6.
- **The agent** — `app/agent/agent.py`. `KnowledgeAgent.ask` = decide → retrieve →
  generate → record. Both collaborators injected as in Stages 3 and 4, so the tests run
  it with a hashing embedder and `MockLLMProvider` and production changes nothing.
- **One refusal path, and it is Stage 4's.** A question the agent declines to search is
  turned into an empty `RetrievalResult` and handed to `LLMService.answer()`, which takes
  the guard it already had: the fixed sentence, and **zero** provider calls. The agent
  writes no refusal of its own. This is the user's Checkpoint A requirement 2 — build on
  the existing guard, do not replace it — and it is asserted by a test that both routes
  produce the identical string.
- **Execution record as a returned value** — `app/agent/models.py`. `AgentAnswer` wraps
  the LLM layer's `GroundedAnswer` unmodified and adds `RetrievalDecision` +
  `RetrievalSummary` (performed, candidates, returned, top score, floor, document ids).
  Stage 9 renders provenance rather than scraping its own logs. The summary carries
  *shape* only — passage text stays out of the object that is safe to log and display.
- **Failures propagate.** A timeout, rate limit or truncated generation raises out of
  `ask()` as its typed `LLMError`. Turning an outage into "the knowledge base does not
  contain enough information" would send the reader to fix the wrong thing and would fold
  infrastructure noise into the refusal rate Stage 11 measures grounding with.
- **Factory** — `app/agent/factory.py`. `get_agent()` composes retriever + service. It
  does **not** choose a provider; that stays in `app/llm/factory.py`, so
  `BKA_LLM_PROVIDER` is interpreted in exactly one place.
- **CLI** — `python -m app.agent ask | demo`. The demo runs the five seed questions plus
  two controls that must be declined for two *different* reasons.
- **Tests** — 104 new tests across 2 files (385 → **489**). No new dependency, no new
  setting: Checkpoint A adds no configuration surface.
- **Docs** — architecture guide §7 rewritten as BUILT, new §20.5 (five decision records
  in the Stage 3/4 what–why–rejected form), plus §1 stage table, §2 structure, §4
  components, §5 data flow, §14 testing, §16 security, header and footer. README gained a
  "Knowledge agent" section.

### Implemented in Stage 4

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

**Stage 5 Checkpoint B is complete, tested and documented, and is waiting for the user's
approval before any commit.** Nothing from Checkpoint B is committed or pushed.

### What remains unfinished in Checkpoint B

Nothing the instruction requires. Deliberately absent, recorded as deferred rather than
missed:

1. **Answer quality evidence — still unmeasured, and now for a different reason.** Real
   adapters exist, but no live call has been made, so nothing proves a real model answers
   *well* from these prompts. The adapters are proven correct in what they **send, parse
   and translate**, not in what comes back. Measuring the rest needs a key, a budget and
   explicit confirmation; it is Stage 11's evaluation set.
2. **Streaming and async** — neither adapter streams. `CompletionRequest` carries no
   streaming flag and the protocol is synchronous (Stage 4, guide §20.4.9). Adding either
   now would be an untested interface with no caller until Stage 9.
3. **Retry policy** — the errors carry `retryable`, and both SDK clients are constructed
   with `BKA_LLM_MAX_RETRIES`, but nothing above the seam acts on the flag. Choosing a
   backoff belongs with a real deadline, which arrives with the HTTP layer.
4. **HTTP exposure** — the agent is still CLI-only. Stage 9.

### Not yet implemented (later stages)

MCP tools (6) · Tool selection (7) · Conversation context (8) · Web interface (9) ·
Request observability (10) · Evaluation framework (11) · Docker (12) ·
Security review (13) · Production architecture (14) · Final review (15)

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

AGENT (Stage 5 — the seam; the first component that owns a whole request)

Question
   │
   ▼  KnowledgeAgent.ask        blank ──▶ ValueError, nothing is called
   ▼  decide_retrieval          RetrievalDecision(retrieve, reason, explanation)
   │
   ├── retrieve=False ──▶ empty RetrievalResult      no embedding, no search
   │   "no_searchable_content"                       e.g. "!!! ???"
   └── retrieve=True  ──▶ Retriever.retrieve()       the RETRIEVAL block above
   │
   ▼  LLMService.answer()       the GENERATION block below, UNCHANGED
   ▼
AgentAnswer   text · sources · decision · RetrievalSummary · GroundedAnswer
   │
   └──▶ logs/app.log  "agent.answered"   route, counts, top score, document ids —
                                         never the question, passages or answer

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

HTTP (unchanged from Stage 1 — the agent is reachable from the CLI only; wiring it
to an endpoint is Stage 9)
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
| `app/agent/models.py` | `RetrievalDecision`, `RetrievalSummary`, `AgentAnswer` |
| `app/agent/policy.py` | `decide_retrieval` — is a knowledge search required? |
| `app/agent/agent.py` | `KnowledgeAgent.ask` / `ask_many` — decide, retrieve, generate |
| `app/agent/factory.py` | `get_agent` — composition from configuration |
| `app/agent/__main__.py` | CLI: ask / demo |
| `app/llm/anthropic_provider.py` | Anthropic adapter — **paid**; one of two vendor modules |
| `app/llm/openai_provider.py` | OpenAI adapter — **paid**; the other |

### Important design decisions (Stage 5 — Checkpoint B)

Summary only — the **full reasoning, with rejected alternatives, is in
`docs/architecture-guide.html` §20.6–§20.9**, which is the authoritative record.

| Decision | Reasoning (short) |
|---|---|
| **Two adapters, not one; no vendor chosen** (5.6) | One adapter proves an adapter can be written; two prove the *abstraction*. Writing the second is what forces the first's assumptions out of shared code — the two APIs disagree on system-prompt placement, the token-ceiling parameter, stop reasons, where a refusal is reported, how text is returned and every usage field name. It also closes the vendor question instead of leaving it to return at Stage 9 and Stage 14 |
| **Default stays `mock`; four independent guards** (5.7) | Spending needs two deliberate acts. The provider default is the guard that does not depend on the environment — "the key isn't set" fails the moment a contributor exports one for another project. `demo` refuses rather than warns because it is 7 calls with no undo; `ask` warns because 1 is proportionate |
| **AST guard narrowed, not deleted** (5.8) | Adding adapters is exactly when that guard starts earning its keep. Explicit two-name allow-list, everything else default-denied. Narrowing also exposed a real bug: the old substring match on `"import anthropic"` would have failed the factory's own honest `from app.llm.anthropic_provider import …`, and the tempting fix was to hide the import behind `importlib` — defeating the guard to satisfy it. The test was wrong; the test was fixed |
| **`LLMConnectionError` added to the taxonomy** (5.9) | Stage 4 wrote the taxonomy with nothing to test it against and left a gap: no retryable type for a connection failure or a 5xx. Both mappings available were wrong in the one field callers read. A concrete adapter found it in an hour; a mock never could |

### Important design decisions (Stage 5 — Checkpoint A)

Summary only — the **full reasoning, with rejected alternatives, is in
`docs/architecture-guide.html` §20.5**, which is the authoritative record.

| Decision | Reasoning (short) |
|---|---|
| **The decision has one substantive branch, and says so** (5.1) | Retrieval is the agent's only evidence until Stage 6, so "always yes" is the honest answer. A keyword classifier fails in both directions — *"why did the withdrawal reverse?"* has no keyword and retrieves fine; *"what is a payment in cricket?"* has one and shouldn't. The floor already answers relevance, with calibration behind it |
| **One refusal path, and it is Stage 4's** (5.2) | The refusal sentence is load-bearing: the API, the web UI and Stage 11 all detect "no answer" by matching it exactly. A second branch is a second thing that must agree, and drift would be invisible until a harness stopped counting refusals |
| **Execution record is a returned value, not a log line** (5.3) | `prompt.md` §15 requires the interface to show what happened. If it only exists in `app.log`, Stage 9 parses its own logs to render a page. Summary and passages are split on a *security* line: shape is safe to log and display, document text is not |
| **A provider failure raises; it never becomes a refusal** (5.4) | An agent that never fails sounds good and is a defect. "Undocumented" means *write the document*; "timeout" means *fix the provider*. Collapsing them also folds infrastructure noise into the grounding metric |
| **The agent is a seam, not a layer of logic** (5.5) | The retriever still has no LLM dependency and the service still does not retrieve. Absorbing either job would end that separation exactly when it became useful — and injection is what keeps 104 agent tests offline and free |

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

### Added in Stage 5 Checkpoint B (3 files, uncommitted)

| File | Purpose |
|---|---|
| `app/llm/anthropic_provider.py` | Anthropic adapter — request/response/error translation |
| `app/llm/openai_provider.py` | OpenAI adapter — the same seam, a different vendor |
| `tests/test_llm_adapters.py` | 99 tests — both adapters, offline against a fake client |

### Modified in Stage 5 Checkpoint B (8 files, uncommitted)

| File | Change |
|---|---|
| `app/llm/base.py` | Added `LLMConnectionError` (retryable) — the gap the adapters exposed |
| `app/llm/factory.py` | 3 providers, `PAID_PROVIDERS`, `is_paid_provider()`, deferred SDK import |
| `app/llm/__init__.py` | Exports `LLMConnectionError`; docstring rewritten for two adapters |
| `app/llm/__main__.py` | Paid-provider warning; `demo --paid` guard |
| `app/agent/__main__.py` | Paid-provider warning; `demo --paid` guard |
| `app/core/config.py` | Comments only — `llm_provider`, `llm_api_key`, transport |
| `requirements.txt` | `anthropic==1.4.0`, `openai==3.11.0`, pinned, with a no-spend note |
| `.env.example` | LLM and secrets sections rewritten for three providers |
| `tests/test_llm_provider.py` | Guard narrowed to seam modules; new no-paid-call-by-default class |
| `README.md` | Status, stack, layout, test count, new "LLM providers" section |
| `docs/architecture-guide.html` | §20.6–§20.9 added; §2, §3, §4, §9, §12, §14, §16, §19 |
| `docs/HANDOVER.md` | This file |

> The venv gained `anthropic`, `openai` and 5 transitive packages
> (`httpx2`, `httpcore2`, `jiter`, `docstring-parser`, `truststore`). This is a package
> download, not an API call — the same category as Stage 3's model download.

### Added in Stage 5 Checkpoint A (8 files, committed in `1478631`)

| File | Purpose |
|---|---|
| `app/agent/__init__.py` | Package exports and the layer overview docstring |
| `app/agent/models.py` | `RetrievalDecision`, `RetrievalSummary`, `AgentAnswer` |
| `app/agent/policy.py` | `decide_retrieval` + the reasoning against a classifier/router |
| `app/agent/agent.py` | `KnowledgeAgent` — the seam between `rag/` and `llm/` |
| `app/agent/factory.py` | `get_agent` |
| `app/agent/__main__.py` | CLI: ask / demo |
| `tests/test_agent.py` | 77 tests — policy, wiring, both refusal routes, record, errors |
| `tests/test_agent_integration.py` | 27 tests — real model, the 5 seed questions + controls |

### Modified in Stage 5 Checkpoint A (4 files, committed in `1478631`)

| File | Change |
|---|---|
| `tests/conftest.py` | `KnowledgeAgent` import; new `agent` fixture |
| `README.md` | Status, architecture, layout, test count, new "Knowledge agent" section |
| `docs/architecture-guide.html` | §7 rewritten as BUILT; §20.5 added (5 records); §1, §2, §4, §5, §14, §16, header, footer |
| `docs/HANDOVER.md` | This file |

> `requirements.txt`, `app/core/config.py` and `.env.example` are **unchanged** by
> Checkpoint A. The agent added no dependency and no setting — it composes what Stages 3
> and 4 already configured, which is the point of it being a seam.

### Added in Stage 4 (11 files, committed in `bee4b22`)

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

### Modified in Stage 4 (7 files, committed in `bee4b22`)

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

### Result (Stage 5 — Checkpoint B)

**601 passed, 0 failed** (489 from Stages 1–5A, **112 new**). Runtime ~52 s.
`ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 37 source files*

> ⚠️ Measured inside the Claude Code session, which is **elevated** (Problems §15).
> Please confirm 601 in your own shell before approving.

| Checkpoint B test file | Tests | Covers |
|---|---|---|
| `tests/test_llm_adapters.py` | 99 | **Both adapters, entirely offline** — every test injects a fake SDK client. **Construction**: a missing key refuses before a client exists; an injected client needs no key; each adapter owns its own default model. **What is sent**: system prompt placement (top-level vs a message), `max_tokens` vs `max_completion_tokens`, the user turn verbatim, and *no* sampling or thinking parameters. **What is parsed**: every stop-reason and finish-reason value including unknown and `None`; a leading thinking block not mistaken for the answer; an OpenAI refusal arriving labelled `"stop"`; null content; a reply with no choices raising; usage translated from differently-named fields; the *answering* model recorded rather than the requested one. **Error translation**: all nine mappings per vendor with the right `retryable` flag, the ordering traps asserted (`APITimeoutError` **is** an `APIConnectionError`), `retry-after` parsed, absent and HTTP-date forms both degrading to `None`, the cause preserved, and a 401 message asserted not to echo the key. **The cost guard**: `demo` refuses before building anything; the free path is not blocked. **The seam is proved**: identical assertions run against *both* adapters, through `LLMService` and through `KnowledgeAgent` |
| `tests/test_llm_provider.py` | 13 changed / added | The guard narrowed to seam modules with an explicit two-name exemption; the seam module names asserted to exist; the factory asserted to *name* vendors while importing none; both adapters asserted free of hardcoded URLs and key literals; and a new `TestNoPaidCallByDefault` class — `mock` is the default with the env var cleared, the registry lists it first, `PAID_PROVIDERS` excludes it, and each paid provider without a key raises naming `BKA_LLM_API_KEY` and the word `PAID` |

### Commands used (Checkpoint B)

```bash
./.venv/Scripts/python.exe -m pytest                            # 601 passed, ~52 s
./.venv/Scripts/python.exe -m pytest tests/test_llm_adapters.py # 99 passed, ~4 s
./.venv/Scripts/python.exe -m ruff check .                      # All checks passed!
./.venv/Scripts/python.exe -m mypy                              # 37 source files
```

### The no-spend properties, verified by hand (2026-09-10)

```
1. default, no env set
   -> llm.provider_selected  paid=False provider=mock
   -> grounded answer, 5 passages, free

2. BKA_LLM_PROVIDER=anthropic, python -m app.agent demo
   -> "!! BKA_LLM_PROVIDER=anthropic - this is a PAID API."
   -> "REFUSED: demo would make up to 7 paid calls. Re-run with --paid"
   -> exit code 2, no agent built, no call made

3. BKA_LLM_PROVIDER=anthropic, python -m app.agent ask "test"   (no key)
   -> warning printed, then LLMConfigurationError:
      "needs BKA_LLM_API_KEY, which is unset ... a real call is a PAID call"
   -> no SDK client was ever constructed

4. env restored
   -> provider = mock | key set = False
```

**No live API call was made at any point.**

### Checkpoint B required coverage (the user's instruction)

| Requirement | Status |
|---|---|
| 1. `AnthropicProvider` using the official `anthropic` SDK | ✅ `app/llm/anthropic_provider.py` |
| 2. `OpenAIProvider` using the official `openai` SDK | ✅ `app/llm/openai_provider.py` |
| 3. Both pinned in `requirements.txt` | ✅ `anthropic==1.4.0`, `openai==3.11.0` |
| 4. Factory + `AVAILABLE_PROVIDERS` accept `anthropic`/`openai`; **default stays `mock`** | ✅ Default unchanged and asserted with the env var cleared |
| 5. `BKA_LLM_API_KEY` environment-only, optional, unset; no key wired in; no live call | ✅ Verified by hand and by test; nothing hardcoded anywhere |
| 6. AST guard **narrowed, not deleted**; seam modules vendor-free; only adapters exempt | ✅ Explicit two-name allow-list, everything else default-denied |
| 6b. Test that `mock` is still the default when `BKA_LLM_PROVIDER` is unset | ✅ `test_mock_is_the_default_provider_when_the_env_var_is_unset` |
| 7. Adapter tests offline; SDK/HTTP mocked; no paid call in CI or here | ✅ 99 tests, fake client injected throughout |
| 8. Guide §20.6 — why two adapters, what/why/rejected | ✅ §20.6, plus §20.7–§20.9 |
| 9. Handover updated, decision recorded as previously deferred → resolved | ✅ *Stage 5 decision* near the top, written **before** any code |
| 10. STAGE COMPLETE report, then STOP | ✅ Below |

---

### Result (Stage 5 — Checkpoint A, for reference)

**489 passed, 0 failed** (385 from Stages 1–4, **104 new**). Runtime ~51 s.
`ruff check .` → *All checks passed!*
`mypy` (strict) → *Success: no issues found in 35 source files*

> ⚠️ **Context this was measured in** (Problems §15 lesson, applied again): run inside
> the Claude Code session, which is **elevated**. `--basetemp=.pytest_tmp` means a
> non-elevated run should behave identically, but the user should confirm 489 passed in
> their own shell before approving.

| Checkpoint A test file | Tests | Covers |
|---|---|---|
| `tests/test_agent.py` | 77 | **The policy** — every seed question retrieves; six no-searchable-content inputs do not; a one-character question still retrieves; blank raises; and the two cases a keyword classifier would get wrong are asserted as passing. **The wiring** — the question reaches the retriever verbatim; one question is exactly one retrieval and one generation; the passages reach the prompt and the knowledge base does not; the agent adds no prompt of its own. **Both refusal routes** — after searching and without searching — producing the identical sentence with **zero** provider calls, and the no-search route making zero *retriever* calls too. **The record** — chunks used never exceeds chunks returned, documents deduplicated, and the summary asserted to contain no passage text. **Errors** — timeout, rate limit, malformed and truncated all propagate; a broken retriever propagates. **The boundary** — no tools, no history, the `DecisionReason` literal pinned to its two Stage 5 values, and an AST walk over `app/agent/` asserting no vendor SDK |
| `tests/test_agent_integration.py` | 27 | **Real model, real corpus.** Each of the five seed questions is answered from its own document, cites that document, and scores > 0.5; all five retrieve and generate. Three off-topic controls are refused *after* being searched, with a provider call count of 0 — the agent does not pre-judge relevance, the calibrated floor does. Two paraphrases with no shared vocabulary still find the right document. One module-scoped index shared across the file; a fresh mock provider per test so call counts stay meaningful (227 s → 18 s) |

### Commands used (Checkpoint A)

```bash
./.venv/Scripts/python.exe -m pytest                          # 489 passed, ~51 s
./.venv/Scripts/python.exe -m pytest tests/test_agent.py      # 77 passed, ~5 s
./.venv/Scripts/python.exe -m pytest tests/test_agent_integration.py  # 27, ~18 s
./.venv/Scripts/python.exe -m ruff check .                    # All checks passed!
./.venv/Scripts/python.exe -m mypy                            # 35 source files

./.venv/Scripts/python.exe -m app.agent demo
./.venv/Scripts/python.exe -m app.agent ask "Why would an ATM transaction fail after card authentication?"
```

### Measured results worth keeping (Checkpoint A)

```
python -m app.agent demo   (real corpus, real embedding model, mock provider)

  seed question                            passages  top score  document (rank 1)
  ATM fail after card auth                  5 / 115    0.790     atm-transaction-lifecycle
  what component handles card auth          5 / 115    0.804     card-authentication
  which API for payment authorisation       5 / 115    0.784     payment-authorisation-api
  troubleshoot a failed cash withdrawal     5 / 115    0.819     atm-cash-withdrawal-troubleshooting
  what config controls transaction limits   5 / 115    0.775     transaction-limits-configuration

  controls
  "What is the capital of France?"   0 / 115 cleared 0.25
                                     REFUSED after searching · provider calls 0
  "!!! ???"                          retrieval not performed
                                     REFUSED without searching · provider calls 0

Note: the card-authentication question cites card-pin-verification at [5] as well —
correct, and visible because the summary deduplicates documents rather than passages.
```

### Checkpoint A required coverage (`prompt.md` §13)

| Requirement | Status |
|---|---|
| Receive a technical question | ✅ `KnowledgeAgent.ask` |
| Determine whether knowledge retrieval is required | ✅ `app/agent/policy.py` → `RetrievalDecision`, returned to the caller. Reasoning and rejected alternatives in guide §20.5.1 |
| Retrieve relevant information | ✅ Stage 3's `Retriever`, injected |
| Pass context to the LLM | ✅ Stage 4's `LLMService`, unchanged |
| Produce a source-backed answer | ✅ `AgentAnswer.sources` + `chunks_used` + prompt version |
| Clearly indicate when information is insufficient | ✅ Two routes, one fixed sentence, both asserted identical |
| Must avoid inventing technical facts | ✅ Three enforcement points: score floor (S3), no-evidence-no-call (S4), system prompt (S4). None is a prompt instruction alone |
| Five example questions | ✅ Worked examples in the CLI demo, the guide §7, the README, and asserted in both test files |
| Agent tests | ✅ 104 new tests, offline, deterministic, free |
| Handover updated | ✅ This file, continuously — the provider decision was written **before** any code |
| Architecture guide §7 + §20.5 | ✅ §7 rewritten as BUILT; §20.5 = five records in the what/why/rejected form |

---

### Result (Stage 4, for reference)

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

**None.** The provider question that blocked Stage 5 was answered on 2026-09-10 and is
recorded under *Stage 5 decision* near the top of this file.

The only thing outstanding is **approval of Checkpoint A**, which is a stop in the
workflow, not an open question.

Decisions already taken with the user's explicit answer:

1. **The embedding model** (Stage 3) — local `sentence-transformers` /
   `all-MiniLM-L6-v2`, chosen over a lexical embedder or a paid hosted API.
2. **The LLM provider** (Stage 4) — **no concrete provider this stage; build and test
   against a mock only. The real adapter and any live key are deferred to a decision
   before Stage 5.** Full record in *Next Action → Decision taken before Stage 4
   implementation begins*. Superseded an earlier instruction in the same session
   (Problems §16).
3. **The concrete provider** (Stage 5, 2026-09-10) — **two adapters, Anthropic and
   OpenAI; no vendor exclusively chosen; default stays `mock`; no live key and no live
   call.** Full record in *Stage 5 decision* near the top of this file. It reverses a
   Stage 4 rejected alternative, and says why.
4. **Stage 5 is split into two approval checkpoints** (2026-09-10) — A: the agent, tested
   against the mock only; B: the two adapters. B does not begin until A is approved.

### Assumptions added in Stage 4

- `@traced` is applied to the public functions of the LLM layer. Deliberate exceptions,
  consistent with Stage 3: Pydantic property accessors on the models, and the private
  helpers `prompts._attribute` / `prompts._fence_safe` and `mock._build` /
  `_next_scripted` / `_synthesise`, which run inside an already-traced call.
- The mock's token counts are a crude `len(text) // 4` estimate, named as an estimate in
  the source. They exist so usage accounting is exercised end to end, not to be accurate.

### Security check (Stage 5 — Checkpoint B)

⚠️ **The "no code path can make a paid call" property is deliberately gone.** Two real
adapters exist now. It is replaced by four independent guards, all tested:
✅ **`BKA_LLM_PROVIDER` still defaults to `mock`** — asserted by a test that clears the
environment variable first. This is the guard that does not depend on the environment.
✅ **Neither adapter can be constructed without `BKA_LLM_API_KEY`** — it raises before an
SDK client object exists, and it does **not** fall through to `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY`, which both SDKs would read silently. That fall-through would turn a
forgotten setting into a working, billing configuration.
✅ **Every adapter test injects a fake client.** The test settings carry no key, so a test
that forgot would fail rather than reach the internet.
✅ **Both CLIs refuse a multi-question `demo` against a paid provider** without `--paid`,
checking *before* an index or a client is built. Verified by hand and by test.
✅ **No key anywhere.** No `sk-`/`sk-ant-` prefixes, no `.env`, nothing hardcoded. The one
secret-shaped literal in the suite is the synthetic `"not-a-real-key-for-tests"`, which
exists so a test can assert a 401 message does **not** contain it.
✅ **The no-vendor AST guard survives, narrowed.** Seam modules stay vendor-free by an
explicit two-name allow-list; `app/agent/` is guarded whole.
✅ **Neither adapter hardcodes a URL** — asserted by test. Endpoints come from the SDKs.
✅ **Adapter logs record shape and cost only** — model, stop reason, token counts. Never
the prompt or the answer, both of which embed document text.
✅ **No live API call has been made**, in the suite or by hand.

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
| **Stage 4 docs commit** | `9a0b462` — `docs(stage-4): record commit hash and push result in handover` |
| **Stage 5 Checkpoint A commit** | `1478631` — `feat(stage-5a): knowledge agent - decide, retrieve, ground, answer` |
| **Stage 5 Checkpoint B commit** | ⏳ **not created** — awaiting the user's approval |
| **Push status** | ✅ `origin/main == 1478631` (Checkpoint A); Checkpoint B unpushed |
| **Working tree** | 15 uncommitted Checkpoint B paths (listed below), plus git-ignored local files |
| **Committed in Checkpoint A** | 12 files: 8 added, 4 modified — 2,199 insertions, 159 deletions |
| **Committed in Stage 4** | 18 files: 11 added, 7 modified — 3,574 insertions, 205 deletions |
| **Committed in Stage 3** | 21 files: 13 added, 8 modified — 4,816 insertions, 302 deletions |
| **Deliberately not committed** | `prompt.md`, `prompt1.md`, `ccp.txt`, `docs/decisions/auto-changes.log`, `.venv/`, `logs/`, `data/vectorstore/`, `.pytest_tmp/`, caches |

### The exact Stage 5 Checkpoint B file set — verified with `git add -An`, 2026-09-10

15 paths, and **no others**. `data/vectorstore/`, `logs/`, `.venv/`, `.pytest_tmp/`,
`prompt.md`, `prompt1.md` and `ccp.txt` are all absent from the listing.

```
add '.env.example'                    add 'app/llm/anthropic_provider.py'
add 'README.md'                       add 'app/llm/openai_provider.py'
add 'app/agent/__main__.py'           add 'tests/test_llm_adapters.py'
add 'app/core/config.py'
add 'app/llm/__init__.py'             add 'app/llm/base.py'
add 'app/llm/__main__.py'             add 'app/llm/factory.py'
add 'docs/HANDOVER.md'                add 'requirements.txt'
add 'docs/architecture-guide.html'    add 'tests/test_llm_provider.py'
```

**Secret scan.** No vendor key prefixes (`sk-`, `sk-ant-`), no base64/hex literals over
40 characters, no card-number-shaped digit runs, no `.env` file. **One deliberate hit,
reviewed and kept:** `tests/test_llm_adapters.py:158` assigns
`llm_api_key = "not-a-real-key-for-tests"`. It is a synthetic, self-labelling placeholder
whose only purpose is the test asserting that a 401 error message cannot echo the key —
the test would be meaningless without a value to look for. **Git locks:** none; no
`git.exe` running. **No nested `banking-knowledge-agent/` directory.**

### The exact Stage 5 Checkpoint A file set — verified with `git add -An`, 2026-09-10

12 paths, and **no others**. `data/vectorstore/`, `logs/`, `.venv/`, `.pytest_tmp/`,
`prompt.md`, `prompt1.md` and `ccp.txt` are all absent from the listing, confirmed by
reading it rather than by assuming.

```
add 'README.md'                       add 'app/agent/__init__.py'
add 'docs/HANDOVER.md'                add 'app/agent/__main__.py'
add 'docs/architecture-guide.html'    add 'app/agent/agent.py'
add 'tests/conftest.py'               add 'app/agent/factory.py'
                                      add 'app/agent/models.py'
add 'tests/test_agent.py'             add 'app/agent/policy.py'
add 'tests/test_agent_integration.py'
```

**Secret scan of the new files:** no secret-shaped assignments, no base64/hex literals
over 40 characters, no card-number-shaped digit runs. **Git locks:** none; no `git.exe`
running.

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

**STOP. Stage 5 Checkpoint B is implemented, tested and documented, and is waiting for
the user's explicit approval.** Nothing from Checkpoint B is committed or pushed.

### On approval of Checkpoint B, in this order

1. Re-run `pytest` (expect 601), `ruff check .`, `mypy` (expect 37 source files).
2. Run the pre-commit checklist in the *Git* section below — `git add -An` first, and
   confirm `data/vectorstore/`, `logs/`, `.venv/`, `.pytest_tmp/`, `prompt.md`,
   `prompt1.md`, `ccp.txt` are absent from the list. Scan the new files for
   secret-shaped values with particular care this time: two files now legitimately
   contain the words "api_key".
3. Commit the Checkpoint B set, push, verify `origin/main == HEAD`, record the hash here.
4. **Then Stage 5 is complete.** Do not continue automatically into Stage 6 — wait for
   the user to start it.

### Stage 6 scope, for when it is started (`prompt.md` §14)

MCP tools: synthetic banking support tools (system configuration, transaction status,
component status, error-code lookup, system version, service health), synthetic data
only, with knowledge retrieval kept clearly separate from live/tool information. Two
things Stage 5 leaves ready for it:

- `DecisionReason` in `app/agent/models.py` is the literal Stage 6 extends when the agent
  gains a second real branch. Guide §20.5.1 records why it has only two values today.
- Tool results are untrusted input in exactly the way retrieved documents are. The
  fencing and escaping in `app/llm/prompts.py` were built for documents; Stage 6 should
  extend the same treatment rather than inventing a second scheme.

> ⚠️ **The two adapters still do not authorise a live call.** A real LLM call is a paid
> call and needs the user's explicit confirmation, given separately at the time. The
> repository is in a state where cloning it and running the suite costs nothing, and that
> property should be preserved.

### Decision taken before Stage 4 implementation begins — LLM provider

**Decided by the user, 2026-09-09.** Kept as the historical record of Stage 4.

> ✅ **The deferral this record created is now resolved** — see *Stage 5 decision* near
> the top of this file: two adapters, no vendor exclusively chosen, no live key, default
> stays `mock`.

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
