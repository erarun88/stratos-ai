from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


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
