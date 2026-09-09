"""Environment-based application configuration.

All configuration is read from environment variables (optionally seeded from a
local ``.env`` file). Nothing is hardcoded and no secret ever has a real
default value -- see ``.env.example`` for the documented settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

Environment = Literal["local", "test", "production"]
LogFormat = Literal["json", "console"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BKA_",
        extra="ignore",
        frozen=True,
    )

    app_name: str = "Banking Knowledge Agent"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    debug: bool = False

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    knowledge_dir: Path = PROJECT_ROOT / "data" / "knowledge"

    # --- RAG pipeline (Stage 3) ------------------------------------------
    # The index is a build artefact of knowledge_dir, so it is git-ignored and
    # rebuilt rather than committed.
    vectorstore_dir: Path = PROJECT_ROOT / "data" / "vectorstore"

    # Runs locally: no API key, no per-query cost, no network after the first
    # download. Set to "hashing" to run the pipeline with no model at all.
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # None lets sentence-transformers choose (CUDA when present, else CPU).
    embedding_device: str | None = None
    embedding_batch_size: int = Field(default=32, ge=1)

    # None means "use the embedding model's own limit", which is the safe
    # default -- a hardcoded number would silently truncate if the model changed.
    chunk_max_tokens: int | None = Field(default=None, ge=16)
    chunk_overlap_tokens: int = Field(default=32, ge=0)

    retrieval_top_k: int = Field(default=5, ge=1)
    # Empirically calibrated against this corpus and this model; re-measure with
    # `python -m app.rag calibrate` if either changes.
    retrieval_min_score: float = Field(default=0.25, ge=-1.0, le=1.0)

    log_level: LogLevel = "INFO"
    log_format: LogFormat = "console"
    log_dir: Path = PROJECT_ROOT / "logs"
    log_to_file: bool = True

    @property
    def is_production(self) -> bool:
        """Whether the app is running with production settings."""
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
