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

### 7. Apply schema migrations

The project has no migration framework yet, so additive schema changes ship as
idempotent scripts. Run all (safe to re-run at any time):

```bash
python -m app.migrate            # Project Management columns
python -m app.migrate_documents  # documents table + indexes
python -m app.migrate_embeddings # AI embedding infrastructure
```

### 7b. Initialize AI infrastructure (required for semantic search)

Set up OpenAI embeddings and database tables:

```bash
export OPENAI_API_KEY=sk-your-key-here  # Get from https://platform.openai.com/account/api-keys
python -m app.init_ai
```

This will:
- Enable pgvector extension in PostgreSQL
- Create embedding storage tables
- Download NLTK tokenizer data
- Verify OpenAI API connectivity

See [backend/EMBEDDING_SETUP.md](backend/EMBEDDING_SETUP.md) for detailed AI setup instructions.

### 8. Seed the database

In a separate terminal (with the virtual environment activated):

```bash
cd backend
python -m app.seed
```

This creates 3 sample projects and 20 sample engineers.

### 9. Verify the API

```bash
curl http://localhost:8000/
# Expected: {"message": "Welcome to StratOS AI"}

curl http://localhost:8000/projects
curl http://localhost:8000/engineers
curl http://localhost:8000/documents
```

### Document storage

Uploaded PDFs are written to `backend/storage/documents/` by default (git-ignored).
Override the location and the size limit in `.env`:

```bash
DOCUMENT_STORAGE_ROOT=/var/lib/stratos/documents
MAX_DOCUMENT_SIZE_MB=25
```

Deleting a document is a soft delete — the record is hidden but retained for audit.
Schedule the retention job to reclaim the stored files:

```bash
python -m app.purge_documents --days 30          # dry run: report only
python -m app.purge_documents --days 30 --apply  # actually delete
```

Interactive API documentation is available at `http://localhost:8000/docs`.

---

## AI Features

### Phase 1: Document Intelligence (✅ Complete)

StratOS AI now includes semantic document search powered by OpenAI embeddings and pgvector:

**Capabilities:**
- 🔍 **Semantic Search** — Find documents by meaning, not just keywords
- 📄 **Automatic Embedding** — Documents are embedded asynchronously after upload
- 💰 **Cost Tracking** — Know exactly how much each embedding costs
- 📊 **Embedding Status** — Monitor embedding progress and errors

**Quick Start:**

1. Set your OpenAI API key: `export OPENAI_API_KEY=sk-...`
2. Initialize: `python -m app.init_ai`
3. Upload a document (it will be embedded automatically)
4. Search semantically:

```bash
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "project risks", "limit": 5}'
```

See [backend/EMBEDDING_SETUP.md](backend/EMBEDDING_SETUP.md) for complete documentation.

**Cost:** ~$0.02 per 1M tokens (approximately $0.50-$2/month for typical usage)

### Planned Features (Phases 2-4)

- **Phase 2:** Semantic search UI in React dashboard
- **Phase 3:** RAG engine with LLM integration
- **Phase 4:** AI agents for project analysis, risk assessment, recommendations

---

## Getting Started (Frontend)

The React frontend lives in the [`frontend/`](frontend/) directory and talks to the FastAPI backend above.

### Prerequisites

- Node.js 20+ and npm
- The backend running at `http://localhost:8000` (see the steps above) with a seeded database

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure the backend URL (optional)

The frontend defaults to `http://localhost:8000`. To point it elsewhere, copy the example env file and edit it:

```bash
cp .env.example .env
# then set VITE_API_BASE_URL in .env
```

### 3. Start the development server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`. Open it in your browser:

- **Dashboard** — executive KPIs, project-status chart and recent activity
- **Engineers** — live table of engineers fetched from `GET /engineers`
- **Projects** — full project CRUD
- **Documents** — document repository: upload PDFs, search/filter, download, delete

> The backend must be running and seeded for the Engineers page to load data. If you see a connection error on the Engineers page, confirm the API is up at `http://localhost:8000/engineers`.

### 4. Build for production (optional)

```bash
npm run build      # type-check + bundle into frontend/dist
npm run preview    # preview the production build locally
```