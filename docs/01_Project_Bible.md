# Project Bible - StratOS AI

## Project Overview

**StratOS AI** is an enterprise-grade AI Operating System for Program & Portfolio Management. It combines AI agents, retrieval-augmented generation (RAG), and workflow automation to help organizations efficiently manage projects, portfolios, risks, resources, and financial planning.

### Current Status
- 🚧 **Phase**: Early Development (Version 1.0.0)
- 📅 **Start Date**: July 2026
- 🎯 **Current Focus**: React frontend foundation on top of the backend MVP (data models + API)

---

## Vision & Mission

### Vision
To empower enterprise organizations with intelligent AI-driven tools that transform complex project and portfolio management into streamlined, data-driven decision-making processes.

### Mission
Build a scalable, secure, and intelligent platform that integrates AI capabilities with traditional project management, enabling teams to:
- Automate routine decision-making tasks
- Gain predictive insights into project risks and timelines
- Optimize resource allocation across portfolios
- Enable data-driven executive decision-making

---

## Problem Statement

Enterprise organizations struggle with:
- **Information Overload**: Managing thousands of data points across multiple projects
- **Manual Processes**: Time-consuming, error-prone project tracking and reporting
- **Poor Visibility**: Lack of real-time insights into portfolio health and risks
- **Inefficient Decision-Making**: Delayed decisions due to data gathering and analysis bottlenecks
- **Resource Optimization**: Difficulty in optimal resource allocation across projects

---

## Solution Overview

StratOS AI addresses these challenges through:

### Core Components
1. **Intelligent Project Management**: AI-powered project tracking and optimization
2. **Portfolio Analytics**: Unified view across all organizational projects
3. **Risk Intelligence**: Predictive risk identification and mitigation
4. **Resource Optimization**: Intelligent resource allocation and scheduling
5. **Executive Dashboards**: Real-time KPIs and business intelligence

### Technology Foundation
- **Backend**: FastAPI (Python) - High-performance, modern REST API framework
- **Database**: PostgreSQL with pgvector - Hybrid relational + vector search capabilities
- **AI**: OpenAI API - Advanced language models for intelligent analysis
- **Infrastructure**: Cloud-based (Supabase) - Scalable, secure, reliable

---

## Key Objectives

### Phase 1: MVP (Current - Q3 2026)
- ✅ Core data models (Projects, Engineers, Resources)
- ✅ Basic REST API endpoints
- ✅ Database schema and migrations
- ✅ Seed data for testing

### Phase 2: Core Features (Q4 2026)
- AI-powered project analytics
- Risk assessment and prediction
- Resource allocation optimization
- Basic reporting and dashboards

### Phase 3: Advanced Features (Q1 2027)
- RAG-based intelligent search and recommendations
- Workflow automation and triggering
- Integration with external systems (Jira, Azure DevOps)
- Advanced AI agents for decision support

### Phase 4: Enterprise Features (Q2 2027+)
- Multi-tenant support
- Advanced role-based access control
- Custom AI agent creation
- Third-party integrations and APIs

---

## Feature Inventory

### Frontend
- ✅ React + TypeScript foundation (Vite, React Router, Tailwind CSS) in [`frontend/`](../frontend/)
- ✅ Navigation sidebar with responsive (mobile hamburger) layout
- ✅ Executive Dashboard page — live KPI cards, project-status bar chart, and Recent Projects/Engineers tables, all from real data
- ✅ Engineers page — live table populated from `GET /engineers` with status badges
- ✅ "Add Engineer", "Edit", and "Change Status" buttons on Engineers (UI only, not yet wired to the API)
- ✅ Projects page — full CRUD: table, Add/Edit modals, Change Status, loading/empty/error states, all wired to the backend
- ✅ Documents page — repository table with debounced search, type/project filters, pagination, upload/download/edit/delete, all wired to the backend

### Executive Dashboard
- ✅ `GET /dashboard/summary` — Portfolio + team headline counts (9 metrics)
- ✅ `GET /dashboard/project-status` — Project counts by status (drives the chart)
- ✅ `GET /dashboard/recent-projects` — 5 most recently created projects
- ✅ `GET /dashboard/recent-engineers` — 5 most recently added engineers
- All values are aggregated live from the database via SQLAlchemy — no hardcoded data

