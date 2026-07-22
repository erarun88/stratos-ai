# System Architecture

## System Overview

StratOS AI follows a modern three-tier architecture combining REST API with AI capabilities. The system is designed for scalability, maintainability, and future expansion with AI agents and workflow automation.

### Current Architecture Diagram

```mermaid
graph TB
    Client["Client / Frontend<br/>(React + TypeScript)"]
    
    subgraph API["FastAPI Backend"]
        Router["API Router<br/>(main.py)"]
        Middleware["CORS Middleware"]
        Models["Data Models<br/>(ORM)"]
    end
    
    subgraph DB["Data Layer"]
        PG["PostgreSQL<br/>(Supabase)"]
        PGVec["pgvector<br/>(Vector Search)"]
    end
    
    subgraph AI["AI Services<br/>(Future)"]
        OpenAI["OpenAI API"]
        Agents["AI Agents"]
        RAG["RAG Engine"]
    end
    
    Client -->|HTTP/REST| Middleware
    Middleware --> Router
    Router --> Models
    Models -->|SQLAlchemy ORM| PG
    PG -.->|Vector Search| PGVec
    Router -.->|Future Integration| AI
    AI -->|API Calls| OpenAI
    
    style API fill:#4A90E2
    style DB fill:#50C878
    style AI fill:#FFB347
    style Client fill:#9B59B6
```

---

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Runtime** | Python | 3.12+ | Backend language |
| **Web Framework** | FastAPI | 0.100+ | REST API framework |
| **Server** | Uvicorn | 0.23+ | ASGI server |
| **Database** | PostgreSQL | 15+ | Primary relational database |
| **Vector DB** | pgvector | 0.5+ | Vector search capabilities |
| **ORM** | SQLAlchemy | 2.0+ | Object-relational mapping |
| **AI** | OpenAI API | Latest | Language models and embeddings |

### Development Stack

| Tool | Purpose |
|------|---------|
| **pip** | Python package management |
| **python-dotenv** | Environment variable management |
| **psycopg2** | PostgreSQL database adapter |
| **uvicorn** | ASGI server for FastAPI |

### Frontend Stack (Planned)
- **React**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Redux/Zustand**: State management
- **TailwindCSS**: Styling
- **Vite**: Build tool

### Infrastructure
- **Supabase**: PostgreSQL hosting + pgvector + Auth (planned)
- **GitHub**: Version control and CI/CD
- **Docker**: Containerization (planned)
- **AWS/GCP**: Cloud deployment (planned)

---

## Design Patterns

### Current Patterns

#### 1. **MVC (Model-View-Controller)**
- **Models**: SQLAlchemy ORM models (Project, Engineer)
- **Views**: FastAPI route handlers (endpoints)
- **Controller**: Business logic in route handlers

#### 2. **Dependency Injection**
- Database session injection in route handlers
- SQLAlchemy `Session` as dependency

#### 3. **Repository Pattern** (Future)
- Planned abstraction layer for data access
- Enables easier testing and database switching

#### 4. **Service Layer** (Planned)
- Separate business logic from route handlers
- Reusable business logic components

### Architectural Patterns

#### 1. **Layered Architecture**
```
┌─────────────────┐
│   Presentation  │ (API Routes)
├─────────────────┤
│   Business      │ (Services, Agents)
├─────────────────┤
│   Data Access   │ (ORM, Repositories)
├─────────────────┤
│   Data Storage  │ (PostgreSQL, pgvector)
└─────────────────┘
```

#### 2. **CORS Middleware Pattern**
- All origins allowed (development configuration)
- Future: Restrict to known domains in production

---

## API Architecture

### REST API Design

#### API Style
- RESTful API following HTTP conventions
- JSON request/response format
- Stateless request handling

#### Current Endpoints

```
GET  /                 → Home message
GET  /projects         → Retrieve all projects
GET  /engineers        → Retrieve all engineers
GET  /db-test          → Database connectivity test
```

#### Future Endpoints

```
POST   /projects            → Create new project
GET    /projects/{id}       → Get project details
PUT    /projects/{id}       → Update project
DELETE /projects/{id}       → Delete project

POST   /engineers           → Create new engineer
GET    /engineers/{id}      → Get engineer details
PUT    /engineers/{id}      → Update engineer
DELETE /engineers/{id}      → Delete engineer

POST   /assignments         → Assign engineer to project
DELETE /assignments/{id}    → Remove assignment

GET    /analytics/portfolio → Portfolio analytics
GET    /analytics/risks     → Risk assessment
POST   /recommendations     → AI-powered recommendations
```

#### Response Format
```json
// Single Resource
{
  "id": 1,
  "name": "CloudSync Platform",
  "customer": "TechCorp Inc.",
  "status": "active",
  "budget": 500000.0
}

// Multiple Resources
[
  {
    "id": 1,
    ...
  },
  {
    "id": 2,
    ...
  }
]
```

---

## Authentication & Authorization

### Current State
- **No authentication** implemented (open API)
- **No authorization** checks

### Future Implementation (Planned)

