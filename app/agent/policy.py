"""The agent's routing decision: does this question require knowledge retrieval?

``prompt.md`` §13 requires the agent to *determine whether knowledge retrieval is
required*. This module is that determination, isolated from the agent so it can
be read, tested and replaced on its own.

**Stage 6 update: there is now a second substantive branch, and it is real.**
The agent holds six MCP tools, so a question can require documentation *and* a
live reading. The retrieval half of the decision is unchanged — every question
with something to search for still searches, for the reasons below — and
:mod:`app.agent.tool_policy` decides the tool half. What follows is Stage 5's
reasoning, preserved because it is still why retrieval has no classifier in front
of it.

**Retrieval has one substantive branch, and that is the honest answer.**
Retrieval is the agent's baseline evidence: its own parametric knowledge is
explicitly disqualified as a source by the system prompt, and a live tool reading
needs documentation alongside it to be interpretable. So for any question with
something to search for, the answer to "is retrieval required?" is yes, and a
branch that skipped it would be fiction.

What the policy does decide is the case where searching is *pointless*: a
question with no searchable content at all. ``"!!! ???"`` is a real input a web
form will produce. Embedding it yields a vector with no meaning, the score floor
rejects everything, and the outcome is a refusal either way — so the policy
skips the search and says why, which is both cheaper and a more precise
diagnosis than "searched 115 passages, found nothing".

**Why not a keyword or topic classifier.** The tempting version routes on
banking vocabulary: *"contains 'ATM' or 'card' → retrieve"*. It fails in both
directions. *"Why did the withdrawal reverse?"* contains no listed keyword and
would skip retrieval that would have succeeded; *"what is a payment in cricket?"*
contains one and would retrieve regardless. A keyword list is a guess about the
corpus wearing the costume of a decision — and the score floor already answers
the relevance question properly, with measured evidence behind the number
(``python -m app.rag calibrate``).

**Why not ask an LLM to route.** An LLM router costs a model call per question to
decide something a single branch already answers correctly, and it makes the
routing non-deterministic and untestable offline. When Stage 7 introduces a real
choice — knowledge, tool, both, or neither — that trade-off is worth revisiting
against actual alternatives. It is not worth it to choose between one option and
itself.
"""

from __future__ import annotations

from app.agent.models import AgentDecision
from app.agent.tool_policy import select_tools
from app.core.tracing import traced

SEARCHABLE_MINIMUM = 1
"""Alphanumeric characters a question needs before searching is worth doing."""


@traced
def decide(question: str) -> AgentDecision:
    """Decide how ``question`` should be answered: search, tools, or neither.

    Stage 6's version of the Stage 5 function. Retrieval is decided exactly as
    before — the reasoning above is unchanged — and then
    :func:`app.agent.tool_policy.select_tools` is asked whether the question also
    names anything a tool can act on.

    The order matters and is not arbitrary. A question with no searchable content
    has nothing for a tool to act on either, so it short-circuits before tool
    selection runs. Everything else retrieves, and may additionally call tools.

    Args:
        question: The user's question. Must not be blank.

    Returns:
        The decision, carrying the rule that produced it, any tool calls to make,
        and a sentence explaining it that is safe to display.

    Raises:
        ValueError: If the question is blank. A blank question is not a routing
            outcome — there is nothing to route — so it fails at the boundary
            rather than becoming a refusal that looks like a considered answer.
    """
    if not question.strip():
        raise ValueError("Cannot decide retrieval for an empty question.")

    if sum(character.isalnum() for character in question) < SEARCHABLE_MINIMUM:
        return AgentDecision(
            retrieve=False,
            tools=(),
            reason="no_searchable_content",
            explanation=(
                "The question contains no searchable words, so the knowledge "
                "base was not searched."
            ),
        )

    tools = select_tools(question)
    if tools:
        named = ", ".join(sorted({invocation.tool for invocation in tools}))
        return AgentDecision(
            retrieve=True,
            tools=tools,
            reason="knowledge_and_live_status_required",
            explanation=(
                "The question names something a support tool can look up, so "
                "the knowledge base was searched for background and the live "
                f"system was queried through: {named}."
            ),
        )

    return AgentDecision(
        retrieve=True,
        tools=(),
        reason="knowledge_required",
        explanation=(
            "Answers must be grounded in the documentation, so the knowledge "
            "base was searched for supporting passages."
        ),
    )


@traced
def decide_retrieval(question: str) -> AgentDecision:
    """Stage 5's name for :func:`decide`.

    Retained so that Stage 5's tests and any caller written against the older
    name keep working. New code should call :func:`decide`, which is what the
    function has actually done since tools arrived.
    """
    return decide(question)