### Project Management
- ✅ `GET /projects` — List all projects
- ✅ `GET /projects/{id}` — Get a single project (404 if not found)
- ✅ `POST /projects` — Create a project (validates required fields, status enum, date order)
- ✅ `PUT /projects/{id}` — Full update of a project (same validations)
- ✅ `PATCH /projects/{id}/status` — Change status (`planning` / `active` / `on_hold` / `completed` / `cancelled`)
- ❌ Hard delete — Intentionally not implemented; projects are retired via status change to preserve portfolio history.
- Fields: `id`, `name`, `customer`, `project_manager`, `status`, `start_date`, `end_date`, `description`, `created_at`, `updated_at` (plus legacy optional `budget`)

### Engineer Management
- ✅ `GET /engineers` — List all engineers
- ✅ `GET /engineers/{id}` — Get a single engineer (404 if not found)
- ✅ `POST /engineers` — Create an engineer (validates project exists, email is unique, name is non-blank)
- ✅ `PUT /engineers/{id}` — Full update of an engineer (same validations)
- ✅ `PATCH /engineers/{id}/status` — Change status (`active` / `inactive` / `on_leave`)
- ✅ `GET /projects/{project_id}/engineers` — List engineers assigned to a project
- ❌ Hard delete — Intentionally not implemented; engineer records are never physically removed so staffing history is preserved. Use the status endpoint instead.

### Document Management
- ✅ `POST /documents` — Upload a PDF with metadata (multipart); validates extension, MIME type, PDF magic number and size limit
- ✅ `GET /documents` — Paginated search/filter (free-text, document type, project, customer) with sorting
- ✅ `GET /documents/{id}` — Get a single document's metadata (404 if not found)
- ✅ `GET /documents/{id}/download` — Stream the stored file back (`Content-Disposition: attachment`)
- ✅ `PATCH /documents/{id}` — Partial metadata update (title, description, type, project, customer)
- ✅ `DELETE /documents/{id}` — Soft delete; the record is hidden from the API and retained for audit
- ✅ `GET /projects/{project_id}/documents` — Documents filed against a project
- ✅ Storage abstraction (`app/storage/`) — local filesystem today; S3/Azure Blob can be added without touching the API, service or schema
- ✅ Retention job (`python -m app.purge_documents`) — reclaims blobs for documents soft-deleted beyond the retention window
- Fields: `id`, `title`, `description`, `document_type`, `project_id`, `customer`, `uploaded_by`, `filename`, `content_type`, `file_size`, `content_hash`, `storage_backend`, `storage_key`, `created_at`, `updated_at`, `deleted_at`
- ❌ AI processing (embeddings, chunking, semantic search, OCR) — out of scope this sprint; the module is the foundation those features will build on

---

## Target Users

### Primary Users
- **Portfolio Managers**: Oversee multiple projects, need portfolio-level insights
- **Project Managers**: Execute individual projects, need status visibility
- **Resource Managers**: Optimize team allocation across projects
- **Executives**: Make strategic decisions based on real-time portfolio data
- **Team Leads**: Track team performance and capacity

### Secondary Users
- Business Analysts: Analyze project data for optimization
- Finance Teams: Monitor budgets and financial health
- Risk Officers: Identify and mitigate project risks

---

## Success Metrics

### Technical Metrics
- API response time: < 200ms for 95th percentile
- Database query performance: < 100ms for standard queries
- System uptime: 99.5%+
- Code coverage: 80%+

### Business Metrics
- User adoption rate: 70%+ of target users within 6 months
- Time-to-insight reduction: 50% faster decision-making
- Project delivery improvement: 15% improvement in on-time delivery
- ROI: 3x return within 12 months

### User Satisfaction
- Net Promoter Score (NPS): > 50
- User satisfaction: > 4.0/5.0
- Adoption rate: 70%+ of features used

---

## Constraints & Limitations

### Current Limitations
- Engineers page is still read-only: its create/edit/status-change buttons are UI placeholders, not yet wired to the API (Projects page is fully wired)
- Dashboard is read-only and not auto-refreshing (reloads on page visit)
- No authentication/authorization system
- No workflow automation engine
- Limited to PostgreSQL database (no NoSQL support currently)
- CORS allows all origins (not production-ready)

### Technical Constraints
- Python/FastAPI backend (no multi-language support initially)
- Synchronous API (async capabilities planned)
- Single-tenant architecture (multi-tenant planned)
- No API versioning strategy yet

