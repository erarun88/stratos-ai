# Architectural Decisions

Record of major architectural and technical decisions made during the development of StratOS AI. These decisions guide the direction of the project and explain the "why" behind our choices.

---

## Format & Guidelines

Each architectural decision follows the ADR (Architecture Decision Record) format:

- **Decision ID**: Unique identifier (ADR-001, ADR-002, etc.)
- **Date**: When the decision was made
- **Title**: Clear, concise title
- **Context**: Why this decision was needed, what problem it solves
- **Options Considered**: Alternatives that were evaluated
- **Decision**: What was chosen and rationale
- **Consequences**: Impact, trade-offs, and implications
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **References**: Related documents or links

---

## Accepted Decisions

### ADR-001: Use FastAPI as Web Framework

**Date**: 2026-06-15

**Status**: ✅ Accepted & Implemented

**Context**: 
The project needed a modern Python web framework to build REST APIs for the StratOS AI backend. The framework must support:
- High performance and throughput
- Easy API development
- Built-in documentation generation
- Type safety and validation
- Async/await support for scalability
- Large and active community

**Options Considered**:
1. **Django**: Full-featured framework, batteries included, heavier
2. **Flask**: Lightweight, minimal, requires more manual configuration
3. **FastAPI**: Modern, fast, auto-documentation, type hints, async-ready
4. **Starlette**: Lower-level ASGI framework, more control, steeper learning curve
5. **Go/Gin**: Different language, excellent performance, different ecosystem

**Decision**: 
✅ **FastAPI** was chosen as the web framework.

**Rationale**:
- Best performance for Python (nearly as fast as Go/Node.js)
- Excellent developer experience with auto-generated OpenAPI docs
- Strong type hints enable early error detection
- Built-in request/response validation (Pydantic)
- Supports async operations natively
- Large and growing ecosystem
- Easy to learn and use
- Perfect balance between simplicity and power

**Consequences**:
- **Positive**:
  - Development is fast and productive
  - API documentation is automatically generated
  - Type safety catches many bugs early
  - Excellent performance for an AI-heavy application
  - Easy to add async operations later
  
- **Negative**:
  - Smaller ecosystem than Django
  - Some advanced features may need custom implementation
  - Team needs Python async/await knowledge

**Future**: 
If requirements change significantly, migration to another framework would require rewriting route handlers and middleware.

---

### ADR-002: PostgreSQL as Primary Database

**Date**: 2026-06-15

**Status**: ✅ Accepted & Implemented

**Context**:
The project needs a reliable, scalable database for enterprise project management data. Requirements include:
- ACID compliance for data integrity
- Support for complex relationships (projects, engineers, assignments)
- Scalability for future growth
- Vector search capabilities for AI features
- Reliability and community support

**Options Considered**:
1. **PostgreSQL**: Mature, feature-rich, excellent ecosystem, pgvector available
2. **MySQL**: Widely used, good performance, fewer advanced features
3. **MongoDB**: NoSQL, flexible schema, document-oriented, scaling complexity
4. **DynamoDB**: Managed service, good scalability, expensive, vendor lock-in
5. **Oracle**: Enterprise database, expensive, overkill for startup

**Decision**:
✅ **PostgreSQL** was chosen as the primary database.

**Rationale**:
- Battle-tested in production environments for decades
- Powerful features: JSON, arrays, full-text search, vector search (pgvector)
- ACID guarantees for data integrity
- Open source (no licensing costs)
- Excellent community and documentation
- pgvector extension enables vector search without separate vector DB
- Supabase provides managed PostgreSQL with pgvector pre-installed
- Native support for complex relationships needed for project management

**Consequences**:
- **Positive**:
  - Rock-solid data integrity
  - Can run AI features (embeddings) natively
  - No separate vector database needed
  - Scales well for enterprise use
  - Open source and cost-effective
  