#### Authentication Methods
1. **API Keys**: For service-to-service communication
2. **JWT Tokens**: For user authentication
3. **OAuth 2.0**: For third-party integrations
4. **SSO**: Single Sign-On via Supabase (planned)

#### Authorization Model
```
Roles:
├── Admin: Full system access
├── Portfolio Manager: Portfolio-level access
├── Project Manager: Project-level access
└── Team Member: Own projects and assignments only

Resources:
├── Projects (view/create/edit/delete)
├── Engineers (view/manage assignments)
├── Reports (view analytics)
└── Settings (admin only)
```

---

## Data Flow

### Current Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant SQLAlchemy
    participant PostgreSQL
    
    Client->>FastAPI: GET /projects
    FastAPI->>SQLAlchemy: select(Project)
    SQLAlchemy->>PostgreSQL: SQL Query
    PostgreSQL-->>SQLAlchemy: Result Set
    SQLAlchemy-->>FastAPI: ORM Objects
    FastAPI-->>Client: JSON Response
```

### Future AI Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Service as Service Layer
    participant Agent as AI Agent
    participant RAG as RAG Engine
    participant OpenAI
    participant DB as PostgreSQL
    
    Client->>API: POST /recommendations?project_id=1
    API->>Service: get_project_recommendations()
    Service->>Agent: analyze_project(project_id)
    Agent->>RAG: retrieve_similar_projects()
    RAG->>DB: vector_search()
    DB-->>RAG: Context (relevant projects)
    RAG-->>Agent: Context + Query
    Agent->>OpenAI: Generate insights
    OpenAI-->>Agent: Recommendations
    Agent-->>Service: Structured response
    Service-->>API: Formatted recommendations
    API-->>Client: JSON response
```

---

## Deployment Architecture

### Current Deployment

```
┌─────────────────────────────┐
│   Development Environment   │
│  (localhost:8000 / Codespace)
│                             │
│  ┌───────────────────────┐  │
│  │   FastAPI (Uvicorn)   │  │
│  │    running on :8000   │  │
│  └───────────────────────┘  │
└──────────────┬──────────────┘
               │
               │ HTTP over SSL
               │
        ┌──────▼────────┐
        │   Supabase    │
        │  PostgreSQL   │
        │   (Cloud)     │
        └───────────────┘
```

### Future Deployment (Planned)

```
┌──────────────────────────────────────────┐
│         Production Environment           │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │        Load Balancer / CDN         │  │
│  └─────────────┬──────────────────────┘  │
│                │                         │
│  ┌─────────────▼──────────────────────┐  │
│  │   FastAPI Instances (Replicas)     │  │
│  │   ├── Instance 1 (Container)       │  │
│  │   ├── Instance 2 (Container)       │  │
│  │   └── Instance N (Container)       │  │
│  └─────────────┬──────────────────────┘  │
│                │                         │
│  ┌─────────────▼──────────────────────┐  │
│  │    PostgreSQL (Managed Cloud)      │  │
│  │    ├── Primary Instance            │  │
│  │    └── Read Replicas               │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │    CI/CD Pipeline (GitHub Actions) │  │
│  │    ├── Test                        │  │
│  │    ├── Build                       │  │
│  │    └── Deploy                      │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## Scalability Strategy

### Horizontal Scaling
1. **API Layer**: Multiple FastAPI instances behind load balancer
2. **Database**: PostgreSQL read replicas for read-heavy queries
3. **Caching**: Redis for session and query result caching (planned)
4. **Message Queue**: Background job processing (planned)

### Vertical Scaling
1. **Database**: Increase instance size for PostgreSQL
2. **API Server**: Increase compute resources
3. **Monitoring**: Performance metrics to identify bottlenecks

### Optimization Techniques
1. **Connection Pooling**: SQLAlchemy connection pooling
2. **Query Optimization**: Indexed queries, efficient joins
3. **Caching Strategy**: API response caching (planned)
4. **Async Processing**: Async routes for long-running operations (planned)

---

## Performance Considerations

### Current Optimizations
- SQLAlchemy ORM for efficient database queries
- CORS middleware for cross-origin requests
- Connection reuse with SQLAlchemy sessions

### Planned Optimizations
1. **Database Indexes**: Strategic indexing on frequently queried columns
2. **Query Optimization**: Batch queries, lazy loading strategies
3. **Caching Layers**: Redis for hot data
4. **Pagination**: Limit result sets for large datasets
5. **Async API**: Async/await for I/O operations
6. **Compression**: gzip compression for API responses

### Performance Targets
- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 100ms
- **Throughput**: 1000+ requests/second
- **Uptime**: 99.5%+

---

## Security Architecture

### Current Security Implementation
- CORS middleware (all origins allowed - development only)
- Environment-based secrets management (.env)
- No authentication/authorization

### Planned Security Measures

#### 1. **Authentication**
- JWT token-based authentication
- Refresh token rotation
- Session management

#### 2. **Authorization**
- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging for sensitive operations

#### 3. **API Security**
- Rate limiting per IP/user
- Request validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- CORS restriction to known domains

#### 4. **Data Security**
- Encryption at rest (database)
- Encryption in transit (TLS/SSL)
- Sensitive data masking in logs
- Data backup and recovery procedures

#### 5. **Infrastructure Security**
- Private subnets for database
- VPC for isolated network
- Security groups and firewall rules
- Secrets management (Vault/Secrets Manager)

#### 6. **Dependency Security**
- Dependency scanning (Dependabot)
- Regular security updates
- Vulnerability assessment

---

## Integration Points

### External Services
- **OpenAI API**: For AI-powered features
- **Supabase**: PostgreSQL database and authentication
- **GitHub**: Version control and CI/CD

### Third-Party Integrations (Planned)
- **Jira**: Project tracking sync
- **Azure DevOps**: Portfolio management
- **Salesforce**: CRM integration
- **Slack**: Notifications and commands
- **Microsoft Teams**: Notifications and integration

### Internal Integrations (Planned)
- **Webhook System**: External system triggers
- **Event Queue**: Async event processing
- **Notification Service**: Email, SMS, push notifications

---

## Module Dependencies

### Current Module Structure

```
backend/app/
├── main.py              # FastAPI application and routes
├── database.py          # Database connection setup
├── seed.py              # Sample data seeding
└── models/
    ├── __init__.py      # Shared ORM Base
    ├── project.py       # Project ORM model
    └── engineer.py      # Engineer ORM model

