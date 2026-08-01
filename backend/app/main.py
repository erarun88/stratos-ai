from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
from app.logging_config import configure_logging
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.embedding import DocumentEmbedding, EmbeddingOperation
from app.routers import documents as documents_router
from app.embedding_queue import start_embedding_scheduler, stop_embedding_scheduler
from app.schemas import (
    EngineerCreate,
    EngineerUpdate,
    EngineerStatusUpdate,
    EngineerResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectStatusUpdate,
    ProjectResponse,
    ProjectStatus,
    EngineerStatus,
    DashboardSummary,
    ProjectStatusCount,
)

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown."""
    # Startup
    start_embedding_scheduler()
    yield
    # Shutdown
    stop_embedding_scheduler()


app = FastAPI(
    title="StratOS AI",
    description="AI Operating System for Enterprise Program & Portfolio Management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Document Management module. Feature routers are mounted here; the older
# project/engineer/dashboard endpoints below remain defined inline.
app.include_router(documents_router.router)
app.include_router(documents_router.project_documents_router)

# AI & Search module
from app.routers import search as search_router
app.include_router(search_router.router)

# Admin module (monitoring & diagnostics)
from app.routers import admin as admin_router
app.include_router(admin_router.router)

# Chat module (AI Project Assistant - Phase 2)
from app.routers import chat as chat_router
app.include_router(chat_router.router)

# Approval Framework module (Phase E - Approval gating for dangerous actions)
from app.routers import approvals as approvals_router
app.include_router(approvals_router.router)

# Execution Studio module (Transparency & Education)
from app.routers import execution_studio_api as execution_studio_router
app.include_router(execution_studio_router.router)

@app.get("/")
def home():
    return {"message": "Welcome to StratOS AI"}

@app.get("/projects", response_model=List[ProjectResponse])
def get_projects():
    with Session(engine) as session:
        statement = select(Project).order_by(Project.id)
        projects = session.execute(statement).scalars().all()
        return projects


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")
        return project


@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate):
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


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_in: ProjectUpdate):
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


@app.patch("/projects/{project_id}/status", response_model=ProjectResponse)
def update_project_status(project_id: int, status_in: ProjectStatusUpdate):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

        project.status = status_in.status.value
        session.commit()
        session.refresh(project)
        return project
@app.get("/engineers", response_model=List[EngineerResponse])
def get_engineers():
    with Session(engine) as session:
        statement = select(Engineer)
        engineers = session.execute(statement).scalars().all()
        return engineers

@app.get("/engineers/{engineer_id}", response_model=EngineerResponse)
def get_engineer(engineer_id: int):
    with Session(engine) as session:
        engineer = session.get(Engineer, engineer_id)
        if not engineer:
            raise HTTPException(status_code=404, detail=f"Engineer with id {engineer_id} not found")
        return engineer

@app.post("/engineers", response_model=EngineerResponse, status_code=status.HTTP_201_CREATED)
def create_engineer(engineer_in: EngineerCreate):
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

@app.put("/engineers/{engineer_id}", response_model=EngineerResponse)
def update_engineer(engineer_id: int, engineer_in: EngineerUpdate):
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

@app.patch("/engineers/{engineer_id}/status", response_model=EngineerResponse)
def update_engineer_status(engineer_id: int, status_in: EngineerStatusUpdate):
    with Session(engine) as session:
        engineer = session.get(Engineer, engineer_id)
        if not engineer:
            raise HTTPException(status_code=404, detail=f"Engineer with id {engineer_id} not found")

        engineer.status = status_in.status.value
        session.commit()
        session.refresh(engineer)
        return engineer

@app.get("/projects/{project_id}/engineers", response_model=List[EngineerResponse])
def get_project_engineers(project_id: int):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

        statement = select(Engineer).where(Engineer.project_id == project_id)
        engineers = session.execute(statement).scalars().all()
        return engineers


# ---------------------------------------------------------------------------
# Dashboard (Executive) endpoints
# ---------------------------------------------------------------------------

# Human-readable labels for project statuses, used by the status chart.
PROJECT_STATUS_LABELS = {
    ProjectStatus.planning: "Planning",
    ProjectStatus.active: "Active",
    ProjectStatus.on_hold: "On Hold",
    ProjectStatus.completed: "Completed",
    ProjectStatus.cancelled: "Cancelled",
}


def _count_by_status(session: Session, model) -> dict:
    """Return {status_value: count} for a model, computed in a single query."""
    rows = session.execute(
        select(model.status, func.count()).group_by(model.status)
    ).all()
    return {status_value: count for status_value, count in rows}


@app.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary():
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


@app.get("/dashboard/project-status", response_model=List[ProjectStatusCount])
def get_dashboard_project_status():
    with Session(engine) as session:
        counts = _count_by_status(session, Project)
        # Return every status in a stable order, including zero counts, so the
        # chart always renders the full set of categories.
        return [
            ProjectStatusCount(
                status=status_enum.value,
                label=PROJECT_STATUS_LABELS[status_enum],
                count=counts.get(status_enum.value, 0),
            )
            for status_enum in ProjectStatus
        ]


@app.get("/dashboard/recent-projects", response_model=List[ProjectResponse])
def get_dashboard_recent_projects():
    with Session(engine) as session:
        statement = select(Project).order_by(Project.created_at.desc(), Project.id.desc()).limit(5)
        return session.execute(statement).scalars().all()


@app.get("/dashboard/recent-engineers", response_model=List[EngineerResponse])
def get_dashboard_recent_engineers():
    with Session(engine) as session:
        # Engineers have no created_at column, so id descending is used as the
        # best available proxy for most-recently-added.
        statement = select(Engineer).order_by(Engineer.id.desc()).limit(5)
        return session.execute(statement).scalars().all()


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return {
            "database": result.scalar()
        }