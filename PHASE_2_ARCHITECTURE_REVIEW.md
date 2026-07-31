# Phase 2: AI Project Assistant - Comprehensive Architecture Review

**Status:** ✅ Architecture Review Complete - Awaiting Approval  
**Date:** 2026-07-28  
**Objective:** Design modular, enterprise-grade AI assistant for project intelligence

---

## Executive Summary

Phase 1 delivered a robust semantic embedding pipeline with vector search. Phase 2 must build an intelligent assistant layer ON TOP of this foundation without becoming monolithic.

### Key Challenge
**Avoid creating a monolith.** The AI Project Assistant must be designed as the FIRST specialized agent in a future multi-agent ecosystem (Document Agent, Finance Agent, Schedule Agent, etc.).

### Design Philosophy
- **Clean separation of concerns** — Each layer has a single responsibility
- **Dependency injection** — Loose coupling, easy testing
- **Modular services** — AI logic doesn't know about HTTP (reusable by other agents)
- **Prompt management** — Centralized, versioned, configurable
- **Response formatting** — Structured outputs for executives
- **Future-ready** — Architecture supports memory, tool calling, and multi-agent orchestration

---

## 1. Current AI Architecture (Phase 1)

### What Exists Today

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript)                          │
│  - Document upload                                      │
│  - Document list & search                               │
│  - Project/Engineer management                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────┐
│  FastAPI Backend                                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Routers (HTTP Layer)                            │   │
│  │ - /documents (upload/list/delete)               │   │
│  │ - /projects (CRUD)                              │   │
│  │ - /engineers (CRUD)                             │   │
│  │ - /search/semantic (query + filter)             │   │
│  │ - /dashboard                                    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │ Services Layer                                  │   │
│  │ - document_embedding_service                   │   │
│  │ - embedding_service (OpenAI API)               │   │
│  │ - chunking_service                             │   │
│  │ - pdf_service                                  │   │
│  │ - embedding_pipeline (checkpoint-based)        │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │ Data Access                                     │   │
│  │ - SQLAlchemy ORM                               │   │
│  │ - PostgreSQL + pgvector                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Strengths Observed
- ✅ **Solid embedding pipeline** — Checkpoint-based, fault-tolerant, measurable
- ✅ **Vector search ready** — `/search/semantic` working, pgvector indexed
- ✅ **Clean service layer** — Business logic separated from HTTP
- ✅ **Storage abstraction** — Local filesystem ready for S3/Azure migration
- ✅ **Comprehensive monitoring** — Pipeline metrics, cost tracking, health checks

### Gaps for Phase 2
- ❌ **No LLM integration** — OpenAI/Claude API not wired
- ❌ **No prompt management** — No centralized prompt templates
- ❌ **No answer synthesis** — Search results retrieved, but not converted to insights
- ❌ **No response formatting** — No structured outputs for executives
- ❌ **No conversation context** — Stateless; each query is isolated
- ❌ **No tool calling** — LLM can't call backend functions
- ❌ **No multi-agent coordination** — Single-purpose design, not extensible

---

## 2. Phase 2: Where the AI Project Assistant Fits

### What Phase 2 Must Deliver

The **AI Project Assistant** is a natural language interface for project intelligence. It answers questions like:

#### Project Understanding
- "Summarize this project."
- "What's the current status?"
- "What are today's priorities?"

#### Project Risks
- "What are the major risks?"
- "Which issues require escalation?"
- "Which dependencies are impacting delivery?"

#### Schedule & Delivery
- "Which sites are delayed?"
- "Which milestones are behind schedule?"

#### Document Intelligence
- "Compare RFDS with CIQ."
- "Summarize uploaded RFDS."
- "Find all references to permit delays."

#### Executive Reporting
- "Generate customer status update."
- "Prepare weekly delivery report."

---

## 3. Proposed Architecture for Phase 2

### High-Level Design

