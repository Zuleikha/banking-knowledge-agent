"""The application-facing LLM service: retrieved context in, grounded answer out.

``LLMService`` is the only thing above this package that callers need. It owns
the sequence that turns evidence into an answer::

    question + RetrievalResult
        -> select_context   (apply the context budget)
        -> build_request    (frozen system prompt + fenced passages + question)
        -> provider.complete
        -> validate         (truncation, refusal, empty body)
        -> GroundedAnswer   (text + sources + provenance)

**What it deliberately does not do.** It does not retrieve. It is handed a
:class:`~app.rag.models.RetrievalResult` that someone else produced. Deciding
*whether* to retrieve, reformulating a question, choosing tools and running the
agent loop are Stage 5 and Stage 7; putting any of that here would make this
class the agent under a different name and leave the seam untested.

**Why an empty retrieval short-circuits.** When retrieval returns nothing, this
service answers with :data:`~app.llm.prompts.INSUFFICIENT_EVIDENCE` and does not
call the provider. A generation request with zero evidence has exactly two
possible outcomes — a refusal, or an answer invented from the model's own
training — and one of those is the failure mode this entire architecture exists
to prevent. Not sending it is cheaper, faster, deterministic, and removes the
only path by which an ungrounded answer could be produced. Stage 5's agent
builds its decision logic on top of this guard; it does not replace it.

**Failures are raised, never returned as text.** A truncated or refused
generation is not quietly handed back as an answer. It raises, because a
half-finished sentence about a transaction limit is more dangerous than an
error: it looks complete.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.tracing import traced
from app.llm.base import (
    LLMError,
    LLMProvider,
    LLMProviderError,
    LLMRefusalError,
    LLMResponseError,
)
from app.llm.models import CompletionRequest, GroundedAnswer, LLMResponse
from app.llm.prompts import (
    INSUFFICIENT_EVIDENCE,
    SYSTEM_PROMPT_VERSION,
    build_request,
    select_context,
)
from app.rag.models import RetrievalResult

logger = get_logger(__name__)


class LLMService:
    """Generates source-backed answers from retrieved context.

    The provider is injected as a protocol, exactly as the retriever's embedder
    and store are. Swapping a mock for a real adapter is a constructor argument,
    not a change to this class or to anything that calls it.
    """

    def __init__(
        self,
        provider: LLMProvider,
        settings: Settings | None = None,
    ) -> None:
        """Wire the service to a provider.

        Args:
            provider: The model implementation to generate with.
            settings: Application settings. Defaults to the cached singleton.
        """
        self._provider = provider
        self._settings = settings or get_settings()

    @property
    def provider(self) -> LLMProvider:
        """The provider answering requests."""
        return self._provider

    @traced
    def answer(self, question: str, retrieval: RetrievalResult) -> GroundedAnswer:
        """Answer ``question`` using only the passages in ``retrieval``.

        Args:
            question: The user's question, in natural language.
            retrieval: Evidence gathered by the RAG layer. An empty result is a
                valid input and produces an honest refusal.

        Returns:
            The answer together with its sources and provenance.

        Raises:
            ValueError: If the question is blank.
            LLMResponseError: If the generation was truncated or empty.
            LLMRefusalError: If the model declined to answer.
            LLMError: For any other provider failure; the concrete subclass says
                whether a retry is worthwhile.
        """
        if not question.strip():
            raise ValueError("Cannot answer an empty question.")

        selected = select_context(retrieval, self._settings)
        if not selected:
            return self._refuse(question, retrieval)

        request = build_request(question, selected, self._settings)
        response = self._complete(request)
        self._validate(response)

        sources = tuple(scored.chunk.citation for scored in selected)
        answer = GroundedAnswer(
            question=question,
            text=response.text,
            sources=sources,
            chunks_used=len(selected),
            chunks_available=len(retrieval.chunks),
            refused=False,
            llm_called=True,
            response=response,
            prompt_version=SYSTEM_PROMPT_VERSION,
        )
        logger.info(
            "llm.answered",
            # Neither the prompt nor the answer text is logged: both embed
            # document content, and Stage 10 decides deliberately what a request
            # record contains. Shape, cost and provenance only.
            provider=response.provider_id,
            model=response.model_id,
            prompt_version=SYSTEM_PROMPT_VERSION,
            chunks_used=answer.chunks_used,
            chunks_available=answer.chunks_available,
            sources=len(sources),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
        )
        return answer

    def _refuse(self, question: str, retrieval: RetrievalResult) -> GroundedAnswer:
        """Answer with the fixed insufficient-evidence sentence. No model call."""
        logger.info(
            "llm.refused_no_context",
            candidates=retrieval.candidates_considered,
            min_score=retrieval.min_score,
            top_score=retrieval.top_score,
        )
        return GroundedAnswer(
            question=question,
            text=INSUFFICIENT_EVIDENCE,
            sources=(),
            chunks_used=0,
            chunks_available=len(retrieval.chunks),
            refused=True,
            llm_called=False,
            response=None,
            prompt_version=SYSTEM_PROMPT_VERSION,
        )

    def _complete(self, request: CompletionRequest) -> LLMResponse:
        """Call the provider, guaranteeing only :class:`LLMError` escapes.

        A provider that raises something untyped has a gap in its translation
        table. Wrapping it here keeps a raw SDK exception from reaching the API
        layer -- where it would be reported as a generic 500 with a vendor's
        wording -- while still failing loudly and preserving the cause.
        """
        try:
            return self._provider.complete(request)
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001 - re-raised as a typed error
            raise LLMProviderError(
                f"Provider '{getattr(self._provider, 'provider_id', 'unknown')}' "
                f"raised an untranslated {type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _validate(response: LLMResponse) -> None:
        """Reject a generation that must not be shown as an answer.

        Raises:
            LLMRefusalError: If the model declined.
            LLMResponseError: If the generation was truncated or empty.
        """
        if response.stop_reason == "refusal":
            raise LLMRefusalError(
                f"Model '{response.model_id}' declined to answer the question."
            )
        if response.stop_reason == "max_tokens":
            raise LLMResponseError(
                f"Model '{response.model_id}' hit the token ceiling and the "
                "answer is truncated. A truncated answer is withheld rather "
                "than shown, because it reads as complete."
            )
        if not response.text.strip():
            raise LLMResponseError(
                f"Model '{response.model_id}' returned an empty response "
                f"(stop_reason={response.stop_reason})."
            )
