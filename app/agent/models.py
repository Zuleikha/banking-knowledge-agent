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
from app.mcp.models import ToolInvocation, ToolResult
from app.rag.models import RetrievalResult

DecisionReason = Literal[
    "knowledge_required",
    "knowledge_and_live_status_required",
    "no_searchable_content",
]
"""Why the agent searched, called tools, or did neither.

Stage 5 had two values. Stage 6 **extends this literal** — as Stage 5's own
docstring said it would — rather than introducing a parallel tool-decision type.
One question produces one routing decision; two decision objects would be two
things that must agree about the same question, and the day they disagreed
neither would be wrong on its own terms.

The new value is ``knowledge_and_live_status_required``: the question names
something a tool can look up, so the agent does both.

**There is deliberately no tool-only value**, and the omission is the same kind
of honesty as Stage 5's refusal to invent a topic classifier. A live reading is
close to useless without the documentation that gives it meaning: knowing that
``limits.atm.per_transaction_amount`` is effectively ``250.00`` only becomes an
answer alongside the documented default of ``500.00`` and the explanation of what
the key controls. Adding a branch that skips retrieval would save one cheap
in-process search and cost the model the vocabulary it needs to interpret what
the tool said. Stage 7 introduces genuine either/or selection, at which point
that branch will be a real choice rather than a worse version of this one.
"""


class AgentDecision(BaseModel):
    """The agent's routing decision for one question: search, tools, or neither.

    Recorded even when the answer is a refusal, because *why* the agent did not
    search is a different diagnosis from *what* the search failed to find.

    Renamed from ``RetrievalDecision`` in Stage 6, when it stopped being only
    about retrieval. :data:`RetrievalDecision` remains as an alias so that
    nothing written against the Stage 5 name has to change.
    """

    model_config = ConfigDict(frozen=True)

    retrieve: bool = Field(description="Whether the knowledge base was searched.")
    tools: tuple[ToolInvocation, ...] = Field(
        default=(),
        description="Tool calls the agent decided to make, in call order.",
    )
    reason: DecisionReason = Field(description="The rule that produced this decision.")
    explanation: str = Field(
        min_length=1,
        description="One sentence a human can read, safe to show in a UI or a log.",
    )

    @property
    def uses_tools(self) -> bool:
        """Whether this decision calls at least one tool."""
        return bool(self.tools)


RetrievalDecision = AgentDecision
"""Stage 5's name for :class:`AgentDecision`.

Kept as an alias rather than removed. The rename is worth making — the object
decides more than retrieval now — but breaking every existing import to record
that would be a cost paid by readers of Stage 5's tests for no benefit to them.
"""


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


class ToolCallSummary(BaseModel):
    """What one tool call did, without its payload.

    The tool-layer counterpart of :class:`RetrievalSummary`, and split from
    :class:`~app.mcp.models.ToolResult` on the same *security* line: shape is
    safe to log, content is not. A tool payload in this project is synthetic, but
    the same tool pointed at a real system would return account identifiers,
    balances and terminal locations, and a summary that carried them would put
    them into every log line that recorded a request.

    The full results travel on :attr:`AgentAnswer.tool_results`, which is
    returned to the caller and never logged.

    **It deliberately carries no ``reason``.** The obvious design put the
    policy's explanation here — *"The question names the transaction reference
    TXN-20260911-004473"* — which is exactly the kind of sentence a UI wants and
    exactly the wrong thing to put in an object whose whole promise is that it is
    safe to log: the explanation names the identifier the argument list was
    careful to omit. A test caught it. The reason lives on
    :attr:`AgentDecision.tools`, which is returned and displayed but never
    written to a log line.
    """

    model_config = ConfigDict(frozen=True)

    tool: str = Field(min_length=1, description="Which tool was called.")
    ok: bool = Field(description="Whether the tool found what was asked for.")
    arguments: tuple[str, ...] = Field(
        default=(),
        description="Argument NAMES supplied. Values are deliberately absent.",
    )
    error_code: str | None = Field(
        default=None, description="Stable failure code when ok is False."
    )
    fields: int = Field(
        default=0, ge=0, description="How many fields the payload carried."
    )

    @classmethod
    def from_call(
        cls, invocation: ToolInvocation, result: ToolResult
    ) -> ToolCallSummary:
        """Summarise one completed call, dropping every argument value."""
        return cls(
            tool=result.tool,
            ok=result.ok,
            arguments=tuple(sorted(invocation.arguments)),
            error_code=result.error_code,
            fields=len(result.data),
        )


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
    decision: AgentDecision = Field(description="The routing decision taken.")
    retrieval: RetrievalSummary = Field(description="What retrieval considered.")
    tools: tuple[ToolCallSummary, ...] = Field(
        default=(),
        description="Shape of each tool call. Safe to log; carries no payload.",
    )
    tool_results: tuple[ToolResult, ...] = Field(
        default=(),
        description="Full tool results, for display. Returned, never logged.",
    )
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

    @property
    def tools_used(self) -> int:
        """Live tool results placed in the prompt."""
        return self.answer.tools_used

    @property
    def used_live_information(self) -> bool:
        """Whether any part of this answer came from a tool rather than a document.

        The question ``prompt.md`` §14 requires a reader to be able to answer,
        exposed as one boolean so a Stage 9 interface does not have to infer it.
        """
        return bool(self.tool_results)