- **Negative**:
  - Heavier than NoSQL for some use cases
  - Vertical scaling limits (though replication possible)
  - JSON queries not as optimized as native document stores

**Related**: [ADR-004: Supabase as Database Provider]

---

### ADR-003: SQLAlchemy ORM for Database Access

**Date**: 2026-06-20

**Status**: ✅ Accepted & Implemented

**Context**:
The project needed a way to interact with PostgreSQL from Python. The ORM must:
- Provide type-safe database operations
- Prevent SQL injection attacks
- Support relationship management (Projects ↔ Engineers)
- Be compatible with FastAPI
- Have good performance

**Options Considered**:
1. **SQLAlchemy**: Full-featured ORM, flexible, large ecosystem
2. **Django ORM**: Part of Django, tightly coupled, not compatible with FastAPI
3. **Tortoise ORM**: Async-first, simpler, newer, smaller ecosystem
4. **Raw SQL**: Direct control, vulnerable to injection, harder to maintain
5. **SQLModel**: Combines SQLAlchemy with Pydantic, newer, smaller community

**Decision**:
✅ **SQLAlchemy 2.0+** was chosen as the ORM.

**Rationale**:
- Most mature and battle-tested Python ORM
- Works seamlessly with FastAPI
- Provides database abstraction (could switch databases if needed)
- Strong type hints support in SQLAlchemy 2.0+
- Excellent relationship support (foreign keys, many-to-many)
- Prevents SQL injection through prepared statements
- Large community with solutions for most problems
- Better performance than higher-level abstractions

**Consequences**:
- **Positive**:
  - Safe from SQL injection attacks
  - Clean, Pythonic code for database operations
  - Easy to manage complex relationships
  - Can swap PostgreSQL for another DB if needed
  
- **Negative**:
  - Steeper learning curve than raw SQL
  - Slightly more verbose than frameworks like Django ORM
  - Requires understanding of sessions and transactions

**Supersedes**: Any consideration of raw SQL or other ORMs

---

### ADR-004: Supabase as Database Provider

**Date**: 2026-06-15

**Status**: ✅ Accepted & Implemented

**Context**:
The project needs managed PostgreSQL hosting with the following requirements:
- Handles infrastructure and backups automatically
- Includes pgvector for AI features
- Cost-effective for early stages
- Quick setup (no ops overhead)
- Scalable as the project grows

**Options Considered**:
1. **Supabase**: Managed PostgreSQL + pgvector + Auth, good UX, reasonable cost
2. **AWS RDS**: More options, industry standard, more complex, higher cost
3. **DigitalOcean Managed DB**: Simpler than AWS, good performance, fewer features
4. **Self-hosted**: Full control, operational overhead, risk of downtime
5. **Azure Database**: Enterprise features, good for Azure shops, higher cost
6. **Google Cloud SQL**: Similar to AWS RDS, good if using GCP ecosystem

**Decision**:
✅ **Supabase** was chosen as the managed database provider.

**Rationale**:
- Excellent developer experience (Postgres + Vector DB + Auth all included)
- pgvector extension pre-installed (saves setup time)
- Affordable for a startup/early-stage project
- Fast setup (no infrastructure work needed)
- Good documentation and community support
- Includes built-in features like authentication (future)
- Starts small, scales as needed
- Good connection pooling with PgBouncer

**Consequences**:
- **Positive**:
  - No database administration overhead
  - Automatic backups and maintenance
  - pgvector available out of box
  - Fast initial deployment
  - Cost-effective at current scale
  
- **Negative**:
  - Vendor lock-in (though PostgreSQL is standard)
  - Less control over database configuration
  - Regional availability considerations
  - Cost increases with scale

**Note**: If costs become prohibitive at scale, migration to self-hosted or AWS RDS is possible but requires planning.

---

### ADR-005: REST API over GraphQL

**Date**: 2026-06-20

**Status**: ✅ Accepted & Implemented

