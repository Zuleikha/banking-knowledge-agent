"""The knowledge agent: a technical question in, a source-backed answer out.

This is the first component that owns a complete request. Stages 3 and 4 each
built one half and were deliberately kept ignorant of the other — the retriever
has no LLM dependency, and ``LLMService`` does not retrieve. The agent is the
seam between them, and it is a thin one on purpose::

    question
       │
       ▼  decide                    policy.py — search? tools? neither?
       │
       ├── retrieve = False ──▶  an empty RetrievalResult (no embedding, no search)
       └── retrieve = True  ──▶  Retriever.retrieve(question)          DOCUMENTATION
       │
       ├── tools = ()       ──▶  nothing called
       └── tools = (...)    ──▶  ToolRegistry.invoke_all(...)          LIVE READINGS
       │                              │
       │                              ├── get_system_configuration
       │                              ├── check_transaction_status
       │                              ├── get_component_status
       │                              ├── look_up_error_code
       │                              ├── retrieve_system_version
       │                              └── check_service_health
       │
       ▼  LLMService.answer(question, retrieval, tool_results)   ← Stage 4's guard
       │        no evidence of either kind  ──▶  refuse, ZERO provider calls
       ▼
    AgentAnswer     answer + sources + decision + retrieval record + tool record

That middle branch is ``prompt.md`` §14's *Agent → MCP → Tool → Result*. The two
kinds of evidence stay separate the whole way through: separate collection,
separate fences in the prompt, separate fields on the answer. A caller can always
ask :attr:`~app.agent.models.AgentAnswer.used_live_information` and get a
truthful yes or no.

**One refusal path, and it is Stage 4's.** When the agent decides not to search,
it does not write its own refusal. It builds an empty
:class:`~app.rag.models.RetrievalResult` and hands that to the service, which
takes the guard it already had: the fixed insufficient-evidence sentence, and no
model call. The alternative — a second refusal branch inside the agent — would
mean two places that must agree on what "insufficient" says, and the API, the web
interface and Stage 11's evaluation harness all detect refusals by that exact
sentence. Two sources for it is one too many.

**The agent does not soften failures.** A provider timeout, a rate limit or a
truncated generation raises out of here as the typed error the LLM layer defined.
Converting an infrastructure failure into "the knowledge base does not contain
enough information" would be a lie of exactly the kind this project exists to
prevent: the corpus is fine, the model is not, and those need different responses
from whoever is reading.
"""

from __future__ import annotations

from app.agent.models import (
    AgentAnswer,
    AgentDecision,
    RetrievalSummary,
    ToolCallSummary,
)
from app.agent.policy import decide
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.tracing import traced
from app.llm.service import LLMService
from app.mcp.models import ToolResult
from app.mcp.registry import ToolRegistry
from app.rag.models import RetrievalResult
from app.rag.retriever import Retriever

logger = get_logger(__name__)


