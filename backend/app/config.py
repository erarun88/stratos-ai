"""Application configuration.

Configuration is read once, at import time, from environment variables
(loaded from backend/.env by python-dotenv). Keeping it in one place means a
new deployment target — or a future move to cloud object storage — is an
environment change rather than a code change.

Usage:
    from app.config import settings
    settings.max_document_size_bytes
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# backend/ — the directory that contains the `app` package.
BACKEND_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DOCUMENT_STORAGE_ROOT = BACKEND_ROOT / "storage" / "documents"
DEFAULT_MAX_DOCUMENT_SIZE_MB = 25


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back on bad input."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the application."""

    # --- Document storage -------------------------------------------------
    # Which storage backend documents are written to. Only "local" is
    # implemented today; see app/storage/ for the abstraction that lets an
    # S3/Azure Blob backend be added without touching the service layer.
    document_storage_backend: str = os.getenv("DOCUMENT_STORAGE_BACKEND", "local")

    # Filesystem root for the local backend. Everything the app writes stays
    # inside this directory.
    document_storage_root: Path = Path(
        os.getenv("DOCUMENT_STORAGE_ROOT") or DEFAULT_DOCUMENT_STORAGE_ROOT
    ).resolve()

    # Hard upload limit, enforced while streaming (never trusting the
    # client-supplied Content-Length header).
    max_document_size_bytes: int = (
        _get_int("MAX_DOCUMENT_SIZE_MB", DEFAULT_MAX_DOCUMENT_SIZE_MB) * 1024 * 1024
    )

    # PDF is the only accepted format this sprint. Adding a format means
    # extending these two sets plus the magic-number table in
    # app/services/document_service.py.
    allowed_document_content_types: frozenset[str] = field(
        default_factory=lambda: frozenset({"application/pdf"})
    )
    allowed_document_extensions: frozenset[str] = field(
        default_factory=lambda: frozenset({".pdf"})
    )

    # Chunk size used when streaming uploads and downloads (1 MB).
    file_chunk_size: int = 1024 * 1024

    # --- Logging ----------------------------------------------------------
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # --- AI & Embedding Configuration ------------------------------------------
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_batch_size: int = _get_int("EMBEDDING_BATCH_SIZE", 20)
    embedding_worker_enabled: bool = os.getenv("EMBEDDING_WORKER_ENABLED", "true").lower() == "true"
    embedding_max_retries: int = _get_int("EMBEDDING_MAX_RETRIES", 3)
    embedding_retry_delay: int = _get_int("EMBEDDING_RETRY_DELAY", 1)
    embedding_max_chunk_tokens: int = _get_int("EMBEDDING_MAX_CHUNK_TOKENS", 800)
    embedding_min_chunk_tokens: int = _get_int("EMBEDDING_MIN_CHUNK_TOKENS", 100)

    # --- LLM Configuration (Phase 2) ------------------------------------------
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" or "openai"
    llm_model: str = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    llm_api_key: str = os.getenv("ANTHROPIC_API_KEY", os.getenv("LLM_API_KEY", ""))
    llm_max_tokens: int = _get_int("LLM_MAX_TOKENS", 2000)
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    llm_timeout_seconds: int = _get_int("LLM_TIMEOUT_SECONDS", 30)

    @property
    def max_document_size_mb(self) -> int:
        return self.max_document_size_bytes // (1024 * 1024)


settings = Settings()
