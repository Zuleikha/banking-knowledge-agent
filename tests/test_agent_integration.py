"""The agent end to end against the real embedding model and the real corpus.

Still free and still offline after the first model download: the embedder runs
locally and the provider is ``MockLLMProvider``, so no request leaves the machine
and nothing is billed.

What these tests can and cannot prove is worth being precise about. They prove
the agent *routes* correctly with real semantics -- that each seed question
reaches its own document, that the off-topic controls are refused rather than
answered from something adjacent, and that the passages the model would see are
the right ones. They cannot prove answer *quality*, because the mock does not
reason. That is Stage 11's evaluation set, and pretending otherwise here would
be the most flattering possible test of the least interesting property.
"""

from __future__ import annotations

import pytest

from app.agent.agent import KnowledgeAgent
from app.core.config import Settings
from app.llm.mock import MockLLMProvider
from app.llm.prompts import INSUFFICIENT_EVIDENCE
from app.llm.service import LLMService
from app.rag.pipeline import build_index

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def real_settings_module() -> Settings:
    """Settings for the real model. Module-scoped alongside the index."""
    return Settings(environment="test", log_to_file=False)


@pytest.fixture(scope="module")
def real_retriever(real_settings_module: Settings):
    """A retriever over the real corpus and the real model, built once.

    Module-scoped for the same reason as ``test_rag_integration.py``: loading
    the transformer and embedding 115 chunks costs seconds, and every test here
    reads from the index without mutating it.
    """
    return build_index(real_settings_module, persist=False)


@pytest.fixture
def real_agent(real_retriever, real_settings_module: Settings) -> KnowledgeAgent:
    """An agent over the real index, with a fresh mock provider per test.

    The index is shared; the provider is not, so ``call_count`` assertions
    measure one test's calls rather than the module's running total.

    Free and offline after the first model download: the embedder runs locally
    and the provider is in-process, so no request leaves the machine.
    """
    return KnowledgeAgent(
        real_retriever,
        LLMService(MockLLMProvider(), real_settings_module),
        real_settings_module,
    )

SEED_EXPECTATIONS = (
    (
        "Why would an ATM transaction fail after card authentication?",
        "atm-transaction-lifecycle",
    ),
    ("What component handles card authentication?", "card-authentication"),
    ("Which API is used for payment authorisation?", "payment-authorisation-api"),
    (
        "How would I troubleshoot a failed cash withdrawal?",
        "atm-cash-withdrawal-troubleshooting",
    ),
    (
        "What configuration controls transaction limits?",
        "transaction-limits-configuration",
    ),
)
"""The five seed questions and the document each one is about.

The document ids are the ones Stage 3 measured as rank 1 for these questions
(handover, *Measured results worth keeping*). Asserting them here means a
chunking, embedding or threshold change that quietly breaks the worked examples
fails a test instead of degrading a demo.
"""

OFF_TOPIC = (
    "What is the capital of France?",
    "How do I bake sourdough bread?",
    "What is the offside rule in football?",
)


class TestSeedQuestions:
    @pytest.mark.parametrize(("question", "document_id"), SEED_EXPECTATIONS)
    def test_each_seed_question_is_answered_from_its_own_document(
        self, real_agent: KnowledgeAgent, question, document_id
    ):
        answer = real_agent.ask(question)
        assert answer.is_grounded, f"{question!r} was not answered"
        assert answer.retrieval.documents[0] == document_id

    @pytest.mark.parametrize(("question", "document_id"), SEED_EXPECTATIONS)
    def test_each_seed_question_cites_that_document(
        self, real_agent: KnowledgeAgent, question, document_id
    ):
        answer = real_agent.ask(question)
        assert any(document_id in source for source in answer.sources), (
            f"{question!r} cited {answer.sources}, expected {document_id}"
        )

    @pytest.mark.parametrize(("question", "_document_id"), SEED_EXPECTATIONS)
    def test_each_seed_question_clears_the_floor_comfortably(
        self, real_agent: KnowledgeAgent, question, _document_id
    ):
        answer = real_agent.ask(question)
        assert answer.retrieval.top_score is not None
        assert answer.retrieval.top_score > 0.5

    def test_every_seed_question_retrieves_and_generates(
        self, real_agent: KnowledgeAgent
    ):
        answers = real_agent.ask_many([question for question, _ in SEED_EXPECTATIONS])
        assert all(answer.decision.retrieve for answer in answers)
        assert all(answer.llm_called for answer in answers)
        assert not any(answer.refused for answer in answers)


class TestRefusalWithRealSemantics:
    @pytest.mark.parametrize("question", OFF_TOPIC)
    def test_an_off_topic_question_is_refused_not_answered(
        self, real_agent: KnowledgeAgent, question
    ):
        answer = real_agent.ask(question)
        assert answer.refused is True
        assert answer.text == INSUFFICIENT_EVIDENCE
        assert answer.sources == ()

    @pytest.mark.parametrize("question", OFF_TOPIC)
    def test_an_off_topic_question_costs_no_model_call(
        self, real_agent: KnowledgeAgent, question
    ):
        provider = real_agent.llm_service.provider
        real_agent.ask(question)
        assert getattr(provider, "call_count", None) == 0

    @pytest.mark.parametrize("question", OFF_TOPIC)
    def test_an_off_topic_question_is_still_searched_before_being_refused(
        self, real_agent: KnowledgeAgent, question
    ):
        """The agent does not pre-judge relevance; the calibrated floor does."""
        answer = real_agent.ask(question)
        assert answer.decision.retrieve is True
        assert answer.retrieval.performed is True
        assert answer.retrieval.candidates_considered > 0


class TestParaphrase:
    @pytest.mark.parametrize(
        ("question", "document_id"),
        [
            (
                "money left the account but no cash came out of the machine",
                "atm-cash-withdrawal-troubleshooting",
            ),
            (
                "how does the system check that a card is genuine",
                "card-authentication",
            ),
        ],
    )
    def test_a_paraphrase_still_finds_the_right_document(
        self, real_agent: KnowledgeAgent, question, document_id
    ):
        """The reason embeddings were chosen over lexical search (guide 20.3.1)."""
        answer = real_agent.ask(question)
        assert answer.is_grounded
        assert document_id in answer.retrieval.documents