Planned Modules:
├── api/                 # API route handlers
│   ├── projects.py
│   ├── engineers.py
│   └── analytics.py
├── services/            # Business logic
│   ├── project_service.py
│   ├── engineer_service.py
│   └── analytics_service.py
├── agents/              # AI Agents
│   ├── project_agent.py
│   ├── risk_agent.py
│   └── recommendation_agent.py
├── rag/                 # RAG Engine
│   ├── retriever.py
│   └── indexer.py
├── schemas/             # Pydantic request/response models
│   ├── project_schema.py
│   └── engineer_schema.py
├── core/                # Core utilities
│   ├── config.py
│   └── constants.py
├── utils/               # Utility functions
│   ├── logger.py
│   └── validators.py
├── prompts/             # AI Prompts
│   ├── system_prompts.py
│   └── user_prompts.py
└── tools/               # AI Tools
    ├── project_tools.py
    └── analytics_tools.py
```

### Dependency Graph

```mermaid
graph TD
    Main["main.py<br/>(FastAPI)"]
    DB["database.py<br/>(DB Connection)"]
    Models["models/<br/>(ORM)"]
    Services["services/<br/>(Business Logic)"]
    Agents["agents/<br/>(AI)"]
    RAG["rag/<br/>(Search)"]
    Schemas["schemas/<br/>(Pydantic)"]
    Utils["utils/<br/>(Helpers)"]
    
    Main --> DB
    Main --> Models
    Main --> Services
    Main --> Schemas
    Services --> Models
    Services --> DB
    Services --> Utils
    Agents --> Services
    Agents --> RAG
    RAG --> Models
    RAG --> DB
    
    style Main fill:#4A90E2
    style Services fill:#50C878
    style Agents fill:#FFB347
    style Models fill:#E74C3C
```

---

## Design Decisions

### ADR-001: FastAPI as Web Framework
**Status**: ✅ Implemented

**Rationale**: FastAPI provides high performance, built-in OpenAPI documentation, and excellent async support. Perfect for a modern Python backend.

### ADR-002: SQLAlchemy ORM
**Status**: ✅ Implemented

**Rationale**: Provides database abstraction, type safety, and enables easy model management. Better than raw SQL for maintainability.

### ADR-003: PostgreSQL with pgvector
**Status**: ✅ Implemented

**Rationale**: PostgreSQL offers reliability and pgvector enables vector search for AI features without additional infrastructure.

### ADR-004: Supabase as Database Provider
**Status**: ✅ Implemented

**Rationale**: Managed PostgreSQL service with built-in pgvector, reducing DevOps overhead and enabling rapid development.

### ADR-005: REST API over GraphQL
**Status**: ✅ Implemented

**Rationale**: REST is simpler to implement initially, well-understood by the team, and sufficient for current feature set. GraphQL can be added later.

---

## Future Architectural Improvements

### Short-term (3-6 months)
- [ ] Async request handling for long-running operations
- [ ] API versioning strategy
- [ ] Request/response validation schemas (Pydantic)
- [ ] Service layer separation
- [ ] Comprehensive error handling

### Medium-term (6-12 months)
- [ ] Multi-tenant support
- [ ] Event-driven architecture for real-time features
- [ ] Message queue (Redis/RabbitMQ) for background jobs
- [ ] GraphQL API as additional query interface
- [ ] Webhook system for external integrations

### Long-term (12+ months)
- [ ] Microservices architecture
- [ ] Serverless components for specific tasks
- [ ] Advanced AI agent orchestration
- [ ] Federated learning for privacy-preserving AI
- [ ] Edge computing for local processing capabilities
