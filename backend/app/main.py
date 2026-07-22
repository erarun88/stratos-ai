from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from sqlalchemy import text

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
    return [
        {
            "id": 1,
            "name": "AT&T 5G Expansion",
            "status": "In Progress"
        },
        {
            "id": 2,
            "name": "Verizon Fiber Deployment",
            "status": "Completed"
        },
        {
            "id": 3,
            "name": "T-Mobile Network Modernization",
            "status": "Planning"
        }
    ]
@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return {
            "database": result.scalar()
        }