```
┌──────────────────────────────────────────────────────────┐
│  Client Layer                                            │
│  - Chat UI (React)                                       │
│  - Query input                                           │
│  - Streaming responses                                   │
└────────────────┬─────────────────────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────▼──────────────────────────────────────────┐
│  API Layer (FastAPI)                                     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ /chat (POST)                                     │   │
│  │ - Query string & project context                 │   │
│  │ - Returns: structured response + citations       │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────────┐
│  AI Service Layer (NEW)                                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Project Assistant Agent                        │    │
│  │ - Coordinates retrieval + synthesis            │    │
│  │ - Routes queries by intent                     │    │
│  │ - Manages conversation context (future)        │    │
│  └────────────────┬────────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐   │
│  │ RAG + Prompt Layer                              │   │
│  │                                                 │   │
│  │ ┌─────────────────────────────────────────┐    │   │
│  │ │ Query Router (Intent Classification)    │    │   │
│  │ │ - Determines question type              │    │   │
│  │ │ - Selects retrieval strategy            │    │   │
│  │ └─────────────────────────────────────────┘    │   │
│  │                                                 │   │
│  │ ┌─────────────────────────────────────────┐    │   │
│  │ │ Context Retriever                       │    │   │
│  │ │ - Semantic search (documents)           │    │   │
│  │ │ - SQL queries (projects/risks/schedule) │    │   │
│  │ │ - Hybrid retrieval                      │    │   │
│  │ └─────────────────────────────────────────┘    │   │
│  │                                                 │   │
│  │ ┌─────────────────────────────────────────┐    │   │
│  │ │ Prompt Templates                        │    │   │
│  │ │ - System prompts by query type          │    │   │
│  │ │ - Few-shot examples                     │    │   │
│  │ │ - Citation formatting                  │    │   │
│  │ └─────────────────────────────────────────┘    │   │
│  │                                                 │   │
│  │ ┌─────────────────────────────────────────┐    │   │
│  │ │ Response Formatters                     │    │   │
│  │ │ - Concise mode                          │    │   │
│  │ │ - Executive summary                     │    │   │
│  │ │ - Detailed analysis                     │    │   │
│  │ └─────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────────┐
│  LLM Integration Layer (NEW)                             │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ LLM Client (Claude 3.5 Sonnet / GPT-4)         │    │
│  │ - API abstraction                              │    │
│  │ - Retry logic + rate limiting                  │    │
│  │ - Token counting & cost tracking (future)      │    │
│  │ - Streaming support                            │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────┬──────────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────────┐
│  Retrieval & Data Layer                                  │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │ Semantic Search  │  │ SQL Queries      │              │
│  │ - pgvector       │  │ - Project status │              │
│  │ - Document chunks│  │ - Risk register  │              │
│  │                  │  │ - Schedule data  │              │
│  └──────────────────┘  └──────────────────┘              │
│         │                      │                         │
│  ┌──────▼──────────────────────▼──────────┐              │
│  │  PostgreSQL + pgvector                │              │
│  │  - documents, embeddings              │              │
│  │  - projects, engineers                │              │
│  │  - risks, schedule                    │              │
│  │  - conversation history (future)      │              │
│  └───────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Folder Structure

### Proposed Directory Layout

```
backend/app/
├── main.py                           # FastAPI app, route mounting
├── config.py                         # Settings (+ new AI config)
├── database.py                       # DB connection
├── schemas.py                        # Pydantic models (existing)
│
├── models/                           # SQLAlchemy ORM
│   ├── __init__.py
│   ├── project.py
│   ├── engineer.py
│   ├── document.py
│   ├── embedding.py
│   └── conversation.py               # ⭐ NEW (Phase 2): Chat history
│
├── routers/                          # HTTP endpoints
│   ├── documents.py                  # (existing)
│   ├── search.py                     # (existing)
│   ├── admin.py                      # (existing)
│   └── chat.py                       # ⭐ NEW (Phase 2): /chat endpoint
│
├── services/                         # Business logic
│   ├── pdf_service.py                # (existing)
│   ├── chunking_service.py           # (existing)
│   ├── embedding_service.py          # (existing)
│   ├── document_embedding_service.py # (existing)
│   ├── embedding_pipeline.py         # (existing - checkpoint-based)
│   ├── pipeline_metrics.py           # (existing)
│   ├── exceptions.py                 # (existing)
│   └── document_service.py           # (existing)
│
├── ai/                               # ⭐ NEW (Phase 2): AI Services
│   ├── __init__.py
│   ├── project_assistant.py          # Main orchestrator
│   │   - route_query()
│   │   - synthesize_answer()
│   │   - format_response()
│   │
│   ├── llm_client.py                 # LLM abstraction
│   │   - generate()
│   │   - stream()
│   │   - retry_logic()
│   │
│   ├── retriever.py                  # RAG layer
│   │   - retrieve_by_intent()
│   │   - semantic_search()
│   │   - sql_query()
│   │   - hybrid_retrieval()
│   │
│   ├── query_router.py               # Intent classification
│   │   - classify_query()
│   │   - extract_parameters()
│   │   - select_strategy()
│   │
│   ├── context_retriever/
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract retriever
│   │   ├── semantic_retriever.py      # Document search
│   │   ├── project_retriever.py       # Project data
│   │   ├── risk_retriever.py          # Risk data
│   │   └── schedule_retriever.py      # Schedule data
│   │
│   └── formatters/                   # Response formatting
│       ├── __init__.py
│       ├── base.py                   # Abstract formatter
│       ├── executive_formatter.py    # Executive summary
│       ├── detailed_formatter.py     # Full analysis
│       └── concise_formatter.py      # Brief answer
│
├── prompts/                          # ⭐ NEW (Phase 2): Prompt templates
│   ├── __init__.py
│   ├── templates.py                  # Template loading
│   ├── system_prompts/
│   │   ├── project_understanding.txt
│   │   ├── risk_analysis.txt
│   │   ├── schedule_analysis.txt
│   │   ├── document_intelligence.txt
│   │   ├── executive_reporting.txt
│   │   └── knowledge_search.txt
│   │
│   └── few_shots/
│       ├── project_summary.json
│       ├── risk_assessment.json
│       ├── status_update.json
│       └── report_generation.json
│
├── storage/                          # (existing)
│   ├── base.py
│   ├── local.py
│   └── __init__.py
│
└── embedding_queue.py                # (existing)
```

### Frontend Structure (Minimal Addition)

```
frontend/src/
├── pages/
│   ├── Dashboard.tsx
│   ├── Projects.tsx
│   ├── Engineers.tsx
│   ├── Documents.tsx
│   └── Chat.tsx                      # ⭐ NEW: Chat interface
│
├── components/
│   └── chat/                         # ⭐ NEW: Chat UI
│       ├── ChatInterface.tsx
│       ├── MessageBubble.tsx
│       ├── CitationLink.tsx
│       └── ResponseFormatter.tsx
│
└── api/
    ├── documents.ts
    ├── projects.ts
    └── chat.ts                       # ⭐ NEW: Chat API client
