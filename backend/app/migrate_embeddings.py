"""Idempotent migration for AI embedding infrastructure.

Creates:
1. document_embeddings table (chunk storage with pgvector)
2. embedding_operations table (audit trail)
3. Adds embedding status columns to documents table

Run this before deploying AI features:
    python -m app.migrate_embeddings
"""

from sqlalchemy import text
from app.database import engine


def migrate():
    """Apply embedding infrastructure migrations."""
    with engine.connect() as connection:
        # Enable pgvector extension if not already enabled
        try:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.commit()
            print("✓ pgvector extension enabled")
        except Exception as e:
            print(f"⚠ pgvector extension: {e}")

        # Add embedding status columns to documents table (if not already present)
        try:
            connection.execute(
                text(
                    """
                    ALTER TABLE documents
                    ADD COLUMN embedding_status VARCHAR(20) DEFAULT 'queued',
                    ADD COLUMN embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
                    ADD COLUMN token_count INTEGER,
                    ADD COLUMN embedding_cost FLOAT,
                    ADD COLUMN embedding_error TEXT,
                    ADD COLUMN embedded_at TIMESTAMP WITH TIME ZONE;
                    """
                )
            )
            connection.commit()
            print("✓ Documents table enhanced with embedding columns")
        except Exception as e:
            # Columns may already exist; this is expected on subsequent runs
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ Documents table already has embedding columns")
            else:
                print(f"⚠ Documents table update: {e}")

        # Create index on embedding_status for efficient querying
        try:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_documents_embedding_status ON documents(embedding_status);"
                )
            )
            connection.commit()
            print("✓ Index on documents.embedding_status created")
        except Exception as e:
            print(f"⚠ Index creation: {e}")

        # Create document_embeddings table
        try:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS document_embeddings (
                        id BIGSERIAL PRIMARY KEY,
                        document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                        chunk_index INTEGER NOT NULL,
                        chunk_text TEXT NOT NULL,
                        embedding vector(1536),
                        token_count INTEGER,
                        chunk_metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE (document_id, chunk_index)
                    );
                    """
                )
            )
            connection.commit()
            print("✓ document_embeddings table created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ document_embeddings table already exists")
            else:
                print(f"⚠ document_embeddings table: {e}")

        # Create indexes on document_embeddings
        try:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_document_embeddings_doc ON document_embeddings(document_id);"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector ON document_embeddings USING ivfflat (embedding vector_cosine_ops);"
                )
            )
            connection.commit()
            print("✓ Indexes on document_embeddings created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ document_embeddings indexes already exist")
            else:
                print(f"⚠ document_embeddings indexes: {e}")

        # Create embedding_operations table
        try:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS embedding_operations (
                        id BIGSERIAL PRIMARY KEY,
                        document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                        operation_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        duration_ms INTEGER,
                        tokens_used INTEGER,
                        cost_usd NUMERIC(10, 6),
                        error_message TEXT,
                        operation_metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_embedding_operations_doc ON embedding_operations(document_id);
                    CREATE INDEX IF NOT EXISTS idx_embedding_operations_type ON embedding_operations(operation_type);
                    CREATE INDEX IF NOT EXISTS idx_embedding_operations_status ON embedding_operations(status);
                    CREATE INDEX IF NOT EXISTS idx_embedding_operations_created ON embedding_operations(created_at);
                    """
                )
            )
            connection.commit()
            print("✓ embedding_operations table created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ embedding_operations table already exists")
            else:
                print(f"⚠ embedding_operations table: {e}")


if __name__ == "__main__":
    print("Starting embedding infrastructure migration...")
    migrate()
    print("✓ Migration complete!")
