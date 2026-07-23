from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.engineer import Engineer
from app.schemas import EngineerCreate, EngineerUpdate, EngineerStatusUpdate, EngineerResponse

app = FastAPI(
    title="StratOS AI",
    description="AI Operating System for Enterprise Program & Portfolio Management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to StratOS AI"}

@app.get("/projects")
def get_projects():
    with Session(engine) as session:
        statement = select(Project)
        projects = session.execute(statement).scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "customer": p.customer,
                "status": p.status,
                "budget": float(p.budget)
            }
            for p in projects
        ]
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

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return {
            "database": result.scalar()
        }