### Business Constraints
- OpenAI API dependency (cost implications at scale)
- Supabase cloud dependency (compliance considerations for regulated industries)
- Limited audit logging capabilities
- No SSO/federated identity management

---

## Dependencies

### External Services
- **Supabase**: PostgreSQL database hosting and pgvector extension
- **OpenAI API**: GPT models for AI capabilities
- **GitHub**: Version control and CI/CD

### Technology Stack
- Python 3.12+
- FastAPI 0.100+
- SQLAlchemy 2.0+
- PostgreSQL 15+
- React + TypeScript (frontend, planned)

### Development Tools
- pip: Python package management
- uvicorn: ASGI server
- python-dotenv: Environment configuration
- psycopg2: PostgreSQL adapter

---

## Timeline & Milestones

| Milestone | Target Date | Status | Description |
|-----------|------------|--------|-------------|
| MVP Database & API | 2026-07-31 | ✅ Complete | Core models, API endpoints, seed data |
| Frontend Foundation | 2026-07-24 | ✅ Complete | React app: sidebar nav, Engineers table wired to `GET /engineers`, placeholder pages |
| Project Management Module | 2026-07-24 | ✅ Complete | Full Project CRUD API + frontend page (table, Add/Edit modals, Change Status) |
| Executive Dashboard Module | 2026-07-24 | ✅ Complete | Dashboard aggregation APIs + frontend (KPIs, status chart, recent tables) |
| Engineers CRUD wiring | 2026-09-15 | 🔄 Planned | Wire Engineers Add/Edit/Change-Status to the API |
| AI Integration | 2026-11-30 | 📋 Planned | OpenAI integration for analytics |
| RAG Implementation | 2027-01-31 | 📋 Planned | Retrieval-augmented generation for search |
| Enterprise Launch | 2027-03-31 | 📋 Planned | Full production-ready release |

---

## Team Structure

### Current Team
- **AI Architect**: System design and AI integration strategy
- **Backend Lead**: FastAPI development and database design
- **Frontend Developer**: React application development (to be hired)
- **DevOps Engineer**: Infrastructure and deployment (to be hired)

### Stakeholders
- **Product Manager**: Feature prioritization and user feedback
- **CTO**: Technical governance and architecture oversight
- **Customer Success**: User onboarding and support

---

## Communication Plan

### Daily Communication
- Async updates via email/Slack
- GitHub discussions for technical decisions
- Commit messages following conventional commits

### Weekly Communication
- Technical sync-ups on architecture decisions
- Feature review and planning

### Monthly Communication
- Stakeholder demos
- Release planning
- Progress reviews

---

## Risk Assessment

### Technical Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| OpenAI API rate limiting | High | Medium | Implement caching, queue system, fallback strategies |
| Database performance degradation | High | Medium | Query optimization, indexing strategy, monitoring |
| Security vulnerabilities | Critical | Low | Regular security audits, dependency scanning |
| Third-party API outages | Medium | Low | Graceful degradation, offline capabilities |

### Business Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| User adoption delays | High | Medium | Extensive user training, clear ROI demonstration |
| Competitive market entry | Medium | High | Rapid feature development, unique capabilities |
| Regulatory compliance issues | High | Low | Legal review, compliance framework |
| OpenAI API cost escalation | Medium | Medium | Cost monitoring, alternative model evaluation |

### Resource Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Key person dependency | High | Medium | Knowledge sharing, documentation, team expansion |
| Scope creep | Medium | High | Strict sprint planning, requirements management |
| Integration complexity | Medium | Medium | Early testing, proof of concepts, technical spikes |

---

## Compliance & Legal Requirements

### Data Privacy
- GDPR compliance for EU users
- CCPA compliance for California users
- Data retention policies (planned)
- Privacy policy and terms of service (to be created)

### Security
- SOC 2 Type II certification (planned)
- Regular security audits
- Dependency vulnerability scanning
- Secure API key management

### Accessibility
- WCAG 2.1 Level AA compliance (frontend, planned)
- Internationalization support (planned)

### Industry Standards
- Project Management Institute (PMI) standards
- ISO/IEC 27001 information security (planned)

---

## Future Enhancements

- Multi-tenant support with tenant isolation
- Advanced role-based access control (RBAC)
- SSO/federated identity management
- Workflow automation engine
- Real-time collaboration features
- Mobile application
- Advanced reporting and analytics
- Integration marketplace for third-party tools
- Custom AI agent creation interface
- Webhook support for external system integration
