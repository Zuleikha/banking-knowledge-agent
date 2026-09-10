"""The knowledge agent: a technical question in, a source-backed answer out.

This is the first component that owns a complete request. Stages 3 and 4 each
built one half and were deliberately kept ignorant of the other — the retriever
has no LLM dependency, and ``LLMService`` does not retrieve. The agent is the
seam between them, and it is a thin one on purpose::

    question
       │
       ▼  decide_retrieval          policy.py — was a search required?
       │
       ├── retrieve = False ──▶  an empty RetrievalResult (no embedding, no search)
       └── retrieve = True  ──▶  Retriever.retrieve(question)
       │
       ▼  LLMService.answer(question, retrieval)      ← Stage 4, unchanged
       │        empty evidence  ──▶  refuse, and make ZERO provider calls
       ▼
    AgentAnswer     answer + sources + decision + retrieval record

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

from app.agent.models import AgentAnswer, RetrievalSummary
from app.agent.policy import decide_retrieval
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.tracing import traced
from app.llm.service import LLMService
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
    ) -> None:
        """Wire the agent to its knowledge source and its model.

        Args:
            retriever: The RAG layer, already indexed.
            llm_service: The generation layer, already bound to a provider.
            settings: Application settings. Defaults to the cached singleton.
        """
        self._retriever = retriever
        self._llm = llm_service
        self._settings = settings or get_settings()

    @property
    def retriever(self) -> Retriever:
        """The knowledge source this agent searches."""
        return self._retriever

    @property
    def llm_service(self) -> LLMService:
        """The generation layer this agent answers through."""
        return self._llm

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

        decision = decide_retrieval(question)
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

        grounded = self._llm.answer(question, retrieval)

        logger.info(
            "agent.answered",
            # The question, the passages and the answer text are all withheld
            # here. The question is already recorded once by the retriever
            # (Stage 3, flagged for Stage 13); logging it again would double the
            # exposure for no extra diagnostic value, and the other two are
            # document content. Route and shape only.
            decision=decision.reason,
            retrieval_performed=summary.performed,
            candidates=summary.candidates_considered,
            chunks_returned=summary.chunks_returned,
            chunks_used=grounded.chunks_used,
            top_score=summary.top_score,
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
            answer=grounded,
        )

    @traced
    def ask_many(self, questions: list[str]) -> tuple[AgentAnswer, ...]:
        """Answer several questions in order. Used by the CLI and by evaluation."""
        return tuple(self.ask(question) for question in questions)

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
