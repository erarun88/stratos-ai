"""Idempotent schema migration for the Document Management module.

The project has no migration framework (Alembic is proposed in ADR-P03) and
SQLAlchemy's create_all() will not alter an existing table, so the additive
DDL for the `documents` table is applied here directly.

Safe to run any number of times — every statement uses IF NOT EXISTS.

Usage (from the backend/ directory, with the virtualenv active):
    python -m app.migrate_documents
"""

from sqlalchemy import text

from app.database import engine

STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS documents (
        id               SERIAL PRIMARY KEY,
        title            VARCHAR(255) NOT NULL,
        description      TEXT,
        document_type    VARCHAR(50)  NOT NULL DEFAULT 'other',
        project_id       INTEGER REFERENCES projects(id),
        customer         VARCHAR(255),
        uploaded_by      VARCHAR(255),
        filename         VARCHAR(255) NOT NULL,
        content_type     VARCHAR(100) NOT NULL,
        file_size        BIGINT       NOT NULL,
        content_hash     VARCHAR(64)  NOT NULL,
        storage_backend  VARCHAR(30)  NOT NULL DEFAULT 'local',
        storage_key      VARCHAR(500) NOT NULL UNIQUE,
        created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
        updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
        deleted_at       TIMESTAMPTZ
    )
    """,
    # Indexes for the list endpoint's filters. Every query also filters on
    # deleted_at IS NULL, so the type/project/customer indexes are partial —
    # smaller, and they only cover rows the API can actually return.
    "CREATE INDEX IF NOT EXISTS ix_documents_project_id ON documents (project_id) WHERE deleted_at IS NULL",
    "CREATE INDEX IF NOT EXISTS ix_documents_document_type ON documents (document_type) WHERE deleted_at IS NULL",
    "CREATE INDEX IF NOT EXISTS ix_documents_customer ON documents (customer) WHERE deleted_at IS NULL",
    "CREATE INDEX IF NOT EXISTS ix_documents_deleted_at ON documents (deleted_at)",
    # Default ordering of the repository listing.
    "CREATE INDEX IF NOT EXISTS ix_documents_created_at ON documents (created_at DESC)",
    # Integrity / de-duplication lookups, and the natural cache key for the
    # future embedding pipeline ("have we already processed this content?").
    "CREATE INDEX IF NOT EXISTS ix_documents_content_hash ON documents (content_hash)",
]


def run() -> None:
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))
    print("✓ Documents table migration applied successfully.")


if __name__ == "__main__":
    run()