**Context**:
The project needs an API style for client-server communication. Requirements:
- Simple to implement initially
- Easy for clients to consume
- Well-understood by the team
- Suitable for current feature set
- Can evolve as needs change

**Options Considered**:
1. **REST**: Well-established, simple, resource-oriented, HTTP-standard
2. **GraphQL**: Flexible, powerful, steep learning curve, over-engineered for MVP
3. **gRPC**: High performance, binary protocol, better for microservices
4. **SOAP**: Legacy, complex, rarely used in modern projects
5. **Hybrid**: REST now, GraphQL later as needs grow

**Decision**:
✅ **REST API** implemented now, with GraphQL as a future option.

**Rationale**:
- REST is simpler to implement for an MVP
- Team understands REST conventions better
- Current feature set doesn't need GraphQL's flexibility
- Better for caching and CDN usage
- HTTP status codes align well with resource operations
- Can add GraphQL layer later without removing REST
- Better browser compatibility for debugging

**Consequences**:
- **Positive**:
  - Fast to implement endpoints
  - Easy to test (curl, Postman, etc.)
  - Standard HTTP behavior
  - Good caching capabilities
  
- **Negative**:
  - Over-fetching (clients get more data than needed)
  - Multiple requests for related data
  - Can be verbose for complex queries
  - Harder to evolve API without breaking changes

**Future Plan**: 
Add GraphQL as alternative query interface in v2.0+ (not replacing REST, supplementing it).

---

### ADR-006: Shared ORM Base Model

**Date**: 2026-07-22

**Status**: ✅ Accepted & Implemented

**Context**:
The project has multiple SQLAlchemy models (Project, Engineer) that need to work together with foreign key relationships. Initially each model had its own `declarative_base()`, causing foreign key resolution to fail.

**Problem**:
```python
# project.py
Base = declarative_base()  # Different base

# engineer.py
Base = declarative_base()  # Different base

# Result: Engineer can't resolve Project table in foreign key ❌
```

**Options Considered**:
1. **Shared Base in __init__.py**: Centralized, clean, scalable
2. **Shared Base in separate file**: More separation, slightly more imports
3. **Keep separate bases**: Would require workarounds, fragile
4. **Use declarative registry**: More complex, unnecessary for current scale

**Decision**:
✅ **Shared Base in models/__init__.py** 

All models import from `app.models` and use the shared `Base`.

**Rationale**:
- Single source of truth for ORM configuration
- Enables proper foreign key resolution
- All models registered in same metadata
- Clean import: `from app.models import Base`
- Easy to maintain and understand
- Scalable as more models are added

**Consequences**:
- **Positive**:
  - Foreign key relationships work correctly
  - Single metadata registry for all tables
  - Easy to create all tables at once
  - Clean architecture for future expansion
  
- **Negative**:
  - Models have a shared dependency
  - Must be careful when adding new models
  - All models are imported when Base is imported

**Implementation**:
```python
# models/__init__.py
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# models/project.py
from app.models import Base

# models/engineer.py  
from app.models import Base
```

---

### ADR-007: Environment-Based Configuration

**Date**: 2026-06-20

**Status**: ✅ Accepted & Implemented

**Context**:
The project needs database credentials and configuration that:
- Works across development, staging, and production
- Keeps secrets secure (not in version control)
- Is easy to configure
- Supports different environments

**Options Considered**:
1. **Environment Variables (.env file)**: Simple, standard, python-dotenv library
2. **Config file (YAML/JSON)**: More flexible, more complex
3. **Hardcoded in code**: Dangerous, never do this ❌
4. **AWS Secrets Manager**: Great for production, overkill for MVP
5. **ConfigParser**: Older Python standard, less flexible

**Decision**:
✅ **Environment Variables with python-dotenv**

**Rationale**:
- Industry standard for configuration
- Simple and lightweight
- Supports development and production workflows
- `.env` file can be .gitignored to keep secrets safe
- Aligns with 12-factor app principles
- Works with all deployment platforms

