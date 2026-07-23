from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


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
