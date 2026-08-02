"""Dashboard router - HTTP endpoints for executive dashboard."""

from typing import List

from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import engine
from app.models.project import Project
from app.models.engineer import Engineer
from app.schemas import (
    DashboardSummary,
    ProjectStatusCount,
    ProjectResponse,
    EngineerResponse,
    ProjectStatus,
    EngineerStatus,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

PROJECT_STATUS_LABELS = {
    ProjectStatus.planning: "Planning",
    ProjectStatus.active: "Active",
    ProjectStatus.on_hold: "On Hold",
    ProjectStatus.completed: "Completed",
    ProjectStatus.cancelled: "Cancelled",
}


def _count_by_status(session: Session, model) -> dict:
    """Return {status_value: count} for a model."""
    rows = session.execute(
        select(model.status, func.count()).group_by(model.status)
    ).all()
    return {status_value: count for status_value, count in rows}


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    """Get dashboard summary metrics."""
    with Session(engine) as session:
        project_counts = _count_by_status(session, Project)
        engineer_counts = _count_by_status(session, Engineer)

        return DashboardSummary(
            total_projects=sum(project_counts.values()),
            active_projects=project_counts.get(ProjectStatus.active.value, 0),
            planning_projects=project_counts.get(ProjectStatus.planning.value, 0),
            on_hold_projects=project_counts.get(ProjectStatus.on_hold.value, 0),
            completed_projects=project_counts.get(ProjectStatus.completed.value, 0),
            cancelled_projects=project_counts.get(ProjectStatus.cancelled.value, 0),
            total_engineers=sum(engineer_counts.values()),
            active_engineers=engineer_counts.get(EngineerStatus.active.value, 0),
            inactive_engineers=engineer_counts.get(EngineerStatus.inactive.value, 0),
        )


@router.get("/project-status", response_model=List[ProjectStatusCount])
def get_dashboard_project_status():
    """Get project status breakdown."""
    with Session(engine) as session:
        counts = _count_by_status(session, Project)
        return [
            ProjectStatusCount(
                status=status_enum.value,
                label=PROJECT_STATUS_LABELS[status_enum],
                count=counts.get(status_enum.value, 0),
            )
            for status_enum in ProjectStatus
        ]


@router.get("/recent-projects", response_model=List[ProjectResponse])
def get_dashboard_recent_projects():
    """Get recent projects."""
    with Session(engine) as session:
        statement = select(Project).order_by(Project.created_at.desc(), Project.id.desc()).limit(5)
        return session.execute(statement).scalars().all()


@router.get("/recent-engineers", response_model=List[EngineerResponse])
def get_dashboard_recent_engineers():
    """Get recently added engineers."""
    with Session(engine) as session:
        statement = select(Engineer).order_by(Engineer.id.desc()).limit(5)
        return session.execute(statement).scalars().all()