**Consequences**:
- **Positive**:
  - Secrets never in version control
  - Easy to configure per environment
  - Standard practice familiar to developers
  
- **Negative**:
  - Must remember to .gitignore .env
  - No validation of required variables
  - Plain text storage on local machine (acceptable for dev)

**Future**: 
For production, migrate to cloud secret management (AWS Secrets Manager, Vault, etc.)

**Implementation**:
```
# .env
DATABASE_URL=postgresql://user:pass@host:5432/db

# Python
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

### ADR-008: CORS Middleware with All Origins (Development Only)

**Date**: 2026-07-22

**Status**: ✅ Accepted & Implemented / ⚠️ Insecure

**Context**:
The API needs to be accessible from web clients (future React frontend). CORS (Cross-Origin Resource Sharing) must be configured.

**Current Implementation**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Decision**:
✅ **Allow all origins for development**
⚠️ **This is intentionally insecure for MVP**

**Rationale for MVP**:
- Easier testing and development
- No need to reconfigure when testing from different domains
- Temporary solution while frontend not yet deployed

**Consequences**:
- **Positive**:
  - Development flexibility
  - Easy testing from any domain
  
- **Negative**:
  - **Security risk**: Any website can access your API
  - Not suitable for production
  - Opens door to CSRF attacks

**Future Migration Plan**:
```python
# For Production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stratos-ai.com",
        "https://app.stratos-ai.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Status**: 🔴 **Must be fixed before production**

---

### ADR-009: Synchronous API for MVP

**Date**: 2026-07-22

**Status**: ✅ Accepted (MVP) / 📋 Planned (Future)

**Context**:
FastAPI supports both synchronous and asynchronous endpoint handlers. For MVP, needed to balance simplicity with future scalability.

**Options Considered**:
1. **Synchronous (sync)**: Simpler, easier to understand, blocking operations
2. **Asynchronous (async)**: More complex, better scalability, non-blocking
3. **Mixed**: Some sync, some async, complexity in management

**Decision**:
✅ **Synchronous for MVP** / 📋 **Async for v1.5+**

**Rationale**:
- Simpler to implement and understand (good for MVP)
- SQLAlchemy ORM works well with sync operations
- Good performance for current scale (< 100 RPS)
- Easier to debug
- Can migrate to async without API changes

**Consequences**:
- **Positive**:
  - Simple, readable code
  - Easier testing and debugging
  - Sufficient for current requirements
  
- **Negative**:
  - Thread pool limitation (~10-20 concurrent requests per process)
  - Cannot handle thousands of concurrent connections
  - Blocking database calls tie up threads

**Future Plan** (v1.5+):
```python
# Migrate to async
@app.get("/projects")
async def get_projects():  # async def
    # async database operations
    projects = await session.execute(statement)
    return projects
```

**Migration**: FastAPI allows gradual migration (sync and async endpoints can coexist)

---

### ADR-010: Store Document Binaries Outside the Database, Behind a Storage Interface

**Date**: 2026-07-26

**Status**: ✅ Accepted

**Context**:
The Document Management module needs to persist PDFs. Three options were considered:

1. **BYTEA / large objects in PostgreSQL** — transactional with the metadata, but bloats
   the database, slows backups, and makes streaming awkward. Supabase storage is the most
   expensive place to keep megabytes of inert bytes.
2. **Cloud object storage now (S3 / Azure Blob)** — the production answer, but adds a
   credential, a vendor dependency and local-development friction in a sprint where no AI
   or cloud work is in scope.
3. **Local filesystem behind an interface** — chosen.

**Decision**:
Blobs are written through the `DocumentStorage` interface (`app/storage/base.py`), with a
local filesystem implementation today. The database stores only `storage_backend` and an
opaque `storage_key`; `get_document_storage()` selects the backend from configuration.

