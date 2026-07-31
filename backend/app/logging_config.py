"""Minimal, centralised logging setup.

The application logs through the standard library `logging` module, so any
production log shipper (JSON formatter, OpenTelemetry handler, Datadog agent)
can be introduced later by changing this one function.
"""

import logging

from app.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure root logging once, at application start-up."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format=LOG_FORMAT,
        force=True,
    )
