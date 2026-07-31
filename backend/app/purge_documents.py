"""Retention job: reclaim storage for soft-deleted documents.

`DELETE /documents/{id}` only hides the record, so the repository keeps an
audit trail and a future "restore" feature stays cheap. This job is the other
half of that decision: after a retention window, the blob is removed from the
storage backend and the row is marked as purged (storage_key is retained for
the audit trail, but the object is gone).

Intended to run from cron / a scheduled worker.

Usage (from the backend/ directory, with the virtualenv active):
    python -m app.purge_documents                  # dry run, 30-day window
    python -m app.purge_documents --days 7 --apply
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.logging_config import configure_logging
from app.models.document import Document
from app.storage import get_document_storage

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_DAYS = 30


def purge(retention_days: int = DEFAULT_RETENTION_DAYS, apply: bool = False) -> int:
    """Delete blobs for documents soft-deleted more than `retention_days` ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    storage = get_document_storage()
    purged = 0

    with Session(engine) as session:
        statement = select(Document).where(
            Document.deleted_at.is_not(None), Document.deleted_at < cutoff
        )
        for document in session.execute(statement).unique().scalars():
            if not storage.exists(document.storage_key):
                continue
            if apply:
                storage.delete(document.storage_key)
                logger.info(
                    "Purged blob for document id=%s key=%s", document.id, document.storage_key
                )
            else:
                logger.info(
                    "[dry-run] Would purge document id=%s key=%s",
                    document.id,
                    document.storage_key,
                )
            purged += 1

    return purged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Retention window in days (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete. Without this flag the job only reports.",
    )
    args = parser.parse_args()

    configure_logging()
    count = purge(retention_days=args.days, apply=args.apply)
    verb = "Purged" if args.apply else "Would purge"
    print(f"✓ {verb} {count} document blob(s) deleted more than {args.days} day(s) ago.")


if __name__ == "__main__":
    main()