```

---

## 5. Core Services to Implement

### AI Services (New)

#### 1. **LLM Client** (`ai/llm_client.py`)
Abstraction layer for Claude/GPT-4 API.

```python
class LLMClient:
    async def generate(
        prompt: str,
        system_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate response from LLM."""
        
    async def stream(
        prompt: str,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        """Stream response for real-time UI updates."""
        
    def count_tokens(text: str) -> int:
        """Estimate token count."""
```

**Why abstraction?**
- Swap Claude ↔ GPT-4 with config change
- Unified retry logic, rate limiting
- Token counting for cost tracking
- Easy to add Anthropic or OpenAI features

---

#### 2. **Query Router** (`ai/query_router.py`)
Classifies query intent to select retrieval strategy.

```python
class QueryRouter:
    def classify(query: str) -> QueryIntent:
        """Identify query type: status, risks, schedule, etc."""
        
    def extract_parameters(query: str, intent: QueryIntent) -> dict:
        """Extract project_id, date_range, customer, etc."""
        
    def select_strategy(intent: QueryIntent) -> RetrievalStrategy:
        """Return appropriate retriever (semantic, SQL, hybrid)."""
```

**Query Intent Types:**
```python
class QueryIntent(Enum):
    PROJECT_SUMMARY = "project_summary"
    PROJECT_STATUS = "project_status"
    PROJECT_RISKS = "project_risks"
    PROJECT_SCHEDULE = "project_schedule"
    DOCUMENT_SEARCH = "document_search"
    DOCUMENT_COMPARISON = "document_comparison"
    EXECUTIVE_SUMMARY = "executive_summary"
    WEEKLY_REPORT = "weekly_report"
    KNOWLEDGE_SEARCH = "knowledge_search"
```

---

#### 3. **Context Retriever** (`ai/retriever.py`)
Multi-strategy retrieval system.

```python
class ContextRetriever:
    async def retrieve(
        query: str,
        intent: QueryIntent,
        filters: dict
    ) -> RetrievalResult:
        """Fetch relevant context from multiple sources."""
        
class RetrievalResult:
    semantic_results: List[SemanticSearchResult]  # From documents
    project_data: List[ProjectData]               # From SQL
    risk_data: List[RiskData]                     # From SQL
    schedule_data: List[ScheduleData]             # From SQL
    source_citations: List[Citation]              # For attribution
```

**Pluggable Retrievers:**
```python
class BaseRetriever(ABC):
    async def retrieve(query: str, filters: dict) -> List[dict]:
        """Retrieve context for a query."""

class SemanticRetriever(BaseRetriever):
    """Search documents via pgvector."""
    
class ProjectRetriever(BaseRetriever):
    """Fetch project metadata from SQL."""
    
class RiskRetriever(BaseRetriever):
    """Find project risks and blockers."""
    
class ScheduleRetriever(BaseRetriever):
    """Fetch schedule/milestone data."""
```

---

#### 4. **Project Assistant Agent** (`ai/project_assistant.py`)
Main orchestrator: routes query → retrieves context → synthesizes answer.

```python
class ProjectAssistantAgent:
    async def answer(
        query: str,
        project_id: Optional[int] = None,
        response_mode: str = "concise"  # or "detailed", "executive"
    ) -> AssistantResponse:
        """Process a query and return structured answer."""
        
    async def _route_query(query: str) -> QueryIntent:
        """Classify query intent."""
        
    async def _retrieve_context(
        query: str,
        intent: QueryIntent,
    ) -> RetrievalResult:
        """Fetch relevant context."""
        
    async def _synthesize_answer(
        query: str,
        intent: QueryIntent,
        context: RetrievalResult,
    ) -> str:
        """Use LLM to synthesize answer."""
        
    async def _format_response(
        answer: str,
        mode: str,
        context: RetrievalResult
    ) -> AssistantResponse:
        """Format response with citations."""

class AssistantResponse:
    answer: str                         # Main text
    citations: List[Citation]          # Source attribution
    confidence: float                  # 0.0-1.0
    requires_escalation: bool          # Risk flag
    metadata: dict                      # Intent, retrieval strategy, etc.
```

---

#### 5. **Response Formatters** (`ai/formatters/`)
Different response styles for different users.

```python
class BaseFormatter(ABC):
    def format(answer: str, context: RetrievalResult) -> str:
        """Format response appropriately."""

class ExecutiveFormatter(BaseFormatter):
    """Structured for C-suite: summary → key points → risks."""
    
class DetailedFormatter(BaseFormatter):
    """Full analysis with supporting data."""
    
class ConciseFormatter(BaseFormatter):
    """Brief answer + links to details."""
```

**Executive Formatter Output Example:**
```json
{
  "executive_summary": "Project CloudSync on track with minor risk.",
  "key_metrics": {
    "status": "Active",
    "progress": 65,
    "schedule_variance": "-2 days",
    "budget_variance": "$50k under"
  },
  "risks": [
    {
      "severity": "high",
      "description": "Ericsson radio integration delay",
      "impact": "5-day slip",
      "mitigation": "Escalate to vendor"
    }
  ],
  "action_items": [
    "Resolve permit delay by Friday",
    "Confirm Ericsson delivery date"
  ],
  "citations": [
    { "source": "Project Charter (Q3 2026)", "relevance": "Status baseline" }
  ]
}
```

---

### Prompt Management (`prompts/`)

#### Centralized Prompt Templates

**System Prompts** — Loaded per query intent:

```yaml
# prompts/system_prompts/project_understanding.txt
You are an enterprise project intelligence assistant.
You help project managers, directors, and executives understand project status.

When answering questions about projects:
1. Always cite sources (document, data system, calculation)
2. Be specific: reference actual project names, dates, owners
3. Flag unusual patterns or risks
4. Provide actionable insights, not just summaries
5. Use professional business tone
```

**Few-Shot Examples** — Improve consistency:

```json
// prompts/few_shots/project_summary.json
{
  "examples": [
    {
      "input": "Summarize the CloudSync project",
      "output": {
        "summary": "CloudSync is a telecom infrastructure platform...",
        "status": "Active",
        "key_dates": [...],
        "risks": [...]
      }
    }
  ]
}
```

---

## 6. Proposed APIs

### New Endpoints

#### 1. **Chat Endpoint** (`POST /chat`)
Main interface for Q&A.

```python
# Request
class ChatRequest(BaseModel):
    query: str = Field(..., description="Question")
    project_id: Optional[int] = Field(None)
    response_mode: str = Field(
        "concise",
        description="concise|detailed|executive"
    )
    include_citations: bool = Field(True)

# Response
class ChatResponse(BaseModel):
    answer: str
    response_mode: str
    citations: List[Citation]
    confidence: float
    metadata: dict  # intent, retrieval_strategy, etc.

# Endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer natural language questions about projects."""
```

#### 2. **Chat Stream** (for frontend real-time UI)

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream answer tokens as they're generated."""
```

#### 3. **Intent Classification** (optional, for debugging)

```python
@router.post("/chat/classify")
async def classify(query: str) -> dict:
    """Debug endpoint: show classified intent."""
```

---

## 7. Data Flow Diagram

```
User Query
    │
    ├─ "Summarize CloudSync project"
    │
    ▼
┌──────────────────────────────────────────┐
│ Query Router (Intent Classification)      │
│ Intent: PROJECT_SUMMARY                  │
│ Parameters: { project_id: 1 }            │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ Context Retriever (Multi-Strategy)        │
│                                          │
│ 1. Semantic Search:                      │
│    Query: "CloudSync project summary"    │
│    Result: Top 5 document chunks         │
│                                          │
│ 2. Project SQL Query:                    │
│    SELECT * FROM projects WHERE id=1     │
│    Result: Project metadata              │
│                                          │
│ 3. Risk SQL Query:                       │
│    SELECT * FROM risks WHERE project=1   │
│    Result: Active risks                  │
│                                          │
│ 4. Schedule SQL Query:                   │
│    SELECT * FROM milestones              │
│    Result: Timeline data                 │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ LLM Synthesis (Claude 3.5 Sonnet)         │
│                                          │
│ System Prompt: "project_understanding"   │
│ Context: [Semantic + SQL results]        │
│ Few-shot: Examples of good summaries     │
│                                          │
│ Generate: Structured answer              │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ Response Formatter                        │
│                                          │
│ Mode: "executive"                        │
│ Format: Structured JSON                  │
│ Add: Citations, confidence, metadata     │
└──────────────┬───────────────────────────┘
               │
               ▼
        Client Response
    {
      "answer": "CloudSync is...",
      "citations": [...],
      "confidence": 0.92,
      "metadata": {...}
    }
```

---

## 8. Integration with Semantic Search

### How Embeddings Are Used

The Project Assistant **leverages Phase 1's embedding pipeline**:

1. **Document Retrieval**
   - User asks: "What are the major risks?"
   - Query is embedded via same OpenAI API
   - pgvector searches for similar chunks
   - Returns: Top 5 risk-related documents

2. **Context Assembly**
   - Search results are passed to LLM as context
   - LLM synthesizes across multiple documents
   - Citations point back to source documents

3. **Semantic Search Filter**
   - Can filter by project, customer, document type
   - Already implemented in Phase 1

4. **Hybrid Retrieval** (optional enhancement)
   - Combine semantic search + keyword search
   - Use keyword search as fallback
   - Rank results by relevance

---

## 9. Future Extensibility: Multi-Agent Architecture

### How Phase 2 Enables Phase 3+

The Project Assistant is designed as **Agent v1** in a future ecosystem:

#### Base Agent Interface (to be introduced)

```python
class Agent(ABC):
    """Base class for all specialized agents."""
    
    async def answer(query: str) -> AgentResponse:
        """Process a query in this agent's domain."""
```

#### Future Agents Will Follow Same Pattern

```python
class DocumentAgent(Agent):
    """Specialized for document intelligence."""
    # - Compare RFDS versions
    # - Extract compliance data
    # - Track document lineage
    
class FinanceAgent(Agent):
    """Specialized for budget/cost analysis."""
    # - Forecast spend
    # - Identify cost drivers
    # - ROI calculations
    
class ScheduleAgent(Agent):
    """Specialized for timeline analytics."""
    # - Critical path analysis
    # - Delay prediction
    # - Resource leveling
    
class ResourceAgent(Agent):
    """Specialized for team/resource optimization."""
    # - Allocation optimization
    # - Skills matching
    # - Workload balancing
```

#### Agent Orchestration (Phase 3)

```python
class MultiAgentOrchestrator:
    """Route queries to appropriate agent(s)."""
    
    async def answer(query: str) -> Response:
        # Query router determines which agent(s) to use
        if "budget" in query:
            return await finance_agent.answer(query)
        elif "resources" in query:
            return await resource_agent.answer(query)
        elif involves_documents(query):
            # Use multiple agents, merge responses
            return await merge_responses([
                await document_agent.answer(query),
                await project_agent.answer(query)
            ])
```

#### Phase 2 Design Supports This Via:

1. **Modular Service Layer** — Each agent can reuse retrievers, formatters, LLM client
2. **Shared Prompt Management** — Centralized prompts for all agents
3. **Common Data Access** — All agents query same database
4. **Dependency Injection** — Easy to compose agents
5. **Stateless Orchestration** — Agents don't depend on each other's state

---

## 10. How Conversation Memory Will Be Added (Phase 3)

Currently: **Stateless** — Each query is independent.

Future: **With Conversation Context** — Build on Phase 2 foundation.

### Database Schema (Future)

```python
class Conversation(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # Future: user auth
    project_id = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class ConversationMessage(Base):
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    tokens = Column(Integer)
    created_at = Column(DateTime)
```

### LLM Context Window Management (Future)

```python
class ConversationManager:
    async def get_context(conversation_id: int) -> str:
        """Load conversation history, fit to token window."""
        # Fetch recent messages
        # Summarize older messages if needed
        # Return: formatted context string
```

### Streaming Support (Future)

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    # Load conversation history
    # Stream answer tokens in real-time
    # Persist to database
```

---

## 11. Tool Calling for Future Agents (Phase 3+)

Phase 2 doesn't need tool calling, but architecture supports it:

### Tool Definition (Future)

```python
class Tool(BaseModel):
    name: str
    description: str
    parameters: dict

class ProjectTools:
    TOOLS = [
        Tool(
            name="get_project_status",
            description="Get current status of a project",
            parameters={"project_id": "integer"}
        ),
        Tool(
            name="update_risk",
            description="Escalate or acknowledge a project risk",
            parameters={"risk_id": "integer", "action": "string"}
        ),
    ]
```

### LLM Tool Calling (Future)

```python
class ProjectAssistantWithTools(ProjectAssistant):
    async def answer_with_tools(query: str) -> Response:
        # Ask LLM to decide which tools to use
        tool_calls = await llm.generate_with_tools(
            query,
            tools=ProjectTools.TOOLS
        )
        
        # Execute tool calls
        results = await self._execute_tools(tool_calls)
        
        # Let LLM synthesize final answer with results
        return await llm.synthesize(query, results)
```

---

## 12. Architecture Recommendations

### Before Implementation

I recommend these improvements to the existing platform:

#### ✅ Recommendation 1: Separate AI Config from Document Config
**Impact:** Keep embedding settings separate from LLM settings.

```python
# backend/app/config.py
@dataclass(frozen=True)
class EmbeddingSettings:
    """Document embedding configuration."""
    embedding_model: str
    embedding_batch_size: int
    # ... existing fields

@dataclass(frozen=True)
class LLMSettings:
    """LLM integration configuration."""
    llm_provider: str  # "claude" or "openai"
    llm_model: str     # "claude-3-5-sonnet" or "gpt-4"
    llm_api_key: str
    llm_max_tokens: int
    llm_temperature: float

@dataclass(frozen=True)
class Settings:
    embedding: EmbeddingSettings
    llm: LLMSettings
    # ... other settings
```

---

#### ✅ Recommendation 2: Extract Shared Utilities
**Impact:** Reusable across all services.

Create `app/utils/`:
```
app/utils/
├── llm_utils.py         # Token counting, prompt formatting
├── retrieval_utils.py   # Query parsing, result ranking
├── formatting_utils.py  # JSON, markdown, citation handling
└── logging_utils.py     # Structured logging (already done)
```

---

#### ✅ Recommendation 3: Structured Logging for AI Services
**Impact:** Observability, debugging, cost tracking.

```python
# In project_assistant.py
logger.info(
    "query_processed",
    extra={
        "query": query,
        "intent": intent.value,
        "retrieval_time_ms": retrieval_ms,
        "llm_time_ms": llm_ms,
        "response_length": len(answer),
        "tokens_used": token_count,
        "cost_usd": cost,
        "model": settings.llm.llm_model,
    }
)
```

---

#### ✅ Recommendation 4: Versioned Prompt Management
**Impact:** Track prompt performance, easy rollbacks.

```python
# prompts/templates.py
class PromptVersion(Base):
    id = Column(Integer, primary_key=True)
    prompt_type = Column(String)  # "project_summary", etc.
    version = Column(Integer)
    content = Column(Text)
    performance_score = Column(Float)
    created_at = Column(DateTime)
    active = Column(Boolean)
```

This allows:
- A/B testing different prompts
- Performance tracking per prompt version
- Easy rollback if new version underperforms

---

### Risks & Trade-offs

#### Risk 1: LLM Hallucination
**Problem:** LLM might invent facts not in documents.

**Mitigations:**
- Always require citations (don't let LLM answer without sources)
- Use grounding: "Only answer based on provided context"
- Flag low-confidence answers
- Manual review for high-stakes decisions

#### Risk 2: Token Cost Explosion
**Problem:** Large context windows (documents) → high OpenAI/Claude costs.

**Mitigations:**
- Implement smart context truncation (keep most relevant snippets)
- Cache frequently asked queries
- Set per-query token limits
- Monitor cost via logging (implemented in Recommendation 3)
- Use smaller model (GPT-3.5) for low-stakes queries

#### Risk 3: Latency for Complex Queries
**Problem:** Multi-step retrieval + LLM → slow response.

**Mitigations:**
- Implement response streaming (show answer as it's generated)
- Cache embedding computations
- Use async everywhere
- Optimize pgvector queries (indexes already exist)
- Parallel retrieval (semantic + SQL queries simultaneously)

#### Risk 4: Tightly Coupled Agent Design
**Problem:** Hard to split into multiple agents later.

**Mitigations:** (Already built into design!)
- Retrievers are pluggable (easy to add new data sources)
- Formatters are separate (easy to add new output formats)
- LLM client is abstracted (easy to swap models)
- Agent logic doesn't know about HTTP (reusable for tool calling)

---

## 13. Implementation Roadmap

### Phase 2a: Foundation (Week 1)
- [ ] Create `app/ai/` directory structure
- [ ] Implement `LLMClient` (Claude 3.5 Sonnet)
- [ ] Implement `QueryRouter` (intent classification)
- [ ] Add AI config to `app/config.py`
- [ ] Create `/chat` endpoint skeleton

### Phase 2b: Retrieval (Week 2)
- [ ] Implement `ContextRetriever` base class
- [ ] Implement pluggable retrievers (semantic, project, risk, schedule)
- [ ] Integrate with existing search endpoints
- [ ] Add test data/fixtures

### Phase 2c: Synthesis (Week 2-3)
- [ ] Implement `ProjectAssistantAgent`
- [ ] Create prompt templates
- [ ] Implement response formatters
- [ ] Add citations & source tracking
- [ ] Implement `/chat` endpoint fully

### Phase 2d: UI & Testing (Week 3-4)
- [ ] React chat interface
- [ ] Stream response handling
- [ ] Citation UI rendering
- [ ] End-to-end testing
- [ ] Performance optimization

### Phase 2e: Monitoring (Week 4)
- [ ] Structured logging
- [ ] Cost tracking
- [ ] Performance dashboards (optional)
- [ ] Deployment to staging

---

## 14. Success Criteria for Phase 2

### Functional
- ✅ Answer 80%+ of common project questions correctly
- ✅ All answers include source citations
- ✅ Support 3+ response modes (concise/detailed/executive)
- ✅ Handle multi-project context
- ✅ Stream responses for UX responsiveness

### Non-Functional
- ✅ Query response time < 5 seconds (p95)
- ✅ Zero hallucination on factual questions (grounded only)
- ✅ Cost < $0.10 per query (token budgeting)
- ✅ Modular architecture (ready for Phase 3 agents)
- ✅ Comprehensive logging (observability)

### Architectural
- ✅ No monolith (services separated)
- ✅ Dependency injection throughout
- ✅ Abstract LLM client (swap providers)
- ✅ Pluggable retrievers (add new data sources)
- ✅ Conversation-ready (models for history)

---

## Summary

### Current State (Phase 1)
✅ Robust embedding pipeline  
✅ Vector search working  
✅ Clean service layer  
✅ Production-ready foundation  

### Proposed State (Phase 2)
✅ LLM integration (Claude/GPT-4)  
✅ Natural language Q&A  
✅ Multi-strategy retrieval  
✅ Structured responses with citations  
✅ Modular, agent-ready architecture  

### Future State (Phase 3+)
✅ Conversation memory  
✅ Multi-agent orchestration  
✅ Tool calling for automation  
✅ Advanced analytics agents  
✅ Enterprise audit trails  

---

**This architecture is ready for implementation.** 

The design:
- ✅ Is **clean** — Clear separation of concerns
- ✅ Is **modular** — Each layer replaceable
- ✅ Is **extensible** — Ready for Phase 3+ agents
- ✅ Is **maintainable** — Well-organized, documented
- ✅ Is **testable** — All services independently testable
- ✅ Is **production-ready** — Addresses security, cost, latency

**Awaiting approval to proceed with implementation.**
