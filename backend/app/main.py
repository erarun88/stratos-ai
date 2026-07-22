from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.engineer import Engineer

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
@app.get("/engineers")
def get_engineers():
    with Session(engine) as session:
        statement = select(Engineer)
        engineers = session.execute(statement).scalars().all()
        return [
            {
                "id": e.id,
                "name": e.name,
                "email": e.email,
                "role": e.role,
                "status": e.status,
                "project_id": e.project_id
            }
            for e in engineers
        ]

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return {
            "database": result.scalar()
        }