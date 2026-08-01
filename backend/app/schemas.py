from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class EngineerStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    on_leave = "on_leave"


class EngineerCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    status: EngineerStatus
    project_id: int

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v


class EngineerUpdate(BaseModel):
    name: str
    email: EmailStr
    role: str
    status: EngineerStatus
    project_id: int

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v


class EngineerStatusUpdate(BaseModel):
    status: EngineerStatus


class EngineerResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    project_id: int

    model_config = ConfigDict(from_attributes=True)


class ProjectStatus(str, Enum):
    planning = "planning"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


def _validate_name(v: str) -> str:
    if not v.strip():
        raise ValueError("must not be empty")
    return v.strip()


class ProjectCreate(BaseModel):
    name: str
    customer: str
    project_manager: str
    status: ProjectStatus = ProjectStatus.planning
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    @field_validator("name", "customer", "project_manager")
    @classmethod
    def not_blank(cls, v: str) -> str:
        return _validate_name(v)

    @model_validator(mode="after")
    def end_date_after_start_date(self) -> "ProjectCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class ProjectUpdate(BaseModel):
    name: str
    customer: str
    project_manager: str
    status: ProjectStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    @field_validator("name", "customer", "project_manager")
    @classmethod
    def not_blank(cls, v: str) -> str:
        return _validate_name(v)

    @model_validator(mode="after")
    def end_date_after_start_date(self) -> "ProjectUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus


class ProjectResponse(BaseModel):
    id: int
    name: str
    customer: str
    project_manager: Optional[str] = None
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Dashboard (Executive) schemas
# ---------------------------------------------------------------------------


class DashboardSummary(BaseModel):
    total_projects: int
    active_projects: int
    planning_projects: int
    on_hold_projects: int
    completed_projects: int
    cancelled_projects: int
    total_engineers: int
    active_engineers: int
    inactive_engineers: int


class ProjectStatusCount(BaseModel):
    status: str
    label: str
    count: int


# ---------------------------------------------------------------------------
# Document Management schemas
# ---------------------------------------------------------------------------


class DocumentType(str, Enum):
    """Business classification of a document.

    Kept deliberately coarse: it drives filtering today and will drive
    retrieval strategy (e.g. which documents feed contract risk analysis)
    once AI processing is added.
    """

    contract = "contract"
    sow = "sow"
    proposal = "proposal"
    report = "report"
    specification = "specification"
    meeting_minutes = "meeting_minutes"
    other = "other"


class DocumentSortField(str, Enum):
    created_at = "created_at"
    title = "title"
    file_size = "file_size"
    document_type = "document_type"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


def _optional_trimmed(value: Optional[str]) -> Optional[str]:
    """Trim an optional free-text field, collapsing blanks to None."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class DocumentCreate(BaseModel):
    """Metadata supplied alongside the uploaded file (multipart form fields)."""

    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    document_type: DocumentType = DocumentType.other
    project_id: Optional[int] = None
    customer: Optional[str] = Field(default=None, max_length=255)
    uploaded_by: Optional[str] = Field(default=None, max_length=255)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        return _validate_name(v)

    @field_validator("description", "customer", "uploaded_by")
    @classmethod
    def blank_to_none(cls, v: Optional[str]) -> Optional[str]:
        return _optional_trimmed(v)

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("project_id must be a positive integer")
        return v


class DocumentUpdate(BaseModel):
    """Partial metadata update (PATCH).

    Only the fields present in the request body are applied, so a client can
    clear `customer` by sending null without disturbing the other fields.
    """

    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    document_type: Optional[DocumentType] = None
    project_id: Optional[int] = None
    customer: Optional[str] = Field(default=None, max_length=255)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _validate_name(v)

    @field_validator("description", "customer")
    @classmethod
    def blank_to_none(cls, v: Optional[str]) -> Optional[str]:
        return _optional_trimmed(v)

    @field_validator("project_id")
    @classmethod
    def project_id_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("project_id must be a positive integer")
        return v


class DocumentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    document_type: str
    project_id: Optional[int] = None
    # Denormalised for display so the UI does not have to join client-side.
    project_name: Optional[str] = None
    customer: Optional[str] = None
    uploaded_by: Optional[str] = None
    filename: str
    content_type: str
    file_size: int
    content_hash: str
    storage_backend: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Embedding status fields for AI features
    embedding_status: Optional[str] = None
    embedding_model: Optional[str] = None
    token_count: Optional[int] = None
    embedding_cost: Optional[float] = None
    embedded_at: Optional[datetime] = None
    embedding_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated envelope — document repositories grow without bound, so the
    list endpoint is paginated from day one."""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
