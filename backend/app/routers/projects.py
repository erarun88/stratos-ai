"""Projects router - HTTP endpoints for project management."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import engine
from app.models.project import Project
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectStatusUpdate,
    ProjectResponse,
    ProjectStatus,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
def get_projects():
    """Get all projects."""
    with Session(engine) as session:
        statement = select(Project).order_by(Project.id)
        projects = session.execute(statement).scalars().all()
        return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    """Get a specific project."""
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")
        return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate):
    """Create a new project."""
    with Session(engine) as session:
        project = Project(
            name=project_in.name,
            customer=project_in.customer,
            project_manager=project_in.project_manager,
            status=project_in.status.value,
            start_date=project_in.start_date,
            end_date=project_in.end_date,
            description=project_in.description,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_in: ProjectUpdate):
    """Update a project."""
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

        project.name = project_in.name
        project.customer = project_in.customer
        project.project_manager = project_in.project_manager
        project.status = project_in.status.value
        project.start_date = project_in.start_date
        project.end_date = project_in.end_date
        project.description = project_in.description

        session.commit()
        session.refresh(project)
        return project


@router.patch("/{project_id}/status", response_model=ProjectResponse)
def update_project_status(project_id: int, status_in: ProjectStatusUpdate):
    """Update project status."""
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

        project.status = status_in.status.value
        session.commit()
        session.refresh(project)
        return project
