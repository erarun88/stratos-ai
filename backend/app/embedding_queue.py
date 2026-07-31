"""Asynchronous embedding job queue using APScheduler.

Processes documents in the background, generating embeddings for newly uploaded files.

In production with multiple instances, this should be migrated to Celery + Redis.
See ADR-013 in docs/07_Decisions.md for the migration path.
"""

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine
from app.models.document import Document
from app.services.document_embedding_service import embed_document

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def _process_embedding_queue():
    """Process pending document embeddings.

    Runs as a background job. Fetches documents with embedding_status='queued'
    and processes them in order.
    """
    try:
        with Session(engine) as session:
            # Find documents waiting for embedding
            pending_docs = session.execute(
                select(Document).where(Document.embedding_status == "queued")
                .order_by(Document.created_at)
                .limit(5)  # Process up to 5 at a time to avoid overwhelming the API
            ).scalars().all()

            if not pending_docs:
                return

            logger.info(f"Processing {len(pending_docs)} pending embeddings")

            for doc in pending_docs:
                if not settings.openai_api_key:
                    logger.error("OPENAI_API_KEY not configured, skipping embedding")
                    break

                try:
                    embed_document(session, doc.id)
                except Exception as e:
                    logger.error(f"Error embedding document {doc.id}: {e}")

    except Exception as e:
        logger.error(f"Error in embedding queue processor: {e}", exc_info=True)


def start_embedding_scheduler():
    """Start the background embedding scheduler.

    Should be called once at application startup.
    """
    global _scheduler

    if not settings.embedding_worker_enabled:
        logger.info("Embedding worker is disabled (EMBEDDING_WORKER_ENABLED=false)")
        return

    if not settings.openai_api_key:
        logger.warning(
            "OPENAI_API_KEY not configured; embedding worker will not process documents"
        )
        return

    try:
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            _process_embedding_queue,
            "interval",
            seconds=30,  # Check for pending documents every 30 seconds
            id="embedding_queue",
            name="Process document embeddings",
            max_instances=1,  # Prevent overlapping runs
        )
        _scheduler.start()
        logger.info("✓ Embedding scheduler started (30s intervals)")
    except Exception as e:
        logger.error(f"Failed to start embedding scheduler: {e}")


def stop_embedding_scheduler():
    """Stop the background embedding scheduler.

    Should be called at application shutdown.
    """
    global _scheduler

    if _scheduler:
        try:
            _scheduler.shutdown(wait=True)
            logger.info("✓ Embedding scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
