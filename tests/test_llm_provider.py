"""The provider seam: protocol conformance, the mock, the factory, the errors.

These tests protect the property that makes the whole layer replaceable -- that
nothing above ``app/llm`` depends on a concrete provider -- and the property that
makes the suite safe: no code path here can reach a network or a paid API.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.core.config import Settings
from app.llm import factory as factory_module
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
from app.llm.mock import MOCK_PROVIDER_ID, MockLLMProvider
from app.llm.models import CompletionRequest, LLMMessage, LLMResponse, TokenUsage
from app.llm.service import LLMService

APP_LLM = Path(__file__).resolve().parents[1] / "app" / "llm"

VENDOR_MARKERS = (
    "import anthropic",
    "from anthropic",
    "import openai",
    "from openai",
    "langchain",
    "google.generativeai",
    "mistralai",
    "cohere",
    "ollama",
    "api.anthropic.com",
    "api.openai.com",
)


def make_request(user: str = "Question: why?") -> CompletionRequest:
    """A minimal valid request."""
    return CompletionRequest(
        system="You are a test system prompt.",
        messages=(LLMMessage(role="user", content=user),),
        max_tokens=256,
    )


# --- The protocol --------------------------------------------------------


class TestLLMProviderProtocol:
    def test_mock_satisfies_the_protocol(self):
        assert isinstance(MockLLMProvider(), LLMProvider)

    def test_an_unrelated_object_does_not(self):
        assert not isinstance(object(), LLMProvider)

    def test_protocol_requires_complete(self):
        assert hasattr(LLMProvider, "complete")

    def test_a_structural_implementation_is_accepted(self):
        """No inheritance required: that is the point of a protocol."""

        class Elsewhere:
            provider_id = "elsewhere"
            model_id = "elsewhere-1"

            def complete(self, request: CompletionRequest) -> LLMResponse:
                return LLMResponse(
                    text="ok", provider_id="elsewhere", model_id="elsewhere-1"
                )

        assert isinstance(Elsewhere(), LLMProvider)
        service = LLMService(Elsewhere())
        assert service.provider.provider_id == "elsewhere"


# --- The error taxonomy --------------------------------------------------


class TestErrorTaxonomy:
    @pytest.mark.parametrize(
        "error_type",
        [
            LLMConfigurationError,
            LLMTimeoutError,
            LLMRateLimitError,
            LLMResponseError,
            LLMRefusalError,
            LLMProviderError,
        ],
    )
    def test_every_error_is_an_llm_error(self, error_type):
        assert issubclass(error_type, LLMError)

    def test_llm_error_is_a_runtime_error(self):
        assert issubclass(LLMError, RuntimeError)

    @pytest.mark.parametrize("error_type", [LLMTimeoutError, LLMRateLimitError])
    def test_transport_failures_are_retryable(self, error_type):
        assert error_type("boom").retryable is True

    @pytest.mark.parametrize(
        "error_type",
        [LLMConfigurationError, LLMResponseError, LLMRefusalError, LLMProviderError],
    )
    def test_other_failures_are_not_retryable(self, error_type):
        assert error_type("boom").retryable is False

    def test_rate_limit_carries_retry_after(self):
        assert LLMRateLimitError("slow down", 30.0).retry_after_seconds == 30.0

    def test_rate_limit_retry_after_is_optional_and_distinguishable(self):
        assert LLMRateLimitError("slow down").retry_after_seconds is None


# --- The mock provider ---------------------------------------------------


class TestMockProvider:
    def test_reports_its_identity(self):
        provider = MockLLMProvider()
        assert provider.provider_id == MOCK_PROVIDER_ID
        assert provider.model_id

    def test_records_every_request(self):
        provider = MockLLMProvider()
        provider.complete(make_request("first"))
        provider.complete(make_request("second"))
        assert provider.call_count == 2
        assert provider.last_request is not None
        assert "second" in provider.last_request.user_text

    def test_last_request_is_none_before_any_call(self):
        assert MockLLMProvider().last_request is None

    def test_reset_clears_recorded_calls(self):
        provider = MockLLMProvider()
        provider.complete(make_request())
        provider.reset()
        assert provider.call_count == 0

    def test_response_is_stamped_with_provider_and_model(self):
        provider = MockLLMProvider()
        response = provider.complete(make_request())
        assert response.provider_id == MOCK_PROVIDER_ID
        assert response.model_id == provider.model_id

    def test_is_deterministic(self):
        first = MockLLMProvider().complete(make_request("same"))
        second = MockLLMProvider().complete(make_request("same"))
        assert first.text == second.text

    def test_cites_the_passages_it_was_given(self):
        user = (
            '<retrieved_documentation>\n<passage id="1" source="a.md">A</passage>\n'
            '<passage id="2" source="b.md">B</passage>\n</retrieved_documentation>\n\n'
            "Question: why?"
        )
        response = MockLLMProvider().complete(make_request(user))
        assert "[1]" in response.text
        assert "[2]" in response.text

    def test_says_so_when_given_no_passages(self):
        response = MockLLMProvider().complete(make_request("Question: why?"))
        assert "does not contain enough information" in response.text

    def test_reports_token_usage(self):
        user = '<passage id="1" source="a.md">A</passage>\n\nQuestion: why?'
        usage = MockLLMProvider().complete(make_request(user)).usage
        assert usage.output_tokens > 0
        assert usage.total_tokens >= usage.output_tokens

    def test_scripted_responses_are_returned_in_order(self):
        provider = MockLLMProvider(responses=["one", "two"])
        assert provider.complete(make_request()).text == "one"
        assert provider.complete(make_request()).text == "two"

    def test_a_scripted_response_object_is_returned_as_is(self):
        canned = LLMResponse(
            text="canned",
            provider_id="mock",
            model_id="m",
            stop_reason="max_tokens",
            usage=TokenUsage(input_tokens=1, output_tokens=2),
        )
        assert MockLLMProvider(responses=[canned]).complete(make_request()) is canned

    def test_exhausting_the_script_raises_rather_than_repeating(self):
        provider = MockLLMProvider(responses=["only one"])
        provider.complete(make_request())
        with pytest.raises(LLMResponseError, match="script exhausted"):
            provider.complete(make_request())

    def test_handler_receives_the_request(self):
        seen: list[CompletionRequest] = []

        def handler(request: CompletionRequest) -> LLMResponse:
            seen.append(request)
            return LLMResponse(text="handled", provider_id="mock", model_id="m")

        MockLLMProvider(handler=handler).complete(make_request("unique"))
        assert len(seen) == 1
        assert "unique" in seen[0].user_text

    @pytest.mark.parametrize(
        "error",
        [
            LLMTimeoutError("timed out"),
            LLMRateLimitError("rate limited", 5.0),
            LLMResponseError("malformed"),
            LLMRefusalError("declined"),
        ],
    )
    def test_handler_can_raise_any_llm_error(self, error):
        def handler(request: CompletionRequest) -> LLMResponse:
            raise error

        with pytest.raises(type(error)):
            MockLLMProvider(handler=handler).complete(make_request())

    def test_responses_and_handler_together_are_rejected(self):
        with pytest.raises(ValueError, match="not both"):
            MockLLMProvider(responses=["x"], handler=lambda request: None)


# --- The factory ---------------------------------------------------------


class TestFactory:
    def test_builds_the_mock_by_default(self, llm_settings: Settings):
        assert isinstance(get_provider(llm_settings), MockLLMProvider)

    def test_default_settings_select_the_mock(self):
        assert Settings().llm_provider == MOCK_PROVIDER_ID

    def test_mock_is_the_only_available_provider(self):
        assert AVAILABLE_PROVIDERS == (MOCK_PROVIDER_ID,)

    @pytest.mark.parametrize("requested", ["anthropic", "openai", "gemini", ""])
    def test_an_unavailable_provider_fails_loudly(
        self, llm_settings: Settings, requested: str
    ):
        settings = llm_settings.model_copy(update={"llm_provider": requested})
        with pytest.raises(LLMConfigurationError) as excinfo:
            get_provider(settings)
        assert "Stage 5" in str(excinfo.value)

    def test_an_unavailable_provider_never_falls_back_to_the_mock(
        self, llm_settings: Settings
    ):
        """Silently substituting a stub for a model is worse than failing."""
        settings = llm_settings.model_copy(update={"llm_provider": "anthropic"})
        with pytest.raises(LLMConfigurationError):
            get_provider(settings)

    def test_configuration_errors_are_not_retryable(self, llm_settings: Settings):
        settings = llm_settings.model_copy(update={"llm_provider": "nope"})
        with pytest.raises(LLMConfigurationError) as excinfo:
            get_provider(settings)
        assert excinfo.value.retryable is False

    def test_service_factory_returns_a_wired_service(self, llm_settings: Settings):
        service = get_llm_service(llm_settings)
        assert isinstance(service, LLMService)
        assert service.provider.provider_id == MOCK_PROVIDER_ID


# --- Configuration -------------------------------------------------------


class TestLLMConfiguration:
    def test_api_key_is_unset_by_default(self):
        assert Settings().llm_api_key is None

    def test_api_key_comes_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("BKA_LLM_API_KEY", "test-value-not-a-real-key")
        assert Settings().llm_api_key is not None

    def test_api_key_is_masked_in_repr(self, monkeypatch):
        monkeypatch.setenv("BKA_LLM_API_KEY", "test-value-not-a-real-key")
        settings = Settings()
        assert "test-value-not-a-real-key" not in repr(settings)
        assert "test-value-not-a-real-key" not in str(settings.llm_api_key)

    def test_api_key_is_masked_in_a_model_dump(self, monkeypatch):
        monkeypatch.setenv("BKA_LLM_API_KEY", "test-value-not-a-real-key")
        assert "test-value-not-a-real-key" not in str(Settings().model_dump())

    def test_model_is_unset_while_no_vendor_is_chosen(self):
        assert Settings().llm_model is None

    def test_defaults_are_sane(self):
        settings = Settings()
        assert settings.llm_max_tokens >= 256
        assert settings.llm_timeout_seconds > 0
        assert settings.llm_max_retries >= 0
        assert settings.llm_context_max_chunks >= 1

    def test_settings_are_overridable_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("BKA_LLM_MAX_TOKENS", "1234")
        monkeypatch.setenv("BKA_LLM_CONTEXT_MAX_CHUNKS", "3")
        settings = Settings()
        assert settings.llm_max_tokens == 1234
        assert settings.llm_context_max_chunks == 3

    def test_invalid_values_are_rejected(self, monkeypatch):
        monkeypatch.setenv("BKA_LLM_MAX_TOKENS", "10")
        with pytest.raises(ValueError, match="llm_max_tokens"):
            Settings()


# --- The safety property: nothing here can call anything ------------------


class TestNoVendorAndNoNetwork:
    def test_no_module_in_app_llm_imports_a_vendor_sdk(self):
        for path in sorted(APP_LLM.glob("*.py")):
            source = path.read_text(encoding="utf-8").lower()
            for marker in VENDOR_MARKERS:
                assert marker not in source, f"{path.name} references {marker!r}"

    def test_no_module_in_app_llm_imports_an_http_client(self):
        for path in sorted(APP_LLM.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for marker in ("import httpx", "import requests", "import urllib.request"):
                assert marker not in source, f"{path.name} imports a network client"

    def test_no_url_appears_in_the_llm_package(self):
        for path in sorted(APP_LLM.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            assert "https://" not in source
            assert "http://" not in source

    def test_the_llm_package_imports_nothing_that_can_reach_a_network(self):
        """Checked against the parsed import statements, not against the prose.

        Substring matching on the source would trip over the word "requests" in
        a docstring; the import table is the thing that actually determines what
        this package can do.
        """
        forbidden = {
            "socket",
            "http",
            "urllib",
            "httpx",
            "requests",
            "aiohttp",
            "anthropic",
            "openai",
        }
        for path in sorted(APP_LLM.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    roots = {(node.module or "").split(".")[0]}
                else:
                    continue
                leaked = roots & forbidden
                assert not leaked, f"{path.name} imports {leaked}"

    def test_no_api_key_is_needed_to_build_a_provider(self, llm_settings: Settings):
        settings = llm_settings.model_copy(update={"llm_api_key": None})
        assert get_provider(settings) is not None

    def test_the_factory_registry_lists_only_free_providers(self):
        assert AVAILABLE_PROVIDERS == (MOCK_PROVIDER_ID,)
        assert factory_module.MOCK_PROVIDER_ID == "mock"
