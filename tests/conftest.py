"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import reset_logging
from app.knowledge.loader import load_knowledge_base
from app.knowledge.models import KnowledgeDocument
from app.llm.mock import MockLLMProvider
from app.llm.service import LLMService
from app.main import create_app
from app.rag.models import RetrievalResult
from app.rag.pipeline import build_index
from app.rag.retriever import Retriever


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Test settings that never touch the developer's real log directory."""
    return Settings(
        environment="test",
        log_level="DEBUG",
        log_format="json",
        log_dir=tmp_path / "logs",
        log_to_file=True,
    )


@pytest.fixture
def app(settings: Settings) -> Iterator[FastAPI]:
    """A FastAPI app built from the test settings."""
    reset_logging()
    yield create_app(settings)
    reset_logging()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client bound to the test application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def knowledge_root() -> Path:
    """The real synthetic knowledge base shipped with the repository."""
    return Settings().knowledge_dir


@pytest.fixture
def rag_settings(tmp_path: Path) -> Settings:
    """Settings for RAG tests: hashing embedder, index written to tmp_path.

    The hashing embedder keeps the suite fast, offline and deterministic. It is
    not semantic, so these tests assert *pipeline* behaviour -- ranking order,
    filtering, thresholds, persistence -- and never retrieval quality. Quality
    is asserted against the real model in ``test_rag_integration.py``.
    """
    return Settings(
        environment="test",
        embedding_model="hashing",
        vectorstore_dir=tmp_path / "vectorstore",
        log_dir=tmp_path / "logs",
        log_to_file=False,
    )


@pytest.fixture
def real_settings(tmp_path: Path) -> Settings:
    """Settings using the real sentence-transformers model, indexed to tmp_path."""
    return Settings(
        environment="test",
        vectorstore_dir=tmp_path / "vectorstore",
        log_dir=tmp_path / "logs",
        log_to_file=False,
    )


@pytest.fixture
def corpus() -> tuple[KnowledgeDocument, ...]:
    """The real synthetic corpus, loaded once per test."""
    return load_knowledge_base(Settings().knowledge_dir)


@pytest.fixture
def retriever(rag_settings: Settings) -> Retriever:
    """A retriever over the real corpus, indexed with the hashing embedder."""
    return build_index(rag_settings, persist=False)


@pytest.fixture
def llm_settings(tmp_path: Path) -> Settings:
    """Settings for LLM tests: mock provider, hashing embedder, no disk logs.

    There is no API key and no provider that could use one. The suite cannot
    make a paid call because no code path exists that makes any call at all.
    """
    return Settings(
        environment="test",
        embedding_model="hashing",
        vectorstore_dir=tmp_path / "vectorstore",
        llm_provider="mock",
        log_dir=tmp_path / "logs",
        log_to_file=False,
    )


@pytest.fixture
def mock_provider() -> MockLLMProvider:
    """A default mock provider that synthesises answers from injected context."""
    return MockLLMProvider()


@pytest.fixture
def llm_service(mock_provider: MockLLMProvider, llm_settings: Settings) -> LLMService:
    """An LLM service wired to the recording mock provider."""
    return LLMService(mock_provider, llm_settings)


@pytest.fixture
def retrieval(retriever: Retriever) -> RetrievalResult:
    """A real, non-empty retrieval result over the real corpus."""
    result = retriever.retrieve("card authentication")
    assert not result.is_empty, "fixture precondition: this query must match"
    return result


@pytest.fixture
def empty_retrieval(retriever: Retriever) -> RetrievalResult:
    """A real retrieval result where nothing cleared the score floor."""
    result = retriever.retrieve("xylophone quokka meringue", min_score=0.99)
    assert result.is_empty, "fixture precondition: this query must match nothing"
    return result