**Consequences**:
- ✅ Database stays small; backups and queries stay fast
- ✅ Adding S3/Azure is one new class plus a config value — no schema, service or API change
- ✅ `storage_backend` is per-row, so existing objects can be migrated gradually
- ⚠️ Blob writes are not transactional with the metadata insert. Mitigated by writing the
  blob first and deleting it if the commit fails (compensating action), so storage is never
  left with an object no row points to
- ⚠️ The local backend does not work across multiple app instances — moving to S3 is a
  prerequisite for horizontal scaling

---

### ADR-011: Soft Delete for Documents

**Date**: 2026-07-26

**Status**: ✅ Accepted

**Context**:
Projects and engineers are never hard-deleted (status change is the retirement path), but a
document repository genuinely needs a delete action. Documents are also contractual and
audit-relevant, and future versioning/approval workflows need the history.

**Decision**:
`DELETE /documents/{id}` sets `deleted_at`. Every query filters `deleted_at IS NULL`, so the
document vanishes from the API. A separate retention job, `app/purge_documents.py`, removes
the blob after a configurable window (default 30 days, dry-run by default).

**Consequences**:
- ✅ Consistent with the project's existing "preserve history" stance
- ✅ Restore, versioning and audit trails become cheap to add
- ✅ Blob storage is still reclaimed, just asynchronously
- ⚠️ Until the retention job runs, deleted content is still on disk — a consideration for
  GDPR/right-to-erasure requests, which will need an immediate-purge path
- ⚠️ The job must actually be scheduled, or storage grows without bound

---

### ADR-012: Routers + Service Layer for New Modules

**Date**: 2026-07-26

**Status**: ✅ Accepted (implements ADR-P02 for new modules)

**Context**:
`main.py` had grown to ~280 lines with every endpoint inline. The Document module adds
uploads, streaming, validation and storage orchestration — materially more logic than a
CRUD handler should carry.

**Decision**:
New modules ship as an `APIRouter` (`app/routers/`) plus a service module
(`app/services/`). Services contain the rules and import no FastAPI; they raise domain
exceptions from `app/services/exceptions.py`, which routers translate into status codes.
Existing Project/Engineer/Dashboard endpoints were **not** refactored — that is a separate,
reviewable change.

**Consequences**:
- ✅ Business logic is unit-testable without an HTTP client, and reusable by the future AI
  ingestion pipeline
- ✅ `main.py` stops growing linearly with the feature count
- ⚠️ Two styles coexist in the codebase until the older endpoints are migrated

---

## Proposed Decisions

### ADR-P01: Input Validation with Pydantic Models

**Date**: 2026-07-22

**Status**: 📋 Proposed (Not implemented yet)

**Context**:
Current endpoints don't validate input data. As endpoints for creating/updating data are added, validation is critical for:
- Data integrity
- Security (prevent injection attacks)
- User feedback (clear error messages)
- Type safety

**Proposed Approach**:
Use Pydantic models for request/response validation.

**Example**:
```python
from pydantic import BaseModel, Field, EmailStr

class EngineerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr  # Validates email format
    role: str
    status: str
    project_id: int

@app.post("/engineers")
def create_engineer(engineer: EngineerCreate):
    # FastAPI automatically validates input
    # Returns 422 if validation fails
    pass
```

**Status**: Waiting for CRUD endpoint implementation

---

### ADR-P02: Service Layer Implementation

**Date**: 2026-07-22

**Status**: 📋 Proposed (Not implemented yet)

**Context**:
Current implementation has business logic in route handlers. As complexity grows, need separation of concerns:

**Current** (Mixed concerns):
```python
@app.get("/projects")
def get_projects():  # Route handler doing query logic
    projects = session.query(Project).all()
    return projects
```

**Proposed** (Separated):
```python
# services/project_service.py
class ProjectService:
    def get_all_projects(self):
        return session.query(Project).all()

# api/projects.py
@app.get("/projects")
def get_projects():  # Route handler
    service = ProjectService()
    return service.get_all_projects()
```

