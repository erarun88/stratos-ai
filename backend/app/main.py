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
app.include_router(chat_router.router, prefix="/api")

# Approval Framework module (Phase E - Approval gating for dangerous actions)
from app.routers import approvals as approvals_router
app.include_router(approvals_router.router)

# Execution Studio module (Transparency & Education)
from app.routers import execution_studio_api as execution_studio_router
app.include_router(execution_studio_router.router)

# Projects module
from app.routers import projects as projects_router
app.include_router(projects_router.router)

# Engineers module
from app.routers import engineers as engineers_router
app.include_router(engineers_router.router)

# Dashboard module
from app.routers import dashboard as dashboard_router
app.include_router(dashboard_router.router)

@app.get("/")
def home():
    return {"message": "Welcome to StratOS AI"}



@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return {
            "database": result.scalar()
        }