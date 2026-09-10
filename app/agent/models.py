"""Data contracts for the knowledge agent.

Three types, describing the three things an agent run produces::

    question  --policy-->     RetrievalDecision   was retrieval required, and why
    decision  --retriever-->  RetrievalSummary    what the search actually found
    both      --service-->    AgentAnswer         the answer, plus that whole record

``AgentAnswer`` wraps rather than replaces
:class:`~app.llm.models.GroundedAnswer`. The LLM layer's contract stays the LLM
layer's; the agent adds the *execution record* on top of it. Flattening the two
would have put agent concerns — which route was taken, what retrieval considered
— into a model that the LLM layer owns and that knows nothing about routing.

**Why the execution record is a first-class value rather than a log line.**
``prompt.md`` §15 requires the API and the web interface to show what actually
happened: retrieval performed, documents used, tools called, final answer. If
that information only exists in ``logs/app.log``, Stage 9 has to scrape its own
logs to render a page. Returning it means the agent's decisions are assertable in
a test and displayable in a UI without either party parsing prose.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.models import GroundedAnswer
from app.rag.models import RetrievalResult

DecisionReason = Literal["knowledge_required", "no_searchable_content"]
"""Why the agent did or did not search the knowledge base.

Stage 5 has exactly two values, and that is deliberate — see
``app/agent/policy.py`` for why inventing a topic classifier here would have been
a guess dressed as a decision. Stage 6 adds tool routing and Stage 7 adds the
remaining branches; both extend this literal rather than introducing the concept.
"""


class RetrievalDecision(BaseModel):
    """The agent's routing decision for one question.

    Recorded even when the answer is a refusal, because *why* the agent did not
    search is a different diagnosis from *what* the search failed to find.
    """

    model_config = ConfigDict(frozen=True)

    retrieve: bool = Field(description="Whether the knowledge base was searched.")
    reason: DecisionReason = Field(description="The rule that produced this decision.")
    explanation: str = Field(
        min_length=1,
        description="One sentence a human can read, safe to show in a UI or a log.",
    )


class RetrievalSummary(BaseModel):
    """What the retrieval step considered and returned.

    Kept separate from the chunks themselves so a caller can show *"searched 115
    passages, none cleared 0.25"* without holding, serialising or rendering the
    document text. That distinction matters from Stage 9 onward: the summary is
    safe to display and to log; the passages are document content and are not.
    """

    model_config = ConfigDict(frozen=True)

    performed: bool = Field(description="Whether a search was actually run.")
    candidates_considered: int = Field(
        default=0, ge=0, description="Passages the store scored before the floor."
    )
    chunks_returned: int = Field(
        default=0, ge=0, description="Passages that cleared the floor."
    )
    top_score: float | None = Field(
        default=None, description="Best cosine score, or None when nothing matched."
    )
    min_score: float | None = Field(
        default=None, description="Floor applied, or None when no search was run."
    )
    documents: tuple[str, ...] = Field(
        default=(),
        description="Distinct document ids behind the matches, best-match order.",
    )

    @classmethod
    def from_result(cls, result: RetrievalResult) -> RetrievalSummary:
        """Summarise a completed retrieval."""
        seen: dict[str, None] = {}
        for scored in result.chunks:
            seen.setdefault(scored.chunk.document_id, None)
        return cls(
            performed=True,
            candidates_considered=result.candidates_considered,
            chunks_returned=len(result.chunks),
            top_score=result.top_score,
            min_score=result.min_score,
            documents=tuple(seen),
        )

    @classmethod
    def not_performed(cls) -> RetrievalSummary:
        """Summarise a run in which the agent decided not to search."""
        return cls(performed=False)


class AgentAnswer(BaseModel):
    """An answer together with the complete record of how it was produced.

    A caller can tell these apart without reading the prose:

    * a **grounded answer** — :attr:`is_grounded`; a model was consulted and at
      least one retrieved passage was in front of it;
    * a **refusal after searching** — :attr:`refused` with
      ``retrieval.performed`` true; the corpus was searched and had nothing
      close enough;
    * a **refusal without searching** — :attr:`refused` with
      ``retrieval.performed`` false; the question had nothing to search for.

    All three are correct outcomes. Only the first is an answer.
    """

    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=1, description="The question that was asked.")
    text: str = Field(min_length=1, description="The answer shown to the user.")
    sources: tuple[str, ...] = Field(
        default=(), description="Citations for the passages placed in the prompt."
    )
    decision: RetrievalDecision = Field(description="The routing decision taken.")
    retrieval: RetrievalSummary = Field(description="What retrieval considered.")
    answer: GroundedAnswer = Field(
        description="The LLM layer's own result, unmodified, including provenance."
    )

    @property
    def refused(self) -> bool:
        """Whether the agent declined to answer for want of evidence."""
        return self.answer.refused

    @property
    def llm_called(self) -> bool:
        """Whether a model was actually consulted."""
        return self.answer.llm_called

    @property
    def is_grounded(self) -> bool:
        """Whether the answer was generated from at least one retrieved passage."""
        return self.answer.is_grounded

    @property
    def chunks_used(self) -> int:
        """Passages actually placed in the prompt."""
        return self.answer.chunks_used

    @property
    def prompt_version(self) -> str:
        """Version of the system instructions behind this answer."""
        return self.answer.prompt_version