**Benefits**:
- Testable business logic
- Reusable across endpoints
- Easier to maintain and modify
- Clear separation of concerns

**Status**: Waiting for CRUD endpoint implementation

---

### ADR-P03: Alembic Migrations for Database Schema

**Date**: 2026-07-22

**Status**: 📋 Proposed (Not implemented yet)

**Context**:
Currently using SQLAlchemy `create_all()` for schema creation. As schema evolves, need:
- Version control for schema changes
- Ability to rollback schema changes
- Production-safe migrations
- Tracking of what changed when

**Current Approach** (Fragile):
```python
Base.metadata.create_all(engine)  # All or nothing
```

**Proposed Approach** (Robust):
```bash
alembic revision --autogenerate -m "Add assignments table"
alembic upgrade head
alembic downgrade -1  # Rollback if needed
```

**Status**: Plan to implement when schema changes are needed

---

### ADR-P04: Structured Logging Infrastructure

**Date**: 2026-07-22

**Status**: 📋 Proposed (Not implemented yet)

**Context**:
No logging currently. For debugging and monitoring need:
- Request/response logging
- Error logging with context
- Performance monitoring
- Structured logs for easy parsing

**Proposed Stack**:
- **Logger**: Python `logging` module
- **Format**: JSON for structured logs
- **Destination**: stdout (for container/cloud deployment)

**Example**:
```python
import logging
logger = logging.getLogger(__name__)

@app.get("/projects")
def get_projects():
    logger.info("Fetching all projects")
    try:
        projects = session.query(Project).all()
        logger.info(f"Retrieved {len(projects)} projects")
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise
```

**Status**: Waiting for production requirements

---

## Deprecated Decisions

### ADR-DEP01: Individual Declarative Bases per Model

**Date**: 2026-07-22

**Status**: ❌ Deprecated (Caused foreign key resolution failures)

**What We Tried**:
```python
# project.py
Base = declarative_base()

# engineer.py
Base = declarative_base()  # Different base!
```

**Why It Failed**:
Foreign key relationships require all models to share the same SQLAlchemy metadata registry.

**Resolution**: 
Replaced with shared Base in `models/__init__.py` (ADR-006)

---

## Decision Summary

### Accepted Decisions (11)
- ✅ FastAPI web framework
- ✅ PostgreSQL database
- ✅ SQLAlchemy ORM
- ✅ Supabase provider
- ✅ REST API design
- ✅ Shared ORM Base
- ✅ Environment configuration
- ✅ CORS for development
- ✅ Document blobs outside the database, behind a storage interface
- ✅ Soft delete for documents (+ retention job)
- ✅ Routers + service layer for new modules

### Proposed Decisions (4)
- 📋 Pydantic validation
- 📋 Service layer
- 📋 Alembic migrations
- 📋 Structured logging

### Deprecated Decisions (1)
- ❌ Individual model bases

---

## Decision Guidelines for Future

When making new architectural decisions:

1. **Document Context**: Why is this decision needed?
2. **List Options**: What alternatives exist?
3. **Explain Choice**: Why was this option chosen?
4. **Consider Impact**: What are the consequences?
5. **Plan Reversibility**: How could we undo this if needed?
6. **Set Expiration**: When should this decision be revisited?

---

## Revision History

| Date | Author | Decision | Status |
|------|--------|----------|--------|
| 2026-06-15 | Architect | ADR-001, ADR-002, ADR-004, ADR-005 | Accepted |
| 2026-06-20 | Architect | ADR-003, ADR-007 | Accepted |
| 2026-07-22 | Team | ADR-006, ADR-008, ADR-009, ADR-P01-P04, ADR-DEP01 | Updated |
| 2026-07-26 | Team | ADR-010, ADR-011, ADR-012 (Document Management) | Accepted |

---

**Last Updated**: 2026-07-26
**Next Review**: 2026-08-22
