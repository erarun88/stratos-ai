# StratOS AI

## AI Operating System for Enterprise Program & Portfolio Management

StratOS AI is an enterprise-grade AI platform designed to help organizations manage projects, portfolios, risks, resources, financials, and executive decision-making through AI-powered agents, retrieval-augmented generation (RAG), and workflow automation.

## Technology Stack

- Frontend: React + TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Vector Database: PGVector
- AI: OpenAI API
- ORM: SQLAlchemy

## Architecture

React → FastAPI → AI Agents → PostgreSQL + PGVector → OpenAI API

## Status

🚧 Under Development

## Getting Started (Backend)

### 1. Clone the repository

```bash
git clone <repository-url>
cd stratos-ai
```

### 2. Create a virtual environment

```bash
cd backend
python3 -m venv venv
```

### 3. Activate the virtual environment

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your PostgreSQL connection string.

### 6. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 7. Seed the database

In a separate terminal (with the virtual environment activated):

```bash
cd backend
python -m app.seed
```

This creates 3 sample projects and 20 sample engineers.

### 8. Verify the API

```bash
curl http://localhost:8000/
# Expected: {"message": "Welcome to StratOS AI"}

curl http://localhost:8000/projects
curl http://localhost:8000/engineers
```

Interactive API documentation is available at `http://localhost:8000/docs`.