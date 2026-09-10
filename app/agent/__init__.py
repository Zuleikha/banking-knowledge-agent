"""The knowledge agent: the first component that owns a complete request.

Stage 5 joins the two halves built in isolation before it::

    question
       │
       ▼  policy      does this question require knowledge retrieval?
       │
       ▼  retriever   Stage 3 — question -> embedding -> search -> passages
       │
       ▼  LLMService  Stage 4 — budget, fence, generate, validate
       │
    AgentAnswer       answer + sources + decision + retrieval record

Two properties are the point of this package:

**It adds a seam, not a layer of logic.** The retriever still has no LLM
dependency and the LLM service still does not retrieve. Everything the agent
knows is *which* of them to call and in what order, which is why the whole
routing rule fits in one readable function in :mod:`app.agent.policy`.

**There is exactly one way to refuse.** A question the agent declines to search
is routed through Stage 4's existing empty-evidence guard rather than getting a
refusal of its own, so the insufficient-evidence sentence has a single
definition — the one the API, the web interface and the evaluation harness all
match against.
"""

from __future__ import annotations

from app.agent.agent import KnowledgeAgent
from app.agent.factory import get_agent
from app.agent.models import (
    AgentAnswer,
    DecisionReason,
    RetrievalDecision,
    RetrievalSummary,
)
from app.agent.policy import decide_retrieval

__all__ = [
    "AgentAnswer",
    "DecisionReason",
    "KnowledgeAgent",
    "RetrievalDecision",
    "RetrievalSummary",
    "decide_retrieval",
    "get_agent",
]
