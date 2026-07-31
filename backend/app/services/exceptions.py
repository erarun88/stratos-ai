"""Domain exceptions raised by the service layer.

Services stay free of HTTP concepts: they raise these, and the API layer
(app/routers/) translates them into status codes. That keeps the business
rules reusable from a future background worker, CLI or AI pipeline.
"""


class ServiceError(Exception):
    """Base class for expected, caller-correctable service failures."""


class DocumentNotFoundError(ServiceError):
    """The requested document does not exist (or has been deleted)."""


class DocumentValidationError(ServiceError):
    """The upload or metadata failed a business rule."""


class DocumentTooLargeError(ServiceError):
    """The upload exceeded the configured maximum size."""


class UnsupportedFileTypeError(ServiceError):
    """The upload is not one of the accepted file formats."""


class RelatedResourceNotFoundError(ServiceError):
    """A referenced resource (e.g. project_id) does not exist."""
