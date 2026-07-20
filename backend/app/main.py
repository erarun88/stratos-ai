from fastapi import FastAPI

app = FastAPI(
    title="StratOS AI",
    description="AI Operating System for Enterprise Program & Portfolio Management",
    version="1.0.0"
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