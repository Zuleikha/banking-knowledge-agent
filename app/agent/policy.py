"""The agent's routing decision: does this question require knowledge retrieval?

``prompt.md`` §13 requires the agent to *determine whether knowledge retrieval is
required*. This module is that determination, isolated from the agent so it can
be read, tested and replaced on its own.

**Stage 5 has one substantive branch, and that is the honest answer.** Retrieval
is the only evidence this agent has. It holds no tools yet — those arrive in
Stage 6 — and its own parametric knowledge is explicitly disqualified as a source
by the system prompt. So for any question with something to search for, the
answer to "is retrieval required?" is yes, and a second branch would be fiction.

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

from app.agent.models import RetrievalDecision
from app.core.tracing import traced

SEARCHABLE_MINIMUM = 1
"""Alphanumeric characters a question needs before searching is worth doing."""


@traced
def decide_retrieval(question: str) -> RetrievalDecision:
    """Decide whether ``question`` should be answered from the knowledge base.

    Args:
        question: The user's question. Must not be blank.

    Returns:
        The decision, carrying the rule that produced it and a sentence
        explaining it that is safe to display.

    Raises:
        ValueError: If the question is blank. A blank question is not a routing
            outcome — there is nothing to route — so it fails at the boundary
            rather than becoming a refusal that looks like a considered answer.
    """
    if not question.strip():
        raise ValueError("Cannot decide retrieval for an empty question.")

    if sum(character.isalnum() for character in question) < SEARCHABLE_MINIMUM:
        return RetrievalDecision(
            retrieve=False,
            reason="no_searchable_content",
            explanation=(
                "The question contains no searchable words, so the knowledge "
                "base was not searched."
            ),
        )

    return RetrievalDecision(
        retrieve=True,
        reason="knowledge_required",
        explanation=(
            "Answers must be grounded in the documentation, so the knowledge "
            "base was searched for supporting passages."
        ),
    )
