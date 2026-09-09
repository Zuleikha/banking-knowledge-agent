"""The single place the application decides which LLM provider to use.

Mirrors :func:`app.rag.embeddings.get_embedder`: one function, driven by
configuration, so adding a vendor is a new module plus a branch here — never a
change to the service, the agent, or the API layer.

**Stage 4 registers exactly one provider: the mock.** No vendor has been chosen
yet, so there is deliberately nothing here that can reach the network, read a
key, or spend money.

**An unknown provider is a loud failure, not a fallback.** Configuring
``BKA_LLM_PROVIDER=anthropic`` today raises
:class:`~app.llm.base.LLMConfigurationError` and names Stage 5. Falling back to
the mock would be far worse than an error: the application would start, answer
questions, and look entirely healthy while a deterministic stub stood in for a
model — and the only evidence would be a wording change nobody reads.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.tracing import traced
from app.llm.base import LLMConfigurationError, LLMProvider
from app.llm.mock import MOCK_PROVIDER_ID, MockLLMProvider
from app.llm.service import LLMService

logger = get_logger(__name__)

AVAILABLE_PROVIDERS = (MOCK_PROVIDER_ID,)
"""Providers this build can construct. Grows when an adapter is added."""


@traced
def get_provider(settings: Settings | None = None) -> LLMProvider:
    """Build the configured provider.

    Args:
        settings: Application settings. Defaults to the cached singleton.

    Returns:
        An :class:`~app.llm.base.LLMProvider`.

    Raises:
        LLMConfigurationError: If ``BKA_LLM_PROVIDER`` names a provider this
            build cannot construct.
    """
    resolved = settings or get_settings()
    requested = resolved.llm_provider

    if requested == MOCK_PROVIDER_ID:
        logger.info("llm.provider_selected", provider=requested)
        return MockLLMProvider()

    raise LLMConfigurationError(
        f"BKA_LLM_PROVIDER='{requested}' is not available in this build. "
        f"Available: {', '.join(AVAILABLE_PROVIDERS)}. A concrete provider "
        "adapter is deferred to a decision before Stage 5; until then the mock "
        "is the only implementation, and it is not substituted silently."
    )


@traced
def get_llm_service(settings: Settings | None = None) -> LLMService:
    """Build an :class:`~app.llm.service.LLMService` over the configured provider.

    The convenience entry point for callers that do not care which provider is
    in use — which, by design, is all of them.

    Args:
        settings: Application settings. Defaults to the cached singleton.

    Returns:
        A ready-to-use service.

    Raises:
        LLMConfigurationError: If the configured provider is unavailable.
    """
    resolved = settings or get_settings()
    return LLMService(get_provider(resolved), resolved)
