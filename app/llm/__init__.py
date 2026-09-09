"""LLM abstraction: prompts, context injection, generation, error handling.

Stage 4 owns everything between retrieved evidence and an answer the application
is willing to show::

    RetrievalResult              (Stage 3)
        |
        v  prompts      budget the context, fence it, add the frozen system prompt
      CompletionRequest
        |
        v  base         LLMProvider protocol -- the vendor-agnostic seam
      LLMResponse
        |
        v  service      reject truncated / refused / empty generations
      GroundedAnswer    answer + sources + provenance

Three properties are the point of this package:

**No vendor above this line.** Nothing outside ``app/llm`` imports an SDK, names
a model, or catches a vendor's exception type. Swapping providers is a new module
plus one branch in :mod:`app.llm.factory`.

**The model sees retrieved context, never the knowledge base.** Fifteen documents
would fit in a prompt; that is exactly why the discipline is established now
rather than when it becomes unavoidable.

**No paid call exists.** Stage 4 ships one provider, :class:`MockLLMProvider`,
which is deterministic and in-process. The concrete adapter and any live API key
are a decision deferred to Stage 5, so the suite is offline and free by
construction rather than by discipline.
"""

from __future__ import annotations

from app.llm.base import (
    LLMConfigurationError,
    LLMError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMRefusalError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.llm.factory import AVAILABLE_PROVIDERS, get_llm_service, get_provider
from app.llm.mock import MOCK_MODEL_ID, MOCK_PROVIDER_ID, MockLLMProvider
from app.llm.models import (
    CompletionRequest,
    GroundedAnswer,
    LLMMessage,
    LLMResponse,
    TokenUsage,
)
from app.llm.prompts import (
    INSUFFICIENT_EVIDENCE,
    SYSTEM_INSTRUCTIONS,
    SYSTEM_PROMPT_VERSION,
    build_request,
    build_user_turn,
    render_context,
    select_context,
)
from app.llm.service import LLMService

__all__ = [
    "AVAILABLE_PROVIDERS",
    "INSUFFICIENT_EVIDENCE",
    "MOCK_MODEL_ID",
    "MOCK_PROVIDER_ID",
    "SYSTEM_INSTRUCTIONS",
    "SYSTEM_PROMPT_VERSION",
    "CompletionRequest",
    "GroundedAnswer",
    "LLMConfigurationError",
    "LLMError",
    "LLMMessage",
    "LLMProvider",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMRefusalError",
    "LLMResponse",
    "LLMResponseError",
    "LLMService",
    "LLMTimeoutError",
    "MockLLMProvider",
    "TokenUsage",
    "build_request",
    "build_user_turn",
    "get_llm_service",
    "get_provider",
    "render_context",
    "select_context",
]
