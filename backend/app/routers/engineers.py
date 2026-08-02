"""Engineers router - HTTP endpoints for engineer management."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.engineer import Engineer
from app.models.project import Project
from app.schemas import (
    EngineerCreate,
    EngineerUpdate,
    EngineerStatusUpdate,
    EngineerResponse,
)

router = APIRouter(prefix="/api/engineers", tags=["engineers"])


@router.get("", response_model=List[EngineerResponse])
def get_engineers():
    """Get all engineers."""
    with Session(engine) as session:
        statement = select(Engineer)
        engineers = session.execute(statement).scalars().all()
        return engineers


@router.get("/{engineer_id}", response_model=EngineerResponse)
def get_engineer(engineer_id: int):
    """Get a specific engineer."""
    with Session(engine) as session:
        engineer = session.get(Engineer, engineer_id)
        if not engineer:
            raise HTTPException(status_code=404, detail=f"Engineer with id {engineer_id} not found")
        return engineer


@router.post("", response_model=EngineerResponse, status_code=status.HTTP_201_CREATED)
def create_engineer(engineer_in: EngineerCreate):
    """Create a new engineer."""
    with Session(engine) as session:
        project = session.get(Project, engineer_in.project_id)
        if not project:
            raise HTTPException(status_code=400, detail=f"Project with id {engineer_in.project_id} does not exist")

        existing = session.execute(
            select(Engineer).where(Engineer.email == engineer_in.email)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail=f"Engineer with email {engineer_in.email} already exists")

        engineer = Engineer(
            name=engineer_in.name,
            email=engineer_in.email,
            role=engineer_in.role,
            status=engineer_in.status.value,
            project_id=engineer_in.project_id
        )
        session.add(engineer)
        session.commit()
        session.refresh(engineer)
        return engineer


@router.put("/{engineer_id}", response_model=EngineerResponse)
def update_engineer(engineer_id: int, engineer_in: EngineerUpdate):
    """Update an engineer."""
    with Session(engine) as session:
        engineer = session.get(Engineer, engineer_id)
        if not engineer:
            raise HTTPException(status_code=404, detail=f"Engineer with id {engineer_id} not found")

        project = session.get(Project, engineer_in.project_id)
        if not project:
            raise HTTPException(status_code=400, detail=f"Project with id {engineer_in.project_id} does not exist")

        existing = session.execute(
            select(Engineer).where(Engineer.email == engineer_in.email, Engineer.id != engineer_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail=f"Engineer with email {engineer_in.email} already exists")

        engineer.name = engineer_in.name
        engineer.email = engineer_in.email
        engineer.role = engineer_in.role
        engineer.status = engineer_in.status.value
        engineer.project_id = engineer_in.project_id

        session.commit()
        session.refresh(engineer)
        return engineer


@router.patch("/{engineer_id}/status", response_model=EngineerResponse)
def update_engineer_status(engineer_id: int, status_in: EngineerStatusUpdate):
    """Update engineer status."""
    with Session(engine) as session:
        engineer = session.get(Engineer, engineer_id)
        if not engineer:
            raise HTTPException(status_code=404, detail=f"Engineer with id {engineer_id} not found")

        engineer.status = status_in.status.value
        session.commit()
        session.refresh(engineer)
        return engineer