class KnowledgeAgent:
    """Answers technical questions from the synthetic banking knowledge base.

    Both collaborators are injected, exactly as they are one layer down: the
    tests run this class with a hashing embedder and
    :class:`~app.llm.mock.MockLLMProvider`, and production passes a
    sentence-transformers retriever and whichever provider is configured.
    Neither this class nor its callers change between the two.
    """

    def __init__(
        self,
        retriever: Retriever,
        llm_service: LLMService,
        settings: Settings | None = None,
        tools: ToolRegistry | None = None,
    ) -> None:
        """Wire the agent to its knowledge source, its model and its tools.

        Args:
            retriever: The RAG layer, already indexed.
            llm_service: The generation layer, already bound to a provider.
            settings: Application settings. Defaults to the cached singleton.
            tools: The MCP tool registry. ``None`` means the agent has no tools
                and behaves exactly as it did in Stage 5 — which is what keeps
                every Stage 5 test meaningful rather than merely passing.

        Note:
            ``tools`` is last so that Stage 5 call sites passing ``settings``
            positionally keep working. Inserting it earlier would have silently
            rebound an argument at any call site not updated in the same commit.
        """
        self._retriever = retriever
        self._llm = llm_service
        self._settings = settings or get_settings()
        self._tools = tools

    @property
    def retriever(self) -> Retriever:
        """The knowledge source this agent searches."""
        return self._retriever

    @property
    def llm_service(self) -> LLMService:
        """The generation layer this agent answers through."""
        return self._llm

    @property
    def tools(self) -> ToolRegistry | None:
        """The tool registry this agent can call, if it has one."""
        return self._tools

    @traced
    def ask(self, question: str) -> AgentAnswer:
        """Answer one technical question, or say why it cannot be answered.

        Args:
            question: The question, in natural language.

        Returns:
            The answer together with the decision and retrieval record behind
            it. A refusal is a valid, successful return value — not an error.

        Raises:
            ValueError: If the question is blank.
            EmbeddingError: If the question cannot be embedded.
            LLMError: If the provider fails or returns an unusable generation.
                Deliberately propagated: a broken model is not the same
                situation as an undocumented answer.
        """
        if not question.strip():
            raise ValueError("Cannot answer an empty question.")

        decision = decide(question)
        retrieval = (
            self._retriever.retrieve(question)
            if decision.retrieve
            else self._no_evidence(question)
        )
        summary = (
            RetrievalSummary.from_result(retrieval)
            if decision.retrieve
            else RetrievalSummary.not_performed()
        )

        tool_results, tool_summaries = self._run_tools(decision)

        grounded = self._llm.answer(question, retrieval, tool_results)

        logger.info(
            "agent.answered",
            # The question, the passages, the tool payloads and the answer text
            # are all withheld here. The question is already recorded once by the
            # retriever (Stage 3, flagged for Stage 13); logging it again would
            # double the exposure for no extra diagnostic value, and the rest is
            # content. Route and shape only -- tool NAMES and argument NAMES are
            # shape, tool argument VALUES and payloads are not.
            decision=decision.reason,
            retrieval_performed=summary.performed,
            candidates=summary.candidates_considered,
            chunks_returned=summary.chunks_returned,
            chunks_used=grounded.chunks_used,
            top_score=summary.top_score,
            tools_called=len(tool_summaries),
            tools=[call.tool for call in tool_summaries],
            tools_found=[call.tool for call in tool_summaries if call.ok],
            refused=grounded.refused,
            llm_called=grounded.llm_called,
            documents=list(summary.documents),
        )

        return AgentAnswer(
            question=question,
            text=grounded.text,
            sources=grounded.sources,
            decision=decision,
            retrieval=summary,
            tools=tool_summaries,
            tool_results=tool_results,
            answer=grounded,
        )

    @traced
    def ask_many(self, questions: list[str]) -> tuple[AgentAnswer, ...]:
        """Answer several questions in order. Used by the CLI and by evaluation."""
        return tuple(self.ask(question) for question in questions)

    def _run_tools(
        self, decision: AgentDecision
    ) -> tuple[tuple[ToolResult, ...], tuple[ToolCallSummary, ...]]:
        """Execute the tool calls the decision asked for.

        Returns both the full results — which go into the prompt and back to the
        caller — and their summaries, which are what gets logged.

        **A tool failure is not softened, for the same reason an LLM failure is
        not.** If a registered tool raises, the :class:`~app.mcp.base.ToolError`
        propagates out of :meth:`ask`. Catching it and answering from
        documentation alone would produce a confident answer that silently
        omitted the live half of the evidence, and the reader would have no way
        to tell. "The status tool is broken" and "the documentation says X" are
        different answers and need different responses from whoever is reading.

        Note that a tool reporting ``ok=False`` is *not* a failure and does not
        raise: "no transaction has that reference" is a finding, and it is passed
        to the model to report.
        """
        if not decision.tools:
            return (), ()
        if self._tools is None:
            # The policy asked for a tool and the agent has no registry. That is
            # a composition error -- get_agent always supplies one -- and it must
            # be loud rather than silently degrading to a documentation-only
            # answer that looks complete.
            raise RuntimeError(
                f"The routing policy selected {len(decision.tools)} tool call(s), "
                "but this agent was built without a tool registry. Build it with "
                "app.agent.factory.get_agent(), or pass tools= explicitly."
            )

        results = self._tools.invoke_all(decision.tools)
        summaries = tuple(
            ToolCallSummary.from_call(invocation, result)
            for invocation, result in zip(decision.tools, results, strict=True)
        )
        return results, summaries

    def _no_evidence(self, question: str) -> RetrievalResult:
        """Build the empty result that routes a no-search question to the guard.

        Nothing was searched, so ``candidates_considered`` is 0 and
        ``min_score`` is the configured floor that was never applied. The object
        exists only to carry "there is no evidence" into the one component that
        knows what to do about it.
        """
        return RetrievalResult(
            query=question,
            chunks=(),
            candidates_considered=0,
            min_score=self._settings.retrieval_min_score,
        